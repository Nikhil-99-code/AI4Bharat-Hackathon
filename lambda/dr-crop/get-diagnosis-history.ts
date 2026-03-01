/**
 * Lambda Function: Get Diagnosis History
 * 
 * This function retrieves a farmer's crop diagnosis history with pagination,
 * filtering by date range and disease type.
 * 
 * Requirements: 1.5
 */

import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';
import { CropDiagnosisRepository } from '../../lib/repositories/crop-diagnosis-repository';
import { CropDiagnosis } from '../../lib/types/domain-entities';

// Environment variables
const TABLE_NAME = process.env.TABLE_NAME!;
const AWS_REGION = process.env.AWS_REGION || 'us-east-1';

// Initialize repository
const diagnosisRepository = new CropDiagnosisRepository({
  tableName: TABLE_NAME,
  region: AWS_REGION,
});

interface GetDiagnosisHistoryRequest {
  farmerId: string;
  limit?: number;
  nextToken?: string;
  startDate?: string; // ISO 8601 format
  endDate?: string; // ISO 8601 format
  diseaseType?: string;
  severityLevel?: 'low' | 'medium' | 'high' | 'critical';
}

interface DiagnosisHistoryResponse {
  diagnoses: CropDiagnosis[];
  count: number;
  nextToken?: string;
  hasMore: boolean;
}

/**
 * Filter diagnoses by date range
 */
function filterByDateRange(
  diagnoses: CropDiagnosis[],
  startDate?: string,
  endDate?: string
): CropDiagnosis[] {
  if (!startDate && !endDate) {
    return diagnoses;
  }

  const start = startDate ? new Date(startDate).getTime() : 0;
  const end = endDate ? new Date(endDate).getTime() : Date.now();

  return diagnoses.filter(diagnosis => {
    const diagnosisTime = diagnosis.createdAt.getTime();
    return diagnosisTime >= start && diagnosisTime <= end;
  });
}

/**
 * Filter diagnoses by disease type
 */
function filterByDiseaseType(
  diagnoses: CropDiagnosis[],
  diseaseType: string
): CropDiagnosis[] {
  const normalizedType = diseaseType.toLowerCase().trim();
  
  return diagnoses.filter(diagnosis => {
    if (!diagnosis.diseaseName) {
      return false;
    }
    return diagnosis.diseaseName.toLowerCase().includes(normalizedType);
  });
}

/**
 * Parse pagination token
 */
function parsePaginationToken(token: string): Record<string, any> | undefined {
  try {
    return JSON.parse(Buffer.from(token, 'base64').toString('utf-8'));
  } catch (error) {
    console.error('Invalid pagination token:', error);
    return undefined;
  }
}

/**
 * Create pagination token
 */
function createPaginationToken(lastEvaluatedKey: Record<string, any>): string {
  return Buffer.from(JSON.stringify(lastEvaluatedKey)).toString('base64');
}

/**
 * Main Lambda handler
 */
