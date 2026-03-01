/**
 * Lambda Function: Analyze Crop Image
 * 
 * This function handles crop image analysis using Amazon Bedrock with Claude 4.5 Sonnet.
 * It performs image preprocessing, validation, disease diagnosis, and stores results in DynamoDB.
 * 
 * Requirements: 1.1, 1.4, 1.5
 */

import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';
import { S3Client, PutObjectCommand } from '@aws-sdk/client-s3';
import { BedrockClient, MultimodalInput } from '../../lib/services/bedrock/bedrock-client';
import { PromptTemplateManager, Language } from '../../lib/services/bedrock/prompt-templates';
import { CropDiagnosisRepository } from '../../lib/repositories/crop-diagnosis-repository';
import { TreatmentStep } from '../../lib/types/domain-entities';
import { v4 as uuidv4 } from 'uuid';

// Environment variables
const TABLE_NAME = process.env.TABLE_NAME!;
const IMAGE_BUCKET = process.env.IMAGE_BUCKET!;
const AWS_REGION = process.env.AWS_REGION || 'us-east-1';

// Initialize clients
const s3Client = new S3Client({ region: AWS_REGION });
const bedrockClient = new BedrockClient({ region: AWS_REGION });
const promptManager = new PromptTemplateManager();
const diagnosisRepository = new CropDiagnosisRepository({
  tableName: TABLE_NAME,
  region: AWS_REGION,
});

interface AnalyzeCropImageRequest {
  farmerId: string;
  imageData: string; // Base64 encoded image
  imageFormat: 'png' | 'jpeg' | 'gif' | 'webp';
  cropType?: string;
  location?: string;
  language?: 'en' | 'bn' | 'hi';
  additionalContext?: string;
}

interface DiagnosisResponse {
  diagnosisId: string;
  diseaseIdentified: boolean;
  diseaseName?: string;
  confidence: number;
  treatmentRecommendations: TreatmentStep[];
  preventiveMeasures: string[];
  followUpRequired: boolean;
  severityLevel?: 'low' | 'medium' | 'high' | 'critical';
  imageUrl: string;
  message: string;
}

/**
 * Validate image quality
 */
function validateImageQuality(imageBuffer: Buffer): { valid: boolean; message?: string } {
  // Check file size (max 10MB)
  const maxSize = 10 * 1024 * 1024;
  if (imageBuffer.length > maxSize) {
    return {
      valid: false,
      message: 'Image size exceeds 10MB. Please upload a smaller image.',
    };
  }

  // Check minimum size (at least 10KB)
  const minSize = 10 * 1024;
  if (imageBuffer.length < minSize) {
    return {
      valid: false,
      message: 'Image is too small. Please upload a clearer, higher resolution image.',
    };
  }

  return { valid: true };
}

/**
 * Upload image to S3
 */
async function uploadImageToS3(
  imageBuffer: Buffer,
  farmerId: string,
  imageFormat: string
): Promise<string> {
  const imageKey = `crop-images/${farmerId}/${Date.now()}-${uuidv4()}.${imageFormat}`;

  await s3Client.send(
    new PutObjectCommand({
      Bucket: IMAGE_BUCKET,
      Key: imageKey,
      Body: imageBuffer,
      ContentType: `image/${imageFormat}`,
      Metadata: {
        farmerId,
        uploadedAt: new Date().toISOString(),
      },
    })
  );

  return `s3://${IMAGE_BUCKET}/${imageKey}`;
}

/**
 * Parse AI response to extract diagnosis information
 */
function parseDiagnosisResponse(aiResponse: string): {
  diseaseIdentified: boolean;
  diseaseName?: string;
  confidence: number;
  treatmentRecommendations: TreatmentStep[];
  preventiveMeasures: string[];
  followUpRequired: boolean;
  severityLevel?: 'low' | 'medium' | 'high' | 'critical';
} {
  // Try to parse structured JSON response
  try {
    // Look for JSON in the response
    const jsonMatch = aiResponse.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      const parsed = JSON.parse(jsonMatch[0]);
      return {
        diseaseIdentified: parsed.diseaseIdentified || false,
        diseaseName: parsed.diseaseName,
        confidence: parsed.confidence || 0.5,
        treatmentRecommendations: parsed.treatmentRecommendations || [],
        preventiveMeasures: parsed.preventiveMeasures || [],
        followUpRequired: parsed.followUpRequired || false,
        severityLevel: parsed.severityLevel,
      };
    }
  } catch (e) {
    console.log('Failed to parse JSON response, using text parsing');
  }

  // Fallback: Parse text response
  const diseaseIdentified = !aiResponse.toLowerCase().includes('no disease') &&
    !aiResponse.toLowerCase().includes('healthy');
  
  // Extract disease name
  const diseaseMatch = aiResponse.match(/disease[:\s]+([^\n.]+)/i);
  const diseaseName = diseaseMatch ? diseaseMatch[1].trim() : undefined;

  // Extract confidence
  const confidenceMatch = aiResponse.match(/confidence[:\s]+(\d+)%/i);
  const confidence = confidenceMatch ? parseInt(confidenceMatch[1]) / 100 : 0.7;

  // Extract treatment recommendations
  const treatmentRecommendations: TreatmentStep[] = [];
  const treatmentSection = aiResponse.match(/treatment[:\s]+(.+?)(?=preventive|$)/is);
  if (treatmentSection) {
    const steps = treatmentSection[1].split(/\d+\.|•|-/).filter(s => s.trim());
    steps.forEach((step, index) => {
      if (step.trim()) {
        treatmentRecommendations.push({
          stepNumber: index + 1,
          description: step.trim(),
        });
      }
    });
  }

  // Extract preventive measures
  const preventiveMeasures: string[] = [];
  const preventiveSection = aiResponse.match(/preventive[:\s]+(.+?)$/is);
  if (preventiveSection) {
    const measures = preventiveSection[1].split(/\d+\.|•|-/).filter(s => s.trim());
    measures.forEach(measure => {
      if (measure.trim()) {
        preventiveMeasures.push(measure.trim());
      }
    });
  }

  // Determine severity
  let severityLevel: 'low' | 'medium' | 'high' | 'critical' | undefined;
  if (diseaseIdentified) {
    if (aiResponse.toLowerCase().includes('critical') || aiResponse.toLowerCase().includes('severe')) {
      severityLevel = 'critical';
    } else if (aiResponse.toLowerCase().includes('high') || aiResponse.toLowerCase().includes('urgent')) {
      severityLevel = 'high';
    } else if (aiResponse.toLowerCase().includes('moderate') || aiResponse.toLowerCase().includes('medium')) {
      severityLevel = 'medium';
    } else {
      severityLevel = 'low';
    }
  }

  return {
    diseaseIdentified,
    diseaseName,
    confidence,
    treatmentRecommendations,
    preventiveMeasures,
    followUpRequired: severityLevel === 'high' || severityLevel === 'critical',
    severityLevel,
  };
}

