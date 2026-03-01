/**
 * Lambda Function: Get Market Intelligence
 * 
 * This function provides comprehensive market intelligence including:
 * - Current market prices and trends
 * - AI-powered market analysis and insights
 * - Personalized recommendations based on farmer portfolio
 * - Government scheme information
 * 
 * Requirements: 2.1, 2.3
 */

import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';
import { BedrockClient, MultimodalInput } from '../../lib/services/bedrock/bedrock-client';
import { PromptTemplateManager, Language } from '../../lib/services/bedrock/prompt-templates';
import { MarketDataRepository } from '../../lib/repositories/market-data-repository';
import { UserRepository } from '../../lib/repositories/user-repository';

// Environment variables
const TABLE_NAME = process.env.TABLE_NAME!;
const AWS_REGION = process.env.AWS_REGION || 'us-east-1';
const CACHE_ENDPOINT = process.env.CACHE_ENDPOINT;

// Initialize clients
const bedrockClient = new BedrockClient({ region: AWS_REGION });
const promptManager = new PromptTemplateManager();
const marketDataRepository = new MarketDataRepository({
  tableName: TABLE_NAME,
  region: AWS_REGION,
});
const userRepository = new UserRepository({
  tableName: TABLE_NAME,
  region: AWS_REGION,
});

interface MarketIntelligenceRequest {
  farmerId: string;
  cropType: string;
  location?: string;
  language?: 'en' | 'bn' | 'hi';
}

interface MarketIntelligence {
  cropType: string;
  location: string;
  currentPrice: {
    price: number;
    unit: string;
    marketName: string;
    quality: string;
    timestamp: Date;
  } | null;
  historicalTrends: {
    period: string;
    average: number;
    min: number;
    max: number;
    trend: 'rising' | 'falling' | 'stable';
  } | null;
  forecast: {
    shortTerm: string;
    mediumTerm: string;
    seasonalFactors: string[];
  };
  marketInsights: string[];
  actionableRecommendations: string[];
  governmentSchemes: Array<{
    schemeName: string;
    eligibility: string;
    benefits: string;
  }>;
}

/**
 * Get cached market data (if ElastiCache is available)
 */
async function getCachedMarketData(cacheKey: string): Promise<any | null> {
  if (!CACHE_ENDPOINT) {
    return null;
  }

  try {
    // TODO: Implement Redis cache lookup when ElastiCache is configured
    // For now, return null to fetch from DynamoDB
    return null;
  } catch (error) {
    console.error('Cache lookup failed:', error);
    return null;
  }
}

/**
 * Set cached market data (if ElastiCache is available)
 */
async function setCachedMarketData(cacheKey: string, data: any, ttlSeconds: number = 900): Promise<void> {
  if (!CACHE_ENDPOINT) {
    return;
  }

  try {
    // TODO: Implement Redis cache storage when ElastiCache is configured
    console.log(`Would cache data with key: ${cacheKey} for ${ttlSeconds}s`);
  } catch (error) {
    console.error('Cache storage failed:', error);
  }
}

/**
 * Fetch market data with caching
 */
async function fetchMarketData(cropType: string, location: string) {
  const cacheKey = `market:${cropType}:${location}`;
  
  // Try cache first
  const cached = await getCachedMarketData(cacheKey);
  if (cached) {
    console.log('Cache hit for market data');
    return cached;
  }

  // Fetch from DynamoDB
  console.log('Cache miss, fetching from DynamoDB');
  const latestData = await marketDataRepository.getLatestMarketData(cropType, location);
  const statistics = await marketDataRepository.getPriceStatistics(cropType, location, 30);

  const result = {
    latestData,
    statistics,
  };

  // Cache the result
  await setCachedMarketData(cacheKey, result, 900); // 15 minutes TTL

  return result;
}

/**
 * Generate AI-powered market insights
 */