export async function handler(event: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> {
  console.log('Received diagnosis history request');

  try {
    // Parse query parameters
    const farmerId = event.queryStringParameters?.farmerId;
    const limit = event.queryStringParameters?.limit
      ? parseInt(event.queryStringParameters.limit)
      : 50;
    const nextToken = event.queryStringParameters?.nextToken;
    const startDate = event.queryStringParameters?.startDate;
    const endDate = event.queryStringParameters?.endDate;
    const diseaseType = event.queryStringParameters?.diseaseType;
    const severityLevel = event.queryStringParameters?.severityLevel as
      | 'low'
      | 'medium'
      | 'high'
      | 'critical'
      | undefined;

    // Validate required fields
    if (!farmerId) {
      return {
        statusCode: 400,
        body: JSON.stringify({
          error: 'Missing required parameter: farmerId',
        }),
      };
    }

    // Validate limit
    if (limit < 1 || limit > 100) {
      return {
        statusCode: 400,
        body: JSON.stringify({
          error: 'Limit must be between 1 and 100',
        }),
      };
    }

    let diagnoses: CropDiagnosis[];
    let lastEvaluatedKey: Record<string, any> | undefined;

    // Parse pagination token if provided
    const exclusiveStartKey = nextToken ? parsePaginationToken(nextToken) : undefined;

    // Query based on filters
    if (severityLevel) {
      // Query by severity level using GSI2
      console.log(`Querying diagnoses by severity: ${severityLevel}`);
      const result = await diagnosisRepository.getDiagnosesBySeverity(severityLevel, limit);
      
      // Filter by farmerId since GSI2 returns all farmers
      diagnoses = result.items.filter(d => d.farmerId === farmerId);
      lastEvaluatedKey = result.lastEvaluatedKey;
    } else if (diseaseType) {
      // Query by disease type using GSI3
      console.log(`Querying diagnoses by disease: ${diseaseType}`);
      const result = await diagnosisRepository.getDiagnosesByDisease(diseaseType, limit);
      
      // Filter by farmerId since GSI3 returns all farmers
      diagnoses = result.items.filter(d => d.farmerId === farmerId);
      lastEvaluatedKey = result.lastEvaluatedKey;
    } else {
      // Query all diagnoses for farmer
      console.log(`Querying all diagnoses for farmer: ${farmerId}`);
      const result = await diagnosisRepository.getDiagnosisHistory(
        farmerId,
        limit,
        exclusiveStartKey
      );
      diagnoses = result.items;
      lastEvaluatedKey = result.lastEvaluatedKey;
    }

    // Apply date range filter if specified
    if (startDate || endDate) {
      console.log(`Filtering by date range: ${startDate} to ${endDate}`);
      diagnoses = filterByDateRange(diagnoses, startDate, endDate);
    }

    // Apply disease type filter if specified and not already queried by disease
    if (diseaseType && !severityLevel) {
      console.log(`Filtering by disease type: ${diseaseType}`);
      diagnoses = filterByDiseaseType(diagnoses, diseaseType);
    }

    // Create response
    const response: DiagnosisHistoryResponse = {
      diagnoses,
      count: diagnoses.length,
      hasMore: !!lastEvaluatedKey,
    };

    if (lastEvaluatedKey) {
      response.nextToken = createPaginationToken(lastEvaluatedKey);
    }

    console.log(`Returning ${diagnoses.length} diagnoses, hasMore: ${response.hasMore}`);

    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      },
      body: JSON.stringify(response),
    };
  } catch (error) {
    console.error('Error retrieving diagnosis history:', error);

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
 * Get diagnosis statistics for a farmer
 */
export async function getStatistics(farmerId: string): Promise<{
  totalDiagnoses: number;
  diseasesDetected: number;
  healthyScans: number;
  followUpRequired: number;
  severityBreakdown: Record<string, number>;
  commonDiseases: Array<{ disease: string; count: number }>;
}> {
  const result = await diagnosisRepository.getDiagnosisHistory(farmerId, 1000);
  const diagnoses = result.items;

  const stats = {
    totalDiagnoses: diagnoses.length,
    diseasesDetected: 0,
    healthyScans: 0,
    followUpRequired: 0,
    severityBreakdown: {
      low: 0,
      medium: 0,
      high: 0,
      critical: 0,
    },
    commonDiseases: [] as Array<{ disease: string; count: number }>,
  };

  const diseaseCount = new Map<string, number>();

  for (const diagnosis of diagnoses) {
    if (diagnosis.diseaseIdentified) {
      stats.diseasesDetected++;
      
      if (diagnosis.diseaseName) {
        diseaseCount.set(
          diagnosis.diseaseName,
          (diseaseCount.get(diagnosis.diseaseName) || 0) + 1
        );
      }
    } else {
      stats.healthyScans++;
    }

    if (diagnosis.followUpRequired) {
      stats.followUpRequired++;
    }

    if (diagnosis.severityLevel) {
      stats.severityBreakdown[diagnosis.severityLevel]++;
    }
  }

  // Get top 5 common diseases
  stats.commonDiseases = Array.from(diseaseCount.entries())
    .map(([disease, count]) => ({ disease, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 5);

  return stats;
}

/**
 * Lambda handler for statistics endpoint
 */
export async function statisticsHandler(
  event: APIGatewayProxyEvent
): Promise<APIGatewayProxyResult> {
  console.log('Received diagnosis statistics request');

  try {
    const farmerId = event.queryStringParameters?.farmerId;

    if (!farmerId) {
      return {
        statusCode: 400,
        body: JSON.stringify({
          error: 'Missing required parameter: farmerId',
        }),
      };
    }

    const statistics = await getStatistics(farmerId);

    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      },
      body: JSON.stringify(statistics),
    };
  } catch (error) {
    console.error('Error retrieving diagnosis statistics:', error);

    return {
      statusCode: 500,
      body: JSON.stringify({
        error: 'Internal server error',
        message: error instanceof Error ? error.message : 'Unknown error occurred',
      }),
    };
  }
}