/**
 * Main Lambda handler
 */
export async function handler(event: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> {
  console.log('Received crop image analysis request');

  try {
    // Parse request body
    const request: AnalyzeCropImageRequest = JSON.parse(event.body || '{}');

    // Validate required fields
    if (!request.farmerId || !request.imageData || !request.imageFormat) {
      return {
        statusCode: 400,
        body: JSON.stringify({
          error: 'Missing required fields: farmerId, imageData, imageFormat',
        }),
      };
    }

    // Decode base64 image
    const imageBuffer = Buffer.from(request.imageData, 'base64');

    // Validate image quality
    const qualityCheck = validateImageQuality(imageBuffer);
    if (!qualityCheck.valid) {
      return {
        statusCode: 400,
        body: JSON.stringify({
          error: 'Image quality validation failed',
          message: qualityCheck.message,
        }),
      };
    }

    // Upload image to S3
    console.log('Uploading image to S3...');
    const imageUrl = await uploadImageToS3(imageBuffer, request.farmerId, request.imageFormat);
    console.log(`Image uploaded: ${imageUrl}`);

    // Prepare multimodal input for Bedrock
    const language = request.language || 'en';
    const promptVariables = {
      cropType: request.cropType || 'unknown',
      location: request.location || 'not specified',
      context: request.additionalContext || 'none',
    };

    const { system, user } = promptManager.getRenderedPrompt(
      'crop_diagnosis',
      promptVariables,
      language
    );

    // Add instruction for structured output
    const enhancedUser = `${user}

Please provide your response in the following JSON format:
{
  "diseaseIdentified": true/false,
  "diseaseName": "name of disease if identified",
  "confidence": 0.0-1.0,
  "treatmentRecommendations": [
    {
      "stepNumber": 1,
      "description": "treatment step description",
      "materials": ["material1", "material2"],
      "timing": "when to apply",
      "precautions": ["precaution1"]
    }
  ],
  "preventiveMeasures": ["measure1", "measure2"],
  "followUpRequired": true/false,
  "severityLevel": "low/medium/high/critical"
}`;

    const multimodalInput: MultimodalInput = {
      text: enhancedUser,
      images: [
        {
          format: request.imageFormat,
          source: {
            bytes: imageBuffer,
          },
        },
      ],
    };

    // Call Bedrock for analysis
    console.log('Analyzing image with Bedrock...');
    const aiResponse = await bedrockClient.invoke(multimodalInput, system);
    console.log('Bedrock analysis complete');

    // Parse diagnosis from AI response
    const diagnosis = parseDiagnosisResponse(aiResponse.content);

    // Store diagnosis in DynamoDB
    console.log('Storing diagnosis in DynamoDB...');
    const diagnosisRecord = await diagnosisRepository.createDiagnosis({
      farmerId: request.farmerId,
      imageUrl,
      diseaseIdentified: diagnosis.diseaseIdentified ? diagnosis.diseaseName || 'Unknown disease' : null,
      diseaseName: diagnosis.diseaseName,
      confidence: diagnosis.confidence,
      treatmentRecommendations: diagnosis.treatmentRecommendations,
      preventiveMeasures: diagnosis.preventiveMeasures,
      followUpRequired: diagnosis.followUpRequired,
      severityLevel: diagnosis.severityLevel,
    });

    console.log(`Diagnosis stored with ID: ${diagnosisRecord.diagnosisId}`);

    // Prepare response
    const response: DiagnosisResponse = {
      diagnosisId: diagnosisRecord.diagnosisId,
      diseaseIdentified: diagnosis.diseaseIdentified,
      diseaseName: diagnosis.diseaseName,
      confidence: diagnosis.confidence,
      treatmentRecommendations: diagnosis.treatmentRecommendations,
      preventiveMeasures: diagnosis.preventiveMeasures,
      followUpRequired: diagnosis.followUpRequired,
      severityLevel: diagnosis.severityLevel,
      imageUrl,
      message: diagnosis.diseaseIdentified
        ? `Disease identified: ${diagnosis.diseaseName}. Please follow the treatment recommendations.`
        : 'No disease detected. Your crop appears healthy. Continue with preventive care.',
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
    console.error('Error analyzing crop image:', error);

    return {
      statusCode: 500,
      body: JSON.stringify({
        error: 'Internal server error',
        message: error instanceof Error ? error.message : 'Unknown error occurred',
      }),
    };
  }
}
