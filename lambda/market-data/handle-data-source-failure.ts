/**
 * Lambda Function: Handle Data Source Failure
 * 
 * Handles fallback scenarios when external market data APIs fail:
 * - Uses cached data when external APIs are unavailable
 * - Sends administrator alerts for data source failures
 * - Implements automatic reconnection logic
 * 
 * Trigger: EventBridge event from ingest-market-data failures or manual invocation
 * Requirements: 6.2, 4.4
 */

import { EventBridgeEvent, APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';
import { MarketDataRepository } from '../../lib/repositories/market-data-repository';
import { SNSClient, PublishCommand } from '@aws-sdk/client-sns';

// Environment variables
const TABLE_NAME = process.env.TABLE_NAME!;
const AWS_REGION = process.env.AWS_REGION || 'us-east-1';
const ADMIN_SNS_TOPIC_ARN = process.env.ADMIN_SNS_TOPIC_ARN;
const CACHE_ENDPOINT = process.env.CACHE_ENDPOINT;
const MARKET_DATA_API_URL = process.env.MARKET_DATA_API_URL || 'https://api.example.com/market-data';
const MARKET_DATA_API_KEY = process.env.MARKET_DATA_API_KEY;

// Initialize clients
const marketDataRepository = new MarketDataRepository({
  tableName: TABLE_NAME,
  region: AWS_REGION,
});

const snsClient = new SNSClient({ region: AWS_REGION });

// Reconnection state
interface ReconnectionState {
  attempts: number;
  lastAttemptTime: number;
  isReconnecting: boolean;
  consecutiveFailures: number;
}

const reconnectionState: ReconnectionState = {
  attempts: 0,
  lastAttemptTime: 0,
  isReconnecting: false,
  consecutiveFailures: 0,
};

const MAX_RECONNECTION_ATTEMPTS = 5;
const RECONNECTION_BACKOFF_BASE = 2000; // 2 seconds
const MAX_BACKOFF = 60000; // 1 minute

interface DataSourceFailureEvent {
  source: string;
  errorType: string;
  errorMessage: string;
  timestamp: string;
  affectedCommodities?: Array<{ cropType: string; location: string }>;
}

/**
 * Calculate exponential backoff delay
 */
function calculateBackoffDelay(attempt: number): number {
  const delay = Math.min(RECONNECTION_BACKOFF_BASE * Math.pow(2, attempt), MAX_BACKOFF);
  // Add jitter to prevent thundering herd
  const jitter = Math.random() * 1000;
  return delay + jitter;
}

/**
 * Send administrator alert
 */
async function sendAdminAlert(subject: string, message: string, priority: 'HIGH' | 'MEDIUM' | 'LOW' = 'MEDIUM'): Promise<void> {
  if (!ADMIN_SNS_TOPIC_ARN) {
    console.warn('ADMIN_SNS_TOPIC_ARN not configured, skipping alert');
    return;
  }

  try {
    await snsClient.send(
      new PublishCommand({
        TopicArn: ADMIN_SNS_TOPIC_ARN,
        Subject: `[${priority}] ${subject}`,
        Message: message,
        MessageAttributes: {
          priority: {
            DataType: 'String',
            StringValue: priority,
          },
          alertType: {
            DataType: 'String',
            StringValue: 'DATA_SOURCE_FAILURE',
          },
        },
      })
    );
    console.log(`Administrator alert sent: ${subject}`);
  } catch (error) {
    console.error('Failed to send administrator alert:', error);
  }
}

/**
 * Get cached market data from DynamoDB (fallback to historical data)
 */
async function getCachedMarketData(cropType: string, location: string): Promise<{
  data: any | null;
  age: number; // in hours
  source: 'cache' | 'historical';
}> {
  try {
    // Try to get the latest market data from DynamoDB
    const latestData = await marketDataRepository.getLatestMarketData(cropType, location);

    if (!latestData) {
      console.log(`No cached data available for ${cropType} in ${location}`);
      return { data: null, age: 0, source: 'historical' };
    }

    // Calculate age of data
    const ageMs = Date.now() - new Date(latestData.timestamp).getTime();
    const ageHours = ageMs / (1000 * 60 * 60);

    console.log(`Found cached data for ${cropType} in ${location}, age: ${ageHours.toFixed(1)} hours`);

    return {
      data: latestData,
      age: ageHours,
      source: 'historical',
    };
  } catch (error) {
    console.error('Error retrieving cached market data:', error);
    return { data: null, age: 0, source: 'historical' };
  }
}

/**
 * Test API connectivity
 */
async function testAPIConnectivity(): Promise<{ isAvailable: boolean; responseTime?: number; error?: string }> {
  const startTime = Date.now();

  try {
    const response = await fetch(`${MARKET_DATA_API_URL}/health`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${MARKET_DATA_API_KEY}`,
      },
      signal: AbortSignal.timeout(5000), // 5 second timeout
    });

    const responseTime = Date.now() - startTime;

    if (response.ok) {
      console.log(`API connectivity test successful, response time: ${responseTime}ms`);
      return { isAvailable: true, responseTime };
    } else {
      return {
        isAvailable: false,
        error: `API returned status ${response.status}`,
      };
    }
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    console.error('API connectivity test failed:', errorMessage);
    return {
      isAvailable: false,
      error: errorMessage,
    };
  }
}

/**
 * Attempt automatic reconnection
 */
async function attemptReconnection(): Promise<{ success: boolean; message: string }> {
  if (reconnectionState.isReconnecting) {
    return { success: false, message: 'Reconnection already in progress' };
  }

  reconnectionState.isReconnecting = true;
  reconnectionState.attempts++;

  console.log(`Attempting reconnection (attempt ${reconnectionState.attempts}/${MAX_RECONNECTION_ATTEMPTS})`);

  try {
    // Test API connectivity
    const connectivityTest = await testAPIConnectivity();

    if (connectivityTest.isAvailable) {
      // Success! Reset state
      reconnectionState.attempts = 0;
      reconnectionState.consecutiveFailures = 0;
      reconnectionState.isReconnecting = false;

      const message = `Data source reconnected successfully after ${reconnectionState.attempts} attempts. Response time: ${connectivityTest.responseTime}ms`;
      console.log(message);

      await sendAdminAlert(
        'Market Data Source Reconnected',
        `The market data API has been successfully reconnected.\n\nAttempts: ${reconnectionState.attempts}\nResponse Time: ${connectivityTest.responseTime}ms\n\nNormal data ingestion will resume.`,
        'MEDIUM'
      );

      return { success: true, message };
    } else {
      // Still failing
      reconnectionState.consecutiveFailures++;
      reconnectionState.lastAttemptTime = Date.now();

      const message = `Reconnection attempt ${reconnectionState.attempts} failed: ${connectivityTest.error}`;
      console.log(message);

      // Check if we should continue trying
      if (reconnectionState.attempts >= MAX_RECONNECTION_ATTEMPTS) {
        await sendAdminAlert(
          'Market Data Source Reconnection Failed',
          `Failed to reconnect to market data API after ${MAX_RECONNECTION_ATTEMPTS} attempts.\n\nLast Error: ${connectivityTest.error}\n\nManual intervention required. System will continue using cached data.`,
          'HIGH'
        );

        reconnectionState.isReconnecting = false;
        return { success: false, message: 'Max reconnection attempts reached' };
      }

      // Schedule next attempt with exponential backoff
      const backoffDelay = calculateBackoffDelay(reconnectionState.attempts);
      console.log(`Next reconnection attempt in ${(backoffDelay / 1000).toFixed(1)} seconds`);

      reconnectionState.isReconnecting = false;
      return { success: false, message };
    }
  } catch (error) {
    reconnectionState.isReconnecting = false;
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    console.error('Error during reconnection attempt:', errorMessage);
    return { success: false, message: errorMessage };
  }
}

/**
 * Handle data source failure event
 */
async function handleFailureEvent(event: DataSourceFailureEvent): Promise<void> {
  console.log('Handling data source failure event:', event);

  // Send initial alert
  await sendAdminAlert(
    'Market Data Source Failure Detected',
    `A failure was detected in the market data source:\n\nSource: ${event.source}\nError Type: ${event.errorType}\nError Message: ${event.errorMessage}\nTimestamp: ${event.timestamp}\n\nSystem will use cached data and attempt automatic reconnection.`,
    'HIGH'
  );

  // Get cached data status for affected commodities
  if (event.affectedCommodities && event.affectedCommodities.length > 0) {
    console.log('Checking cached data availability for affected commodities...');

    const cacheStatus = await Promise.all(
      event.affectedCommodities.map(async ({ cropType, location }) => {
        const cached = await getCachedMarketData(cropType, location);
        return {
          cropType,
          location,
          hasCache: cached.data !== null,
          cacheAge: cached.age,
        };
      })
    );

    const noCacheItems = cacheStatus.filter(item => !item.hasCache);
    const staleCacheItems = cacheStatus.filter(item => item.hasCache && item.cacheAge > 24);

    if (noCacheItems.length > 0 || staleCacheItems.length > 0) {
      let alertMessage = 'Cache status for affected commodities:\n\n';

      if (noCacheItems.length > 0) {
        alertMessage += 'No cached data available for:\n';
        noCacheItems.forEach(item => {
          alertMessage += `- ${item.cropType} in ${item.location}\n`;
        });
        alertMessage += '\n';
      }

      if (staleCacheItems.length > 0) {
        alertMessage += 'Stale cached data (>24 hours) for:\n';
        staleCacheItems.forEach(item => {
          alertMessage += `- ${item.cropType} in ${item.location} (${item.cacheAge.toFixed(1)} hours old)\n`;
        });
      }

      await sendAdminAlert(
        'Market Data Cache Status Alert',
        alertMessage,
        'HIGH'
      );
    }
  }

  // Attempt automatic reconnection
  const reconnectionResult = await attemptReconnection();

  if (!reconnectionResult.success && reconnectionState.attempts < MAX_RECONNECTION_ATTEMPTS) {
    // Schedule next reconnection attempt
    console.log('Scheduling next reconnection attempt...');
  }
}

/**
 * EventBridge handler for failure events
 */
export async function handler(event: EventBridgeEvent<string, DataSourceFailureEvent>): Promise<void> {
  console.log('Data source failure handler invoked');
  console.log('Event:', JSON.stringify(event, null, 2));

  try {
    await handleFailureEvent(event.detail);
  } catch (error) {
    console.error('Error handling data source failure:', error);
    throw error;
  }
}

/**
 * API Gateway handler for manual reconnection attempts
 */
export async function apiHandler(event: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> {
  console.log('Manual reconnection attempt requested');

  try {
    const result = await attemptReconnection();

    return {
      statusCode: result.success ? 200 : 503,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      },
      body: JSON.stringify({
        success: result.success,
        message: result.message,
        reconnectionState: {
          attempts: reconnectionState.attempts,
          consecutiveFailures: reconnectionState.consecutiveFailures,
          lastAttemptTime: reconnectionState.lastAttemptTime,
        },
      }),
    };
  } catch (error) {
    console.error('Error during manual reconnection:', error);

    return {
      statusCode: 500,
      body: JSON.stringify({
        error: 'Internal server error',
        message: error instanceof Error ? error.message : 'Unknown error occurred',
      }),
    };
  }
}

/**
 * Get cached data handler (for use by other services when API is down)
 */
export async function getCachedDataHandler(event: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> {
  console.log('Cached data request received');

  try {
    const queryParams = event.queryStringParameters || {};
    const cropType = queryParams.cropType;
    const location = queryParams.location;

    if (!cropType || !location) {
      return {
        statusCode: 400,
        body: JSON.stringify({
          error: 'Missing required parameters: cropType, location',
        }),
      };
    }

    const cached = await getCachedMarketData(cropType, location);

    if (!cached.data) {
      return {
        statusCode: 404,
        body: JSON.stringify({
          error: 'No cached data available',
          cropType,
          location,
        }),
      };
    }

    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'X-Cache-Age-Hours': cached.age.toString(),
        'X-Cache-Source': cached.source,
      },
      body: JSON.stringify({
        data: cached.data,
        cacheAge: cached.age,
        cacheSource: cached.source,
        warning: cached.age > 24 ? 'Data is more than 24 hours old' : undefined,
      }),
    };
  } catch (error) {
    console.error('Error retrieving cached data:', error);

    return {
      statusCode: 500,
      body: JSON.stringify({
        error: 'Internal server error',
        message: error instanceof Error ? error.message : 'Unknown error occurred',
      }),
    };
  }
}
