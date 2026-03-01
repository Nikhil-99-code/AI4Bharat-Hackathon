/**
 * Lambda Function: Get Government Schemes
 * 
 * This function provides government scheme information including:
 * - Scheme matching based on farmer's crops and location
 * - Eligibility recommendations
 * - Application guidance
 * - Benefit calculations
 * 
 * Requirements: 2.4
 */

import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';
import { BedrockClient, MultimodalInput } from '../../lib/services/bedrock/bedrock-client';
import { UserRepository } from '../../lib/repositories/user-repository';

// Environment variables
const TABLE_NAME = process.env.TABLE_NAME!;
const AWS_REGION = process.env.AWS_REGION || 'us-east-1';

// Initialize clients
const bedrockClient = new BedrockClient({ region: AWS_REGION });
const userRepository = new UserRepository({
  tableName: TABLE_NAME,
  region: AWS_REGION,
});

interface GovernmentSchemeRequest {
  farmerId: string;
  cropTypes?: string[];
  language?: 'en' | 'bn' | 'hi';
}

interface GovernmentScheme {
  schemeId: string;
  schemeName: string;
  description: string;
  eligibilityCriteria: string[];
  benefits: string[];
  applicationProcess: string;
  documents: string[];
  deadline?: string;
  contactInfo: string;
  matchScore: number; // 0-100, how well it matches farmer's profile
  matchReasons: string[];
}

interface SchemeRecommendation {
  farmerId: string;
  location: string;
  cropTypes: string[];
  schemes: GovernmentScheme[];
  totalPotentialBenefits: string;
  applicationGuidance: string[];
}

/**
 * Government scheme database (in production, this would be a separate DynamoDB table or external API)
 */
const GOVERNMENT_SCHEMES = [
  {
    schemeId: 'PM-KISAN',
    schemeName: 'Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)',
    description: 'Income support scheme providing direct financial assistance to farmers',
    eligibilityCriteria: [
      'All landholding farmers',
      'Valid Aadhaar card',
      'Bank account linked to Aadhaar',
    ],
    benefits: [
      '₹6,000 per year in three equal installments',
      'Direct bank transfer',
      'No upper limit on land holding',
    ],
    applicationProcess: 'Apply online at pmkisan.gov.in or through Common Service Centers',
    documents: ['Aadhaar card', 'Bank account details', 'Land ownership documents'],
    contactInfo: 'PM-KISAN Helpline: 155261 / 011-24300606',
    applicableCrops: ['all'],
    applicableStates: ['all'],
  },
  {
    schemeId: 'PMFBY',
    schemeName: 'Pradhan Mantri Fasal Bima Yojana (PMFBY)',
    description: 'Crop insurance scheme providing financial support against crop loss',
    eligibilityCriteria: [
      'All farmers growing notified crops',
      'Sharecroppers and tenant farmers eligible',
      'Must enroll before sowing/planting',
    ],
    benefits: [
      'Coverage against natural calamities, pests, and diseases',
      'Low premium rates (2% for Kharif, 1.5% for Rabi)',
      'Quick claim settlement',
    ],
    applicationProcess: 'Apply through banks, CSCs, or insurance company portals',
    documents: ['Aadhaar card', 'Bank account', 'Land records', 'Sowing certificate'],
    contactInfo: 'PMFBY Helpline: 011-23382012',
    applicableCrops: ['rice', 'wheat', 'potato', 'cotton', 'sugarcane'],
    applicableStates: ['all'],
  },
  {
    schemeId: 'KCC',
    schemeName: 'Kisan Credit Card (KCC)',
    description: 'Credit facility for farmers to meet agricultural expenses',
    eligibilityCriteria: [
      'Farmers owning cultivable land',
      'Tenant farmers and sharecroppers',
      'Self-help groups of farmers',
    ],
    benefits: [
      'Credit up to ₹3 lakh at 7% interest',
      'Flexible repayment terms',
      'Insurance coverage included',
      'ATM-cum-debit card facility',
    ],
    applicationProcess: 'Apply at any bank branch with required documents',
    documents: ['Identity proof', 'Address proof', 'Land ownership documents'],
    contactInfo: 'Contact nearest bank branch',
    applicableCrops: ['all'],
    applicableStates: ['all'],
  },
  {
    schemeId: 'PKVY',
    schemeName: 'Paramparagat Krishi Vikas Yojana (PKVY)',
    description: 'Organic farming promotion scheme',
    eligibilityCriteria: [
      'Farmers willing to adopt organic farming',
      'Minimum cluster size of 50 acres',
      'Group of 50 or more farmers',
    ],
    benefits: [
      '₹50,000 per hectare over 3 years',
      'Training and certification support',
      'Market linkage assistance',
    ],
    applicationProcess: 'Apply through State Agriculture Department',
    documents: ['Land records', 'Group formation certificate', 'Bank account details'],
    contactInfo: 'State Agriculture Department',
    applicableCrops: ['all'],
    applicableStates: ['all'],
  },
  {
    schemeId: 'MSP',
    schemeName: 'Minimum Support Price (MSP)',
    description: 'Government procurement at guaranteed minimum prices',
    eligibilityCriteria: [
      'Farmers growing notified crops',
      'Quality standards must be met',
      'Registration with procurement agency',
    ],
    benefits: [
      'Guaranteed minimum price for produce',
      'Protection from price volatility',
      'Direct procurement by government agencies',
    ],
    applicationProcess: 'Register with local procurement center during harvest season',
    documents: ['Land records', 'Crop cultivation certificate', 'Bank account'],
    contactInfo: 'Local Food Corporation of India (FCI) office',
    applicableCrops: ['rice', 'wheat', 'potato', 'cotton', 'sugarcane'],
    applicableStates: ['all'],
  },
];

