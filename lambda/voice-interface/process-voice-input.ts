/**
 * Lambda Function: Process Voice Input
 * 
 * This function handles voice input processing including:
 * - Speech-to-text using Amazon Transcribe
 * - Language detection for Bengali and Hindi
 * - Intent recognition and entity extraction
 * - Storage of audio files in S3
 * 
 * Requirements: 3.1, 3.3
 */

import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';
import { 
  TranscribeClient, 
  StartTranscriptionJobCommand,
  GetTranscriptionJobCommand,
  TranscriptionJob,
  LanguageCode
} from '@aws-sdk/client-transcribe';
import { S3Client, PutObjectCommand } from '@aws-sdk/client-s3';
import { BedrockClient, MultimodalInput } from '../../lib/services/bedrock/bedrock-client';
import { v4 as uuidv4 } from 'uuid';

// Environment variables
const TABLE_NAME = process.env.TABLE_NAME!;
const AUDIO_BUCKET = process.env.AUDIO_BUCKET!;
const AWS_REGION = process.env.AWS_REGION || 'us-east-1';

// Initialize clients
const s3Client = new S3Client({ region: AWS_REGION });
const transcribeClient = new TranscribeClient({ region: AWS_REGION });
const bedrockClient = new BedrockClient({ region: AWS_REGION });

interface ProcessVoiceInputRequest {
  farmerId: string;
  audioData: string; // Base64 encoded audio
  audioFormat: 'mp3' | 'wav' | 'flac' | 'ogg';
  language?: 'bn' | 'hi' | 'en';
  sessionId?: string;
}

interface VoiceProcessingResult {
  transcription: string;
  detectedLanguage: string;
  intent: IntentClassification;
  entities: EntityExtraction[];
  confidence: number;
  requiresClarification: boolean;
  sessionId: string;
  audioUrl: string;
}

interface IntentClassification {
  intentName: string;
  confidence: number;
  category: 'crop_diagnosis' | 'market_query' | 'price_alert' | 'grievance' | 'profile_update' | 'general_query';
}

interface EntityExtraction {
  entityType: 'crop_type' | 'location' | 'price' | 'date' | 'disease' | 'other';
  value: string;
  confidence: number;
}

/**
 * Upload audio file to S3
 */
async function uploadAudioToS3(
  audioBuffer: Buffer,
  farmerId: string,
  audioFormat: string
): Promise<string> {
  const audioKey = `voice-recordings/${farmerId}/${Date.now()}-${uuidv4()}.${audioFormat}`;

  await s3Client.send(
    new PutObjectCommand({
      Bucket: AUDIO_BUCKET,
      Key: audioKey,
      Body: audioBuffer,
      ContentType: `audio/${audioFormat}`,
      Metadata: {
        farmerId,
        uploadedAt: new Date().toISOString(),
      },
    })
  );

  return `s3://${AUDIO_BUCKET}/${audioKey}`;
}

/**
 * Detect language from audio using Amazon Transcribe
 */
async function detectLanguage(audioUrl: string): Promise<string> {
  const jobName = `lang-detect-${uuidv4()}`;

  // Start transcription job with language identification
  await transcribeClient.send(
    new StartTranscriptionJobCommand({
      TranscriptionJobName: jobName,
      Media: { MediaFileUri: audioUrl },
      IdentifyLanguage: true,
      LanguageOptions: ['bn-IN', 'hi-IN', 'en-IN'],
    })
  );

  // Poll for completion
  let job: TranscriptionJob | undefined;
  for (let i = 0; i < 30; i++) {
    const response = await transcribeClient.send(
      new GetTranscriptionJobCommand({ TranscriptionJobName: jobName })
    );
    
    job = response.TranscriptionJob;
    if (job?.TranscriptionJobStatus === 'COMPLETED') {
      break;
    } else if (job?.TranscriptionJobStatus === 'FAILED') {
      throw new Error(`Language detection failed: ${job.FailureReason}`);
    }
    
    await new Promise(resolve => setTimeout(resolve, 2000));
  }

  if (!job || job.TranscriptionJobStatus !== 'COMPLETED') {
    throw new Error('Language detection timed out');
  }

  // Extract detected language
  const detectedLanguage = job.IdentifiedLanguageScore?.[0]?.LanguageCode || 'en-IN';
  return detectedLanguage.split('-')[0]; // Return 'bn', 'hi', or 'en'
}

/**
 * Transcribe audio using Amazon Transcribe
 */
async function transcribeAudio(
  audioUrl: string,
  languageCode: LanguageCode
): Promise<string> {
  const jobName = `transcribe-${uuidv4()}`;

  // Start transcription job
  await transcribeClient.send(
    new StartTranscriptionJobCommand({
      TranscriptionJobName: jobName,
      Media: { MediaFileUri: audioUrl },
      LanguageCode: languageCode,
      MediaFormat: audioUrl.endsWith('.mp3') ? 'mp3' : 
                   audioUrl.endsWith('.wav') ? 'wav' :
                   audioUrl.endsWith('.flac') ? 'flac' : 'ogg',
    })
  );

  // Poll for completion
  let job: TranscriptionJob | undefined;
  for (let i = 0; i < 30; i++) {
    const response = await transcribeClient.send(
      new GetTranscriptionJobCommand({ TranscriptionJobName: jobName })
    );
    
    job = response.TranscriptionJob;
    if (job?.TranscriptionJobStatus === 'COMPLETED') {
      break;
    } else if (job?.TranscriptionJobStatus === 'FAILED') {
      throw new Error(`Transcription failed: ${job.FailureReason}`);
    }
    
    await new Promise(resolve => setTimeout(resolve, 2000));
  }

  if (!job || job.TranscriptionJobStatus !== 'COMPLETED') {
    throw new Error('Transcription timed out');
  }

  // Fetch transcription result
  const transcriptUri = job.Transcript?.TranscriptFileUri;
  if (!transcriptUri) {
    throw new Error('No transcript URI found');
  }

  const response = await fetch(transcriptUri);
  const transcriptData = await response.json();
  
  return transcriptData.results?.transcripts?.[0]?.transcript || '';
}

