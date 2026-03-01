/**
 * Lambda Function: Analyze Farmer Portfolio
 * 
 * This function analyzes a farmer's crop portfolio and provides:
 * - Optimization suggestions based on market trends
 * - Profit scenario calculations
 * - Crop diversification recommendations
 * - Risk assessment
 * 
 * Requirements: 2.3
 */

import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';
import { BedrockClient, MultimodalInput } from '../../lib/services/bedrock/bedrock-client';
import { MarketDataRepository } from '../../lib/repositories/market-data-repository';
import { UserRepository } from '../../lib/repositories/user-repository';

// Environment variables
const TABLE_NAME = process.env.TABLE_NAME!;
const AWS_REGION = process.env.AWS_REGION || 'us-east-1';

// Initialize clients
const bedrockClient = new BedrockClient({ region: AWS_REGION });
const marketDataRepository = new MarketDataRepository({
  tableName: TABLE_NAME,
  region: AWS_REGION,
});
const userRepository = new UserRepository({
  tableName: TABLE_NAME,
  region: AWS_REGION,
});

interface PortfolioAnalysisRequest {
  farmerId: string;
  language?: 'en' | 'bn' | 'hi';
}

interface CropAnalysis {
  cropType: string;
  currentMarketPrice: number | null;
  pricetrend: 'rising' | 'falling' | 'stable';
  profitPotential: 'high' | 'medium' | 'low';
  riskLevel: 'high' | 'medium' | 'low';
  recommendations: string[];
}

interface ProfitScenario {
  scenario: 'optimistic' | 'realistic' | 'pessimistic';
  estimatedRevenue: number;
  assumptions: string[];
}

interface PortfolioAnalysis {
  farmerId: string;
  totalLandArea: number;
  cropAnalysis: CropAnalysis[];
  optimizationSuggestions: string[];
  profitScenarios: ProfitScenario[];
  diversificationRecommendations: string[];
  overallRiskAssessment: string;
}

/**
 * Analyze individual crop performance
 */
async function analyzeCrop(
  cropType: string,
  location: string,
  landArea: number
): Promise<CropAnalysis> {
  // Get market data
  const latestData = await marketDataRepository.getLatestMarketData(cropType, location);
  const statistics = await marketDataRepository.getPriceStatistics(cropType, location, 30);

  // Determine profit potential based on trend and price stability
  let profitPotential: 'high' | 'medium' | 'low' = 'medium';
  let riskLevel: 'high' | 'medium' | 'low' = 'medium';

  if (statistics) {
    const priceVolatility = (statistics.max - statistics.min) / statistics.average;
    
    if (statistics.trend === 'rising' && priceVolatility < 0.2) {
      profitPotential = 'high';
      riskLevel = 'low';
    } else if (statistics.trend === 'falling' || priceVolatility > 0.4) {
      profitPotential = 'low';
      riskLevel = 'high';
    }
  }

  // Generate recommendations
  const recommendations: string[] = [];
  
  if (statistics?.trend === 'rising') {
    recommendations.push('Consider increasing cultivation area for this crop next season');
    recommendations.push('Current market conditions are favorable for selling');
  } else if (statistics?.trend === 'falling') {
    recommendations.push('Consider reducing cultivation area or switching to alternative crops');
    recommendations.push('Explore value-added processing to improve margins');
  } else {
    recommendations.push('Maintain current cultivation levels');
    recommendations.push('Monitor market trends closely for changes');
  }

  if (riskLevel === 'high') {
    recommendations.push('Consider crop insurance to mitigate price volatility risks');
  }

  return {
    cropType,
    currentMarketPrice: latestData?.price || null,
    pricetrend: statistics?.trend || 'stable',
    profitPotential,
    riskLevel,
    recommendations,
  };
}

/**
 * Calculate profit scenarios
 */
function calculateProfitScenarios(
  cropAnalyses: CropAnalysis[],
  landArea: number
): ProfitScenario[] {
  const scenarios: ProfitScenario[] = [];

  // Calculate average price per crop
  const totalCrops = cropAnalyses.length;
  const avgPricePerCrop = cropAnalyses.reduce((sum, crop) => 
    sum + (crop.currentMarketPrice || 0), 0) / totalCrops;

  // Optimistic scenario (20% above current prices)
  scenarios.push({
    scenario: 'optimistic',
    estimatedRevenue: avgPricePerCrop * landArea * 1.2,
    assumptions: [
      'Favorable weather conditions',
      'Strong market demand',
      'Minimal crop losses',
      'Prices 20% above current levels',
    ],
  });

  // Realistic scenario (current prices)
  scenarios.push({
    scenario: 'realistic',
    estimatedRevenue: avgPricePerCrop * landArea,
    assumptions: [
      'Normal weather conditions',
      'Stable market demand',
      'Average crop yield',
      'Current market prices maintained',
    ],
  });

  // Pessimistic scenario (20% below current prices)
  scenarios.push({
    scenario: 'pessimistic',
    estimatedRevenue: avgPricePerCrop * landArea * 0.8,
    assumptions: [
      'Adverse weather conditions',
      'Weak market demand',
      'Some crop losses',
      'Prices 20% below current levels',
    ],
  });

  return scenarios;
}