/**
 * Match schemes to farmer profile
 */
function matchSchemesToFarmer(
  cropTypes: string[],
  location: string,
  state: string,
  landArea: number
): GovernmentScheme[] {
  const matchedSchemes: GovernmentScheme[] = [];

  for (const scheme of GOVERNMENT_SCHEMES) {
    let matchScore = 0;
    const matchReasons: string[] = [];

    // Check crop applicability
    const cropMatch = scheme.applicableCrops.includes('all') || 
      cropTypes.some(crop => scheme.applicableCrops.includes(crop.toLowerCase()));
    
    if (cropMatch) {
      matchScore += 40;
      if (scheme.applicableCrops.includes('all')) {
        matchReasons.push('Applicable to all crops');
      } else {
        const matchingCrops = cropTypes.filter(crop => 
          scheme.applicableCrops.includes(crop.toLowerCase())
        );
        matchReasons.push(`Applicable to your crops: ${matchingCrops.join(', ')}`);
      }
    }

    // Check state applicability
    const stateMatch = scheme.applicableStates.includes('all') || 
      scheme.applicableStates.includes(state.toLowerCase());
    
    if (stateMatch) {
      matchScore += 30;
      matchReasons.push('Available in your state');
    }

    // Additional scoring based on scheme type
    if (scheme.schemeId === 'PM-KISAN') {
      matchScore += 30; // Universal scheme, always relevant
      matchReasons.push('Universal income support for all farmers');
    }

    if (scheme.schemeId === 'PMFBY' && landArea > 2) {
      matchScore += 20; // More relevant for larger farms
      matchReasons.push('Recommended for risk protection on your land size');
    }

    if (scheme.schemeId === 'KCC' && landArea > 1) {
      matchScore += 15; // Credit facility useful for most farmers
      matchReasons.push('Credit facility to support agricultural expenses');
    }

    // Only include schemes with reasonable match
    if (matchScore >= 40) {
      matchedSchemes.push({
        schemeId: scheme.schemeId,
        schemeName: scheme.schemeName,
        description: scheme.description,
        eligibilityCriteria: scheme.eligibilityCriteria,
        benefits: scheme.benefits,
        applicationProcess: scheme.applicationProcess,
        documents: scheme.documents,
        contactInfo: scheme.contactInfo,
        matchScore,
        matchReasons,
      });
    }
  }

  // Sort by match score (highest first)
  matchedSchemes.sort((a, b) => b.matchScore - a.matchScore);

  return matchedSchemes;
}

/**
 * Generate AI-powered application guidance
 */
