/**
 * Lambda Function: Handle Offline Voice
 * 
 * This function handles voice processing in offline mode, caching basic
 * voice models locally and queuing commands for later processing.
 * 
 * Requirements: 3.5, 8.1
 */

import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';
import { S3Client, PutObjectCommand } from '@aws-sdk/client-s3';
import { OfflineVoiceProcessor, OfflineProcessingResult } from './offline-voice-processor';
import { v4 as uuidv4 } from 'uuid';

// Environment variables
const AUDIO_BUCKET = process.env.AUDIO_BUCKET!;
const AWS_REGION = process.env.AWS_REGION || 'us-east-1';

// Initialize clients
const s3Client = new S3Client({ region: AWS_REGION });
const offlineProcessor = new OfflineVoiceProcessor();

interface HandleOfflineVoiceRequest {
  farmerId: string;
  audioData: string; // Base64 encoded audio
  audioFormat: 'mp3' | 'wav' | 'flac' | 'ogg';
  language?: 'bn' | 'hi' | 'en';
}

interface HandleOfflineVoiceResponse {
  result: OfflineProcessingResult;
  voiceFeedback: string;
  queueStatus: {
    totalQueued: number;
    estimatedSyncTime?: Date;
  };
}

/**
 * Upload audio file to S3 for offline processing
 */
async function uploadAudioToS3(
  audioBuffer: Buffer,
  farmerId: string,
  audioFormat: string
): Promise<string> {
  const audioKey = `offline-voice/${farmerId}/${Date.now()}-${uuidv4()}.${audioFormat}`;

  await s3Client.send(
    new PutObjectCommand({
      Bucket: AUDIO_BUCKET,
      Key: audioKey,
      Body: audioBuffer,
      ContentType: `audio/${audioFormat}`,
      Metadata: {
        farmerId,
        uploadedAt: new Date().toISOString(),
        mode: 'offline',
      },
    })
  );

  return `s3://${AUDIO_BUCKET}/${audioKey}`;
}

/**
 * Main Lambda handler
 */
export async function handler(event: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> {
  console.log('Received offline voice processing request');

  try {
    // Parse request body
    const request: HandleOfflineVoiceRequest = JSON.parse(event.body || '{}');

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

    // Process voice in offline mode
    console.log('Processing voice in offline mode...');
    const result = await offlineProcessor.processOfflineVoice(
      audioBuffer,
      request.farmerId,
      audioUrl
    );

    // Get voice feedback about offline status
    const language = request.language || 'en';
    const voiceFeedback = offlineProcessor.getOfflineStatusFeedback(language);

    // Get queued commands count
    const queuedCommands = await offlineProcessor.getQueuedCommands(request.farmerId);

    // Prepare response
    const response: HandleOfflineVoiceResponse = {
      result,
      voiceFeedback,
      queueStatus: {
        totalQueued: queuedCommands.length,
        estimatedSyncTime: result.estimatedSyncTime,
      },
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
    console.error('Error handling offline voice:', error);

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
 * Lambda handler for synchronizing queued commands
 */
export async function syncHandler(event: any): Promise<any> {
  console.log('Synchronizing offline voice commands');

  try {
    const farmerId = event.farmerId;

    if (!farmerId) {
      throw new Error('farmerId is required');
    }

    // Synchronize queued commands
    const syncResult = await offlineProcessor.synchronizeQueuedCommands(farmerId);

    console.log(`Sync complete: ${JSON.stringify(syncResult)}`);

    return {
      statusCode: 200,
      body: JSON.stringify({
        message: 'Synchronization complete',
        result: syncResult,
      }),
    };
  } catch (error) {
    console.error('Error synchronizing commands:', error);

    return {
      statusCode: 500,
      body: JSON.stringify({
        error: 'Synchronization failed',
        message: error instanceof Error ? error.message : 'Unknown error occurred',
      }),
    };
  }
}