async function generateMarketInsights(
  cropType: string,
  location: string,
  currentPrice: number | null,
  trend: string,
  farmerPortfolio: string,
  language: Language
): Promise<{
  forecast: { shortTerm: string; mediumTerm: string; seasonalFactors: string[] };
  insights: string[];
  recommendations: string[];
}> {
  const promptVariables = {
    cropType,
    location,
    currentPrice: currentPrice ? `₹${currentPrice}` : 'Not available',
    trend: trend || 'stable',
    portfolio: farmerPortfolio,
  };

  const { system, user } = promptManager.getRenderedPrompt(
    'market_intelligence',
    promptVariables,
    language
  );

  // Add structured output instruction
  const enhancedUser = `${user}

Please provide your response in the following JSON format:
{
  "forecast": {
    "shortTerm": "1-2 week price forecast and factors",
    "mediumTerm": "1-3 month outlook",
    "seasonalFactors": ["factor1", "factor2"]
  },
  "insights": ["insight1", "insight2", "insight3"],
  "recommendations": ["recommendation1", "recommendation2", "recommendation3"]
}`;

  const multimodalInput: MultimodalInput = {
    text: enhancedUser,
  };

  console.log('Generating market insights with Bedrock...');
  const aiResponse = await bedrockClient.invoke(multimodalInput, system);

  // Parse AI response
  try {
    const jsonMatch = aiResponse.content.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      const parsed = JSON.parse(jsonMatch[0]);
      return {
        forecast: parsed.forecast || {
          shortTerm: 'Analysis in progress',
          mediumTerm: 'Analysis in progress',
          seasonalFactors: [],
        },
        insights: parsed.insights || [],
        recommendations: parsed.recommendations || [],
      };
    }
  } catch (e) {
    console.log('Failed to parse JSON response, using fallback');
  }

  // Fallback parsing
  return {
    forecast: {
      shortTerm: 'Market analysis suggests monitoring prices closely over the next 1-2 weeks.',
      mediumTerm: 'Medium-term outlook depends on seasonal demand and supply factors.',
      seasonalFactors: ['Seasonal demand', 'Weather conditions', 'Supply chain factors'],
    },
    insights: [
      'Current market conditions are being analyzed.',
      'Consider local market trends and demand patterns.',
      'Monitor government announcements for policy changes.',
    ],
    recommendations: [
      'Track daily price movements in your local market.',
      'Consider storage options if prices are expected to rise.',
      'Consult with FPO for collective selling opportunities.',
    ],
  };
}

/**
 * Get farmer portfolio summary
 */
async function getFarmerPortfolio(farmerId: string): Promise<string> {
  const userProfile = await userRepository.getUserProfile(farmerId);
  
  if (!userProfile) {
    return 'No portfolio information available';
  }

  return `Crops: ${userProfile.cropTypes.join(', ')}; Land: ${userProfile.landArea} acres; Location: ${userProfile.location.district}, ${userProfile.location.state}`;
}

/**
 * Get government schemes (placeholder - will be enhanced in sub-task 6.5)
 */
function getGovernmentSchemes(cropType: string, location: string): Array<{
  schemeName: string;
  eligibility: string;
  benefits: string;
}> {
  // Placeholder implementation
  return [
    {
      schemeName: 'PM-KISAN',
      eligibility: 'All landholding farmers',
      benefits: '₹6000 per year in three installments',
    },
  ];
}

/**
 * Main Lambda handler
 */
export async function handler(event: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> {
  console.log('Received market intelligence request');

  try {
    // Parse request
    const request: MarketIntelligenceRequest = JSON.parse(event.body || '{}');

    // Validate required fields
    if (!request.farmerId || !request.cropType) {
      return {
        statusCode: 400,
        body: JSON.stringify({
          error: 'Missing required fields: farmerId, cropType',
        }),
      };
    }

    // Get user profile for location if not provided
    const userProfile = await userRepository.getUserProfile(request.farmerId);
    const location = request.location || userProfile?.location.district || 'Unknown';
    const language = request.language || userProfile?.language || 'en';

    // Fetch market data with caching
    console.log(`Fetching market data for ${request.cropType} in ${location}`);
    const { latestData, statistics } = await fetchMarketData(request.cropType, location);

    // Get farmer portfolio
    const farmerPortfolio = await getFarmerPortfolio(request.farmerId);

    // Generate AI-powered insights
    const aiInsights = await generateMarketInsights(
      request.cropType,
      location,
      latestData?.price || null,
      statistics?.trend || 'stable',
      farmerPortfolio,
      language as Language
    );

    // Get government schemes
    const schemes = getGovernmentSchemes(request.cropType, location);

    // Build response
    const response: MarketIntelligence = {
      cropType: request.cropType,
      location,
      currentPrice: latestData ? {
        price: latestData.price,
        unit: latestData.unit,
        marketName: latestData.marketName,
        quality: latestData.quality,
        timestamp: latestData.timestamp,
      } : null,
      historicalTrends: statistics ? {
        period: '30 days',
        average: statistics.average,
        min: statistics.min,
        max: statistics.max,
        trend: statistics.trend,
      } : null,
      forecast: aiInsights.forecast,
      marketInsights: aiInsights.insights,
      actionableRecommendations: aiInsights.recommendations,
      governmentSchemes: schemes,
    };

    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      },
      body: JSON.stringify(response),
    };
  } catch (error) {
    console.error('Error generating market intelligence:', error);

    return {
      statusCode: 500,
      body: JSON.stringify({
        error: 'Internal server error',
        message: error instanceof Error ? error.message : 'Unknown error occurred',
      }),
    };
  }
}