/**
 * Generate AI-powered optimization suggestions
 */
async function generateOptimizationSuggestions(
  farmerId: string,
  cropAnalyses: CropAnalysis[],
  landArea: number,
  location: string,
  language: 'en' | 'bn' | 'hi'
): Promise<{
  optimizationSuggestions: string[];
  diversificationRecommendations: string[];
  overallRiskAssessment: string;
}> {
  // Prepare context for AI
  const cropSummary = cropAnalyses.map(crop => 
    `${crop.cropType}: Price ₹${crop.currentMarketPrice || 'N/A'}, Trend: ${crop.pricetrend}, Profit Potential: ${crop.profitPotential}, Risk: ${crop.riskLevel}`
  ).join('\n');

  const systemPrompt = `You are an agricultural portfolio optimization expert.
Analyze the farmer's crop portfolio and provide actionable optimization suggestions.

Guidelines:
- Consider market trends, profit potential, and risk levels
- Suggest crop diversification strategies
- Recommend timing for planting and selling
- Consider seasonal factors and local conditions
- Provide practical, implementable advice
- Focus on maximizing profit while managing risk`;

  const userPrompt = `Analyze this farmer's portfolio and provide optimization suggestions:

Location: ${location}
Total Land: ${landArea} acres
Current Crops:
${cropSummary}

Please provide:
1. Top 3-5 optimization suggestions for maximizing profit
2. Crop diversification recommendations to reduce risk
3. Overall risk assessment and mitigation strategies

Provide response in JSON format:
{
  "optimizationSuggestions": ["suggestion1", "suggestion2", "suggestion3"],
  "diversificationRecommendations": ["recommendation1", "recommendation2"],
  "overallRiskAssessment": "detailed risk assessment"
}`;

  const multimodalInput: MultimodalInput = {
    text: userPrompt,
  };

  console.log('Generating portfolio optimization with Bedrock...');
  const aiResponse = await bedrockClient.invoke(multimodalInput, systemPrompt);

  // Parse AI response
  try {
    const jsonMatch = aiResponse.content.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      const parsed = JSON.parse(jsonMatch[0]);
      return {
        optimizationSuggestions: parsed.optimizationSuggestions || [],
        diversificationRecommendations: parsed.diversificationRecommendations || [],
        overallRiskAssessment: parsed.overallRiskAssessment || 'Risk assessment in progress',
      };
    }
  } catch (e) {
    console.log('Failed to parse JSON response, using fallback');
  }

  // Fallback suggestions
  return {
    optimizationSuggestions: [
      'Focus on crops with rising price trends and high profit potential',
      'Consider staggered planting to spread market risk',
      'Explore contract farming opportunities for price stability',
    ],
    diversificationRecommendations: [
      'Diversify across 3-4 different crop types to reduce risk',
      'Include both cash crops and food crops in your portfolio',
      'Consider adding high-value crops with strong market demand',
    ],
    overallRiskAssessment: 'Portfolio shows moderate risk. Diversification and market monitoring recommended.',
  };
}

/**
 * Main Lambda handler
 */
export async function handler(event: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> {
  console.log('Received portfolio analysis request');

  try {
    // Parse request
    const request: PortfolioAnalysisRequest = JSON.parse(event.body || '{}');

    // Validate required fields
    if (!request.farmerId) {
      return {
        statusCode: 400,
        body: JSON.stringify({
          error: 'Missing required field: farmerId',
        }),
      };
    }

    // Get user profile
    const userProfile = await userRepository.getUserProfile(request.farmerId);
    
    if (!userProfile) {
      return {
        statusCode: 404,
        body: JSON.stringify({
          error: 'Farmer profile not found',
        }),
      };
    }

    const language = request.language || userProfile.language || 'en';
    const location = userProfile.location.district;

    // Analyze each crop in the portfolio
    console.log(`Analyzing portfolio for farmer ${request.farmerId}`);
    const cropAnalyses: CropAnalysis[] = [];

    for (const cropType of userProfile.cropTypes) {
      const analysis = await analyzeCrop(
        cropType,
        location,
        userProfile.landArea / userProfile.cropTypes.length // Assume equal distribution
      );
      cropAnalyses.push(analysis);
    }

    // Calculate profit scenarios
    const profitScenarios = calculateProfitScenarios(cropAnalyses, userProfile.landArea);

    // Generate AI-powered optimization suggestions
    const aiSuggestions = await generateOptimizationSuggestions(
      request.farmerId,
      cropAnalyses,
      userProfile.landArea,
      location,
      language as 'en' | 'bn' | 'hi'
    );

    // Build response
    const response: PortfolioAnalysis = {
      farmerId: request.farmerId,
      totalLandArea: userProfile.landArea,
      cropAnalysis: cropAnalyses,
      optimizationSuggestions: aiSuggestions.optimizationSuggestions,
      profitScenarios,
      diversificationRecommendations: aiSuggestions.diversificationRecommendations,
      overallRiskAssessment: aiSuggestions.overallRiskAssessment,
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
    console.error('Error analyzing portfolio:', error);

    return {
      statusCode: 500,
      body: JSON.stringify({
        error: 'Internal server error',
        message: error instanceof Error ? error.message : 'Unknown error occurred',
      }),
    };
  }
}
