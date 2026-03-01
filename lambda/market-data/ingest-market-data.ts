/**
 * Lambda Function: Ingest Market Data
 * 
 * Scheduled function that runs every 15 minutes to fetch commodity price data
 * from external APIs, validate for anomalies, and store in DynamoDB.
 * 
 * Trigger: EventBridge scheduled rule (every 15 minutes)
 * Requirements: 6.1, 6.3, 6.4
 */

import { EventBridgeEvent } from 'aws-lambda';
import { MarketDataRepository, CreateMarketDataInput } from '../../lib/repositories/market-data-repository';
import { SNSClient, PublishCommand } from '@aws-sdk/client-sns';
import { createCircuitBreaker, CircuitBreaker } from './circuit-breaker';

// Environment variables
const TABLE_NAME = process.env.TABLE_NAME!;
const AWS_REGION = process.env.AWS_REGION || 'us-east-1';
const ADMIN_SNS_TOPIC_ARN = process.env.ADMIN_SNS_TOPIC_ARN;
const MARKET_DATA_API_KEY = process.env.MARKET_DATA_API_KEY;
const MARKET_DATA_API_URL = process.env.MARKET_DATA_API_URL || 'https://api.example.com/market-data';

// Initialize clients
const marketDataRepository = new MarketDataRepository({
  tableName: TABLE_NAME,
  region: AWS_REGION,
});

const snsClient = new SNSClient({ region: AWS_REGION });

// Initialize circuit breaker
const circuitBreaker: CircuitBreaker = createCircuitBreaker('MarketDataAPI', {
  failureThreshold: 3,
  successThreshold: 2,
  timeout: 60000, // 1 minute
});

// Commodity and location configurations
const COMMODITY_CONFIGS = [
  { cropType: 'Potato', locations: ['Kolkata', 'Delhi', 'Mumbai', 'Bangalore'] },
  { cropType: 'Rice', locations: ['Kolkata', 'Delhi', 'Mumbai', 'Hyderabad'] },
  { cropType: 'Wheat', locations: ['Delhi', 'Jaipur', 'Lucknow', 'Chandigarh'] },
  { cropType: 'Tomato', locations: ['Kolkata', 'Delhi', 'Mumbai', 'Bangalore'] },
  { cropType: 'Onion', locations: ['Nashik', 'Delhi', 'Bangalore', 'Kolkata'] },
];

interface ExternalMarketDataResponse {
  commodity: string;
  market: string;
  district: string;
  state: string;
  price: number;
  unit: string;
  quality: string;
  timestamp: string;
}

/**
 * Check circuit breaker state
 */
function checkCircuitBreaker(): boolean {
  return circuitBreaker.isAllowingRequests();
}

/**
 * Fetch market data from external API
 */