/**
 * Recognize intent and extract entities using Bedrock
 */
async function recognizeIntentAndEntities(
  transcription: string,
  language: string
): Promise<{
  intent: IntentClassification;
  entities: EntityExtraction[];
  confidence: number;
  requiresClarification: boolean;
}> {
  const systemPrompt = `You are an intent recognition system for an agricultural AI assistant.
Analyze the farmer's voice input and identify:
1. Primary intent (crop_diagnosis, market_query, price_alert, grievance, profile_update, general_query)
2. Entities (crop types, locations, prices, dates, diseases)
3. Confidence level
4. Whether clarification is needed

Respond in JSON format:
{
  "intent": {
    "intentName": "specific action",
    "confidence": 0.0-1.0,
    "category": "one of the categories"
  },
  "entities": [
    {
      "entityType": "crop_type|location|price|date|disease|other",
      "value": "extracted value",
      "confidence": 0.0-1.0
    }
  ],
  "confidence": 0.0-1.0,
  "requiresClarification": true/false,
  "clarificationReason": "why clarification is needed (if applicable)"
}`;

  const userPrompt = `Language: ${language}
Transcription: "${transcription}"

Analyze this farmer's voice input and extract intent and entities.`;

  const multimodalInput: MultimodalInput = {
    text: userPrompt,
  };

  console.log('Recognizing intent with Bedrock...');
  const aiResponse = await bedrockClient.invoke(multimodalInput, systemPrompt);

  // Parse AI response
  try {
    const jsonMatch = aiResponse.content.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      const parsed = JSON.parse(jsonMatch[0]);
      return {
        intent: parsed.intent || {
          intentName: 'general_query',
          confidence: 0.5,
          category: 'general_query',
        },
        entities: parsed.entities || [],
        confidence: parsed.confidence || 0.5,
        requiresClarification: parsed.requiresClarification || false,
      };
    }
  } catch (e) {
    console.log('Failed to parse intent recognition response');
  }

  // Fallback
  return {
    intent: {
      intentName: 'general_query',
      confidence: 0.5,
      category: 'general_query',
    },
    entities: [],
    confidence: 0.5,
    requiresClarification: true,
  };
}

/**
 * Main Lambda handler
 */
export async function handler(event: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> {
  console.log('Received voice input processing request');

  try {
    // Parse request body
    const request: ProcessVoiceInputRequest = JSON.parse(event.body || '{}');

    // Validate required fields
    if (!request.farmerId || !request.audioData || !request.audioFormat) {
      return {
        statusCode: 400,
        body: JSON.stringify({
          error: 'Missing required fields: farmerId, audioData, audioFormat',
        }),
      };
    }

    // Decode base64 audio
    const audioBuffer = Buffer.from(request.audioData, 'base64');

    // Upload audio to S3
    console.log('Uploading audio to S3...');
    const audioUrl = await uploadAudioToS3(audioBuffer, request.farmerId, request.audioFormat);
    console.log(`Audio uploaded: ${audioUrl}`);

    // Detect language if not provided
    let language = request.language;
    if (!language) {
      console.log('Detecting language...');
      language = await detectLanguage(audioUrl) as 'bn' | 'hi' | 'en';
      console.log(`Detected language: ${language}`);
    }

    // Map language to Transcribe language code
    const languageCodeMap: Record<string, LanguageCode> = {
      'bn': 'bn-IN',
      'hi': 'hi-IN',
      'en': 'en-IN',
    };
    const languageCode = languageCodeMap[language] || 'en-IN';

    // Transcribe audio
    console.log('Transcribing audio...');
    const transcription = await transcribeAudio(audioUrl, languageCode);
    console.log(`Transcription: ${transcription}`);

    // Recognize intent and extract entities
    console.log('Recognizing intent and entities...');
    const nluResult = await recognizeIntentAndEntities(transcription, language);

    // Generate session ID if not provided
    const sessionId = request.sessionId || uuidv4();

    // Prepare response
    const response: VoiceProcessingResult = {
      transcription,
      detectedLanguage: language,
      intent: nluResult.intent,
      entities: nluResult.entities,
      confidence: nluResult.confidence,
      requiresClarification: nluResult.requiresClarification,
      sessionId,
      audioUrl,
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
    console.error('Error processing voice input:', error);

    return {
      statusCode: 500,
      body: JSON.stringify({
        error: 'Internal server error',
        message: error instanceof Error ? error.message : 'Unknown error occurred',
      }),
    };
  }
}