async function generateApplicationGuidance(
  schemes: GovernmentScheme[],
  farmerProfile: { cropTypes: string[]; location: string; landArea: number },
  language: 'en' | 'bn' | 'hi'
): Promise<string[]> {
  const schemeNames = schemes.map(s => s.schemeName).join(', ');

  const systemPrompt = `You are a government scheme advisory expert helping farmers access agricultural schemes.
Provide clear, step-by-step guidance for applying to government schemes.

Guidelines:
- Provide practical, actionable steps
- Mention common pitfalls to avoid
- Suggest optimal application timing
- Recommend priority order for multiple schemes
- Keep language simple and accessible`;

  const userPrompt = `Provide application guidance for a farmer with the following profile:
Crops: ${farmerProfile.cropTypes.join(', ')}
Location: ${farmerProfile.location}
Land Area: ${farmerProfile.landArea} acres

Matched Schemes: ${schemeNames}

Provide 5-7 key guidance points in JSON format:
{
  "guidance": ["step1", "step2", "step3", "step4", "step5"]
}`;

  const multimodalInput: MultimodalInput = {
    text: userPrompt,
  };

  try {
    console.log('Generating application guidance with Bedrock...');
    const aiResponse = await bedrockClient.invoke(multimodalInput, systemPrompt);

    // Parse AI response
    const jsonMatch = aiResponse.content.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      const parsed = JSON.parse(jsonMatch[0]);
      return parsed.guidance || [];
    }
  } catch (e) {
    console.log('Failed to generate AI guidance, using fallback');
  }

  // Fallback guidance
  return [
    'Start with PM-KISAN as it has universal eligibility and simple application process',
    'Ensure all documents (Aadhaar, land records, bank account) are ready before applying',
    'Apply for crop insurance (PMFBY) before sowing season begins',
    'Consider Kisan Credit Card for working capital needs',
    'Visit nearest Common Service Center (CSC) for application assistance',
    'Keep copies of all submitted documents and application receipts',
    'Follow up regularly on application status through helpline numbers',
  ];
}

/**
 * Calculate total potential benefits
 */
function calculateTotalBenefits(schemes: GovernmentScheme[]): string {
  const benefits: string[] = [];

  for (const scheme of schemes) {
    if (scheme.schemeId === 'PM-KISAN') {
      benefits.push('₹6,000/year from PM-KISAN');
    }
    if (scheme.schemeId === 'PKVY') {
      benefits.push('Up to ₹50,000/hectare from PKVY');
    }
  }

  if (benefits.length === 0) {
    return 'Benefits vary based on scheme utilization';
  }

  return benefits.join(' + ');
}

/**
 * Main Lambda handler
 */
export async function handler(event: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> {
  console.log('Received government scheme request');

  try {
    // Parse request
    const request: GovernmentSchemeRequest = JSON.parse(event.body || '{}');

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

    const cropTypes = request.cropTypes || userProfile.cropTypes;
    const language = request.language || userProfile.language || 'en';

    // Match schemes to farmer profile
    console.log(`Matching schemes for farmer ${request.farmerId}`);
    const matchedSchemes = matchSchemesToFarmer(
      cropTypes,
      userProfile.location.district,
      userProfile.location.state,
      userProfile.landArea
    );

    // Generate application guidance
    const applicationGuidance = await generateApplicationGuidance(
      matchedSchemes,
      {
        cropTypes,
        location: `${userProfile.location.district}, ${userProfile.location.state}`,
        landArea: userProfile.landArea,
      },
      language as 'en' | 'bn' | 'hi'
    );

    // Calculate total potential benefits
    const totalBenefits = calculateTotalBenefits(matchedSchemes);

    // Build response
    const response: SchemeRecommendation = {
      farmerId: request.farmerId,
      location: `${userProfile.location.district}, ${userProfile.location.state}`,
      cropTypes,
      schemes: matchedSchemes,
      totalPotentialBenefits: totalBenefits,
      applicationGuidance,
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
    console.error('Error fetching government schemes:', error);

    return {
      statusCode: 500,
      body: JSON.stringify({
        error: 'Internal server error',
        message: error instanceof Error ? error.message : 'Unknown error occurred',
      }),
    };
  }
}
