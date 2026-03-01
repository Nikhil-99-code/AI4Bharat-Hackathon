/**
 * Offline Voice Processor
 * 
 * This service handles voice processing when the system is offline or
 * has limited connectivity. It caches basic voice models locally and
 * queues commands for later processing.
 * 
 * Requirements: 3.5, 8.1
 */

import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient, PutCommand, QueryCommand } from '@aws-sdk/lib-dynamodb';

// Environment variables
const TABLE_NAME = process.env.TABLE_NAME!;
const AWS_REGION = process.env.AWS_REGION || 'us-east-1';

// Initialize DynamoDB client
const dynamoClient = new DynamoDBClient({ region: AWS_REGION });
const docClient = DynamoDBDocumentClient.from(dynamoClient);

export interface OfflineVoiceCommand {
  commandId: string;
  farmerId: string;
  audioUrl: string;
  timestamp: Date;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  localTranscription?: string;
  detectedIntent?: string;
  retryCount: number;
}

export interface OfflineProcessingResult {
  commandId: string;
  status: 'queued' | 'processed_locally' | 'requires_sync';
  localResponse?: string;
  queuedForSync: boolean;
  estimatedSyncTime?: Date;
}

/**
 * Offline Voice Processor Service
 */
export class OfflineVoiceProcessor {
  private cachedModels: Map<string, any>;
  private offlineCapabilities: Set<string>;

  constructor() {
    this.cachedModels = new Map();
    this.offlineCapabilities = new Set([
      'basic_greeting',
      'status_check',
      'offline_notification',
      'simple_query',
    ]);
    
    this.initializeCachedModels();
  }

  /**
   * Initialize cached voice models for offline use
   */
  private initializeCachedModels(): void {
    // Cache basic voice models (simplified patterns)
    this.cachedModels.set('greetings', {
      patterns: ['hello', 'hi', 'namaste', 'namaskar', 'হ্যালো', 'নমস্কার', 'नमस्ते'],
      response: 'greeting_response',
    });

    this.cachedModels.set('status', {
      patterns: ['status', 'how are you', 'working', 'অবস্থা', 'स्थिति'],
      response: 'status_response',
    });

    this.cachedModels.set('help', {
      patterns: ['help', 'support', 'assist', 'সাহায্য', 'मदद'],
      response: 'help_response',
    });
  }

  /**
   * Process voice command in offline mode
   */
  async processOfflineVoice(
    audioData: Buffer,
    farmerId: string,
    audioUrl: string
  ): Promise<OfflineProcessingResult> {
    console.log('Processing voice in offline mode');

    // Generate command ID
    const commandId = `offline-${Date.now()}-${farmerId}`;

    // Try basic local transcription (simplified pattern matching)
    const localTranscription = await this.basicLocalTranscription(audioData);

    // Check if command can be handled offline
    const canHandleOffline = this.canHandleOffline(localTranscription);

    if (canHandleOffline) {
      // Process locally
      const localResponse = this.generateLocalResponse(localTranscription);

      // Still queue for verification when online
      await this.queueForSync(commandId, farmerId, audioUrl, localTranscription, 'processed_locally');

      return {
        commandId,
        status: 'processed_locally',
        localResponse,
        queuedForSync: true,
        estimatedSyncTime: new Date(Date.now() + 3600000), // 1 hour
      };
    } else {
      // Queue for processing when online
      await this.queueForSync(commandId, farmerId, audioUrl, localTranscription, 'queued');

      return {
        commandId,
        status: 'requires_sync',
        localResponse: this.getOfflineNotification(localTranscription),
        queuedForSync: true,
        estimatedSyncTime: new Date(Date.now() + 3600000),
      };
    }
  }

  /**
   * Basic local transcription using pattern matching
   */
  private async basicLocalTranscription(audioData: Buffer): Promise<string> {
    // In a real implementation, this would use a lightweight local model
    // For now, we'll return a placeholder
    console.log('Performing basic local transcription');
    
    // Simulate basic pattern detection
    // In production, this would use a cached lightweight model
    return 'unknown_command';
  }

  /**
   * Check if command can be handled offline
   */
  private canHandleOffline(transcription: string): boolean {
    const lowerTranscription = transcription.toLowerCase();

    for (const [_, model] of this.cachedModels) {
      if (model.patterns.some((pattern: string) => lowerTranscription.includes(pattern.toLowerCase()))) {
        return true;
      }
    }

    return false;
  }

  /**
   * Generate local response for offline commands
   */
  private generateLocalResponse(transcription: string): string {
    const lowerTranscription = transcription.toLowerCase();

    for (const [key, model] of this.cachedModels) {
      if (model.patterns.some((pattern: string) => lowerTranscription.includes(pattern.toLowerCase()))) {
        return this.getResponseTemplate(model.response);
      }
    }

    return this.getOfflineNotification(transcription);
  }