async function fetchExternalMarketData(
  cropType: string,
  location: string
): Promise<ExternalMarketDataResponse | null> {
  if (!checkCircuitBreaker()) {
    throw new Error('Circuit breaker is OPEN');
  }

  return await circuitBreaker.execute(async () => {
    const url = `${MARKET_DATA_API_URL}/prices?commodity=${encodeURIComponent(cropType)}&location=${encodeURIComponent(location)}`;
    
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${MARKET_DATA_API_KEY}`,
        'Content-Type': 'application/json',
      },
      signal: AbortSignal.timeout(10000), // 10 second timeout
    });

    if (!response.ok) {
      throw new Error(`API returned status ${response.status}`);
    }

    return await response.json() as ExternalMarketDataResponse;

    const data = await response.json();
    return data;
  });
}

/**
 * Validate price data for anomalies
 */
async function validatePriceData(
  cropType: string,
  location: string,
  newPrice: number
): Promise<{ isValid: boolean; anomalyReason?: string }> {
  try {
    // Get historical statistics
    const statistics = await marketDataRepository.getPriceStatistics(cropType, location, 30);

    if (!statistics) {
      // No historical data, accept the price
      return { isValid: true };
    }

    // Check for extreme deviation (>50% from average)
    const deviationPercent = Math.abs((newPrice - statistics.average) / statistics.average) * 100;

    if (deviationPercent > 50) {
      return {
        isValid: false,
        anomalyReason: `Price deviation of ${deviationPercent.toFixed(1)}% from 30-day average (₹${statistics.average.toFixed(2)})`,
      };
    }

    // Check if price is outside historical range with buffer
    const rangeBuffer = (statistics.max - statistics.min) * 0.2; // 20% buffer
    if (newPrice < statistics.min - rangeBuffer || newPrice > statistics.max + rangeBuffer) {
      return {
        isValid: false,
        anomalyReason: `Price ₹${newPrice} outside historical range ₹${statistics.min}-₹${statistics.max} with buffer`,
      };
    }

    return { isValid: true };
  } catch (error) {
    console.error('Error validating price data:', error);
    // On validation error, accept the price but log the issue
    return { isValid: true };
  }
}

/**
 * Send administrator alert
 */
async function sendAdminAlert(subject: string, message: string): Promise<void> {
  if (!ADMIN_SNS_TOPIC_ARN) {
    console.warn('ADMIN_SNS_TOPIC_ARN not configured, skipping alert');
    return;
  }

  try {
    await snsClient.send(
      new PublishCommand({
        TopicArn: ADMIN_SNS_TOPIC_ARN,
        Subject: subject,
        Message: message,
      })
    );
    console.log('Administrator alert sent successfully');
  } catch (error) {
    console.error('Failed to send administrator alert:', error);
  }
}

/**
 * Process market data for a single commodity and location
 */
async function processMarketData(cropType: string, location: string): Promise<{
  success: boolean;
  error?: string;
}> {
  try {
    console.log(`Processing market data for ${cropType} in ${location}`);

    // Fetch data from external API
    const externalData = await fetchExternalMarketData(cropType, location);

    if (!externalData) {
      return { success: false, error: 'No data returned from API' };
    }

    // Validate price data
    const validation = await validatePriceData(cropType, location, externalData.price);

    if (!validation.isValid) {
      console.warn(`Anomaly detected: ${validation.anomalyReason}`);
      await sendAdminAlert(
        `Market Data Anomaly Detected: ${cropType} in ${location}`,
        `An anomaly was detected in market data:\n\nCrop: ${cropType}\nLocation: ${location}\nPrice: ₹${externalData.price}\nReason: ${validation.anomalyReason}\n\nPlease review the data source.`
      );
      // Still store the data but flag it
    }

    // Store in DynamoDB
    const marketDataInput: CreateMarketDataInput = {
      cropType: externalData.commodity,
      location: externalData.market,
      district: externalData.district,
      state: externalData.state,
      price: externalData.price,
      marketName: externalData.market,
      quality: externalData.quality,
      unit: externalData.unit,
      source: 'external_api',
      trend: undefined, // Will be calculated by repository
    };

    await marketDataRepository.createMarketData(marketDataInput);
    console.log(`Successfully stored market data for ${cropType} in ${location}`);

    return { success: true };
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    console.error(`Error processing market data for ${cropType} in ${location}:`, errorMessage);
    return { success: false, error: errorMessage };
  }
}

/**
 * Main Lambda handler
 */
export async function handler(event: EventBridgeEvent<string, any>): Promise<void> {
  console.log('Market data ingestion started');
  console.log('Event:', JSON.stringify(event, null, 2));

  const results: Array<{ cropType: string; location: string; success: boolean; error?: string }> = [];
  let totalSuccess = 0;
  let totalFailures = 0;

  // Process all commodity and location combinations
  for (const config of COMMODITY_CONFIGS) {
    for (const location of config.locations) {
      const result = await processMarketData(config.cropType, location);
      results.push({
        cropType: config.cropType,
        location,
        success: result.success,
        error: result.error,
      });

      if (result.success) {
        totalSuccess++;
      } else {
        totalFailures++;
      }

      // Small delay to avoid overwhelming the API
      await new Promise(resolve => setTimeout(resolve, 100));
    }
  }

  console.log(`Market data ingestion completed: ${totalSuccess} success, ${totalFailures} failures`);

  // Get circuit breaker metrics
  const cbMetrics = circuitBreaker.getMetrics();

  // Send alert if there were significant failures
  if (totalFailures > 0) {
    const failureDetails = results
      .filter(r => !r.success)
      .map(r => `- ${r.cropType} in ${r.location}: ${r.error}`)
      .join('\n');

    await sendAdminAlert(
      `Market Data Ingestion Failures: ${totalFailures} of ${results.length}`,
      `Market data ingestion completed with failures:\n\nTotal Success: ${totalSuccess}\nTotal Failures: ${totalFailures}\n\nFailure Details:\n${failureDetails}\n\nCircuit Breaker State: ${cbMetrics.state}\nFailure Count: ${cbMetrics.failures}\nTotal Requests: ${cbMetrics.totalRequests}`
    );
  }

  // Log summary
  console.log('Ingestion Summary:', {
    totalProcessed: results.length,
    totalSuccess,
    totalFailures,
    circuitBreakerState: cbMetrics.state,
    circuitBreakerMetrics: cbMetrics,
  });
}
