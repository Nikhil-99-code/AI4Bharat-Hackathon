/**
 * Lambda Function: Generate Voice Response
 * 
 * This function converts text responses to speech using Amazon Polly
 * with support for Bengali, Hindi, and English voices.
 * 
 * Requirements: 3.3
 */

import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';
import { 
  PollyClient, 
  SynthesizeSpeechCommand,
  VoiceId,
  Engine,
  OutputFormat
} from '@aws-sdk/client-polly';
import { S3Client, PutObjectCommand } from '@aws-sdk/client-s3';
import { v4 as uuidv4 } from 'uuid';

// Environment variables
const AUDIO_BUCKET = process.env.AUDIO_BUCKET!;
const AWS_REGION = process.env.AWS_REGION || 'us-east-1';

// Initialize clients
const pollyClient = new PollyClient({ region: AWS_REGION });
const s3Client = new S3Client({ region: AWS_REGION });

interface GenerateVoiceResponseRequest {
  text: string;
  language: 'bn' | 'hi' | 'en';
  voiceId?: string;
  farmerId?: string;
  outputFormat?: 'mp3' | 'ogg_vorbis' | 'pcm';
}

interface VoiceResponseResult {
  audioUrl: string;
  audioData?: string; // Base64 encoded audio (optional)
  duration?: number;
  language: string;
  voiceId: string;
}

/**
 * Get appropriate voice ID for language
 */
function getVoiceIdForLanguage(language: string, customVoiceId?: string): VoiceId {
  if (customVoiceId) {
    return customVoiceId as VoiceId;
  }

  // Default voices for each language
  const voiceMap: Record<string, VoiceId> = {
    'bn': 'Aditi', // Bengali (Indian)
    'hi': 'Aditi', // Hindi (Indian) - Aditi supports both Hindi and Bengali
    'en': 'Kajal', // English (Indian)
  };

  return voiceMap[language] || 'Kajal';
}

/**
 * Synthesize speech using Amazon Polly
 */
async function synthesizeSpeech(
  text: string,
  voiceId: VoiceId,
  outputFormat: OutputFormat = 'mp3'
): Promise<Buffer> {
  console.log(`Synthesizing speech with voice: ${voiceId}, format: ${outputFormat}`);

  const command = new SynthesizeSpeechCommand({
    Text: text,
    VoiceId: voiceId,
    OutputFormat: outputFormat,
    Engine: 'neural', // Use neural engine for better quality
    LanguageCode: voiceId === 'Aditi' ? 'hi-IN' : 'en-IN',
  });

  const response = await pollyClient.send(command);

  if (!response.AudioStream) {
    throw new Error('No audio stream received from Polly');
  }

  // Convert stream to buffer
  const chunks: Uint8Array[] = [];
  for await (const chunk of response.AudioStream) {
    chunks.push(chunk);
  }

  return Buffer.concat(chunks);
}

/**
 * Upload audio to S3
 */
async function uploadAudioToS3(
  audioBuffer: Buffer,
  farmerId: string,
  format: string
): Promise<string> {
  const audioKey = `voice-responses/${farmerId}/${Date.now()}-${uuidv4()}.${format}`;

  await s3Client.send(
    new PutObjectCommand({
      Bucket: AUDIO_BUCKET,
      Key: audioKey,
      Body: audioBuffer,
      ContentType: `audio/${format}`,
      Metadata: {
        farmerId,
        generatedAt: new Date().toISOString(),
      },
    })
  );

  return `s3://${AUDIO_BUCKET}/${audioKey}`;
}

/**
 * Estimate audio duration (rough estimate based on text length)
 */
function estimateDuration(text: string): number {
  // Average speaking rate: ~150 words per minute
  const words = text.split(/\s+/).length;
  const minutes = words / 150;
  return Math.ceil(minutes * 60); // Return seconds
}

/**
 * Main Lambda handler
 */
export async function handler(event: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> {
  console.log('Received voice response generation request');

  try {
    // Parse request body
    const request: GenerateVoiceResponseRequest = JSON.parse(event.body || '{}');

    // Validate required fields
    if (!request.text || !request.language) {
      return {
        statusCode: 400,
        body: JSON.stringify({
          error: 'Missing required fields: text, language',
        }),
      };
    }

    // Validate text length (Polly has limits)
    if (request.text.length > 3000) {
      return {
        statusCode: 400,
        body: JSON.stringify({
          error: 'Text too long. Maximum 3000 characters allowed.',
        }),
      };
    }

    // Get voice ID for language
    const voiceId = getVoiceIdForLanguage(request.language, request.voiceId);
    console.log(`Using voice: ${voiceId} for language: ${request.language}`);

    // Determine output format
    const outputFormat = request.outputFormat || 'mp3';

    // Synthesize speech
    console.log('Synthesizing speech...');
    const audioBuffer = await synthesizeSpeech(
      request.text,
      voiceId,
      outputFormat as OutputFormat
    );
    console.log(`Audio synthesized: ${audioBuffer.length} bytes`);

    // Upload to S3 if farmerId is provided
    let audioUrl = '';
    if (request.farmerId) {
      console.log('Uploading audio to S3...');
      audioUrl = await uploadAudioToS3(audioBuffer, request.farmerId, outputFormat);
      console.log(`Audio uploaded: ${audioUrl}`);
    }

    // Estimate duration
    const duration = estimateDuration(request.text);

    // Prepare response
    const response: VoiceResponseResult = {
      audioUrl,
      audioData: audioBuffer.toString('base64'), // Include base64 audio in response
      duration,
      language: request.language,
      voiceId,
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
    console.error('Error generating voice response:', error);

    return {
      statusCode: 500,
      body: JSON.stringify({
        error: 'Internal server error',
        message: error instanceof Error ? error.message : 'Unknown error occurred',
      }),
    };
  }
}