  /**
   * Get response template
   */
  private getResponseTemplate(responseType: string): string {
    const templates: Record<string, Record<string, string>> = {
      'greeting_response': {
        'en': 'Hello! I am currently in offline mode. I can help with basic queries. For advanced features, please try again when you have internet connectivity.',
        'bn': 'হ্যালো! আমি বর্তমানে অফলাইন মোডে আছি। আমি মৌলিক প্রশ্নে সাহায্য করতে পারি। উন্নত বৈশিষ্ট্যের জন্য, ইন্টারনেট সংযোগ থাকলে আবার চেষ্টা করুন।',
        'hi': 'नमस्ते! मैं वर्तमान में ऑफ़लाइन मोड में हूं। मैं बुनियादी प्रश्नों में मदद कर सकता हूं। उन्नत सुविधाओं के लिए, कृपया इंटरनेट कनेक्टिविटी होने पर पुनः प्रयास करें।',
      },
      'status_response': {
        'en': 'System is currently in offline mode. Basic functionality is available. Your requests will be processed when connectivity is restored.',
        'bn': 'সিস্টেম বর্তমানে অফলাইন মোডে আছে। মৌলিক কার্যকারিতা উপলব্ধ। সংযোগ পুনরুদ্ধার হলে আপনার অনুরোধ প্রক্রিয়া করা হবে।',
        'hi': 'सिस्टम वर्तमान में ऑफ़लाइन मोड में है। बुनियादी कार्यक्षमता उपलब्ध है। कनेक्टिविटी बहाल होने पर आपके अनुरोधों को संसाधित किया जाएगा।',
      },
      'help_response': {
        'en': 'In offline mode, I can provide basic information and queue your requests. For crop diagnosis, market data, and alerts, please connect to the internet.',
        'bn': 'অফলাইন মোডে, আমি মৌলিক তথ্য প্রদান করতে এবং আপনার অনুরোধ সারিবদ্ধ করতে পারি। ফসল নির্ণয়, বাজার ডেটা এবং সতর্কতার জন্য, ইন্টারনেটে সংযুক্ত হন।',
        'hi': 'ऑफ़लाइन मोड में, मैं बुनियादी जानकारी प्रदान कर सकता हूं और आपके अनुरोधों को कतारबद्ध कर सकता हूं। फसल निदान, बाजार डेटा और अलर्ट के लिए, कृपया इंटरनेट से कनेक्ट करें।',
      },
    };

    return templates[responseType]?.['en'] || 'Processing your request...';
  }

  /**
   * Get offline notification message
   */
  private getOfflineNotification(transcription: string): string {
    return `Your request has been queued and will be processed when internet connectivity is restored. You said: "${transcription}"`;
  }

  /**
   * Queue command for synchronization
   */
  private async queueForSync(
    commandId: string,
    farmerId: string,
    audioUrl: string,
    localTranscription: string,
    status: string
  ): Promise<void> {
    const command: OfflineVoiceCommand = {
      commandId,
      farmerId,
      audioUrl,
      timestamp: new Date(),
      status: status as any,
      localTranscription,
      retryCount: 0,
    };

    await docClient.send(
      new PutCommand({
        TableName: TABLE_NAME,
        Item: {
          PK: `OFFLINE_QUEUE#${farmerId}`,
          SK: `COMMAND#${commandId}`,
          ...command,
          GSI_PK: 'OFFLINE_QUEUE',
          GSI_SK: `STATUS#${status}#${Date.now()}`,
        },
      })
    );

    console.log(`Command queued for sync: ${commandId}`);
  }

  /**
   * Get queued commands for a farmer
   */
  async getQueuedCommands(farmerId: string): Promise<OfflineVoiceCommand[]> {
    const result = await docClient.send(
      new QueryCommand({
        TableName: TABLE_NAME,
        KeyConditionExpression: 'PK = :pk AND begins_with(SK, :sk)',
        ExpressionAttributeValues: {
          ':pk': `OFFLINE_QUEUE#${farmerId}`,
          ':sk': 'COMMAND#',
        },
      })
    );

    return (result.Items || []) as OfflineVoiceCommand[];
  }

  /**
   * Synchronize queued commands when online
   */
  async synchronizeQueuedCommands(farmerId: string): Promise<{
    synchronized: number;
    failed: number;
    pending: number;
  }> {
    console.log(`Synchronizing queued commands for farmer: ${farmerId}`);

    const queuedCommands = await this.getQueuedCommands(farmerId);
    
    let synchronized = 0;
    let failed = 0;
    let pending = 0;

    for (const command of queuedCommands) {
      if (command.status === 'queued' || command.status === 'processing') {
        try {
          // In production, this would trigger actual processing
          // For now, we'll just mark as completed
          await this.updateCommandStatus(command.commandId, farmerId, 'completed');
          synchronized++;
        } catch (error) {
          console.error(`Failed to sync command ${command.commandId}:`, error);
          failed++;
        }
      } else if (command.status === 'completed') {
        synchronized++;
      } else {
        pending++;
      }
    }

    return { synchronized, failed, pending };
  }

  /**
   * Update command status
   */
  private async updateCommandStatus(
    commandId: string,
    farmerId: string,
    status: string
  ): Promise<void> {
    await docClient.send(
      new PutCommand({
        TableName: TABLE_NAME,
        Item: {
          PK: `OFFLINE_QUEUE#${farmerId}`,
          SK: `COMMAND#${commandId}`,
          status,
          updatedAt: new Date().toISOString(),
        },
      })
    );
  }

  /**
   * Provide voice feedback about offline status
   */
  getOfflineStatusFeedback(language: string = 'en'): string {
    const feedback: Record<string, string> = {
      'en': 'You are currently offline. Basic voice commands are available. Your requests will be processed when you reconnect to the internet.',
      'bn': 'আপনি বর্তমানে অফলাইন আছেন। মৌলিক ভয়েস কমান্ড উপলব্ধ। ইন্টারনেটে পুনরায় সংযোগ করলে আপনার অনুরোধ প্রক্রিয়া করা হবে।',
      'hi': 'आप वर्तमान में ऑफ़लाइन हैं। बुनियादी वॉयस कमांड उपलब्ध हैं। जब आप इंटरनेट से फिर से कनेक्ट होंगे तो आपके अनुरोधों को संसाधित किया जाएगा।',
    };

    return feedback[language] || feedback['en'];
  }
}
