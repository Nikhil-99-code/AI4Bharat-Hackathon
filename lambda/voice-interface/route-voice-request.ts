/**
 * Lambda Function: Route Voice Request
 * 
 * This function routes voice requests to appropriate services based on
 * intent recognition and handles ambiguous inputs with clarification.
 * 
 * Requirements: 3.2, 3.4
 */

import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';
import { NLUService, NLUResult } from './nlu-service';
import { EventBridgeClient, PutEventsCommand } from '@aws-sdk/client-eventbridge';

// Environment variables
const EVENT_BUS_NAME = process.env.EVENT_BUS_NAME!;
const AWS_REGION = process.env.AWS_REGION || 'us-east-1';

// Initialize clients
const nluService = new NLUService({ region: AWS_REGION });
const eventBridgeClient = new EventBridgeClient({ region: AWS_REGION });

interface RouteVoiceRequestInput {
  farmerId: string;
  transcription: string;
  language: 'bn' | 'hi' | 'en';
  sessionId: string;
  context?: Record<string, any>;
}

interface RouteVoiceRequestResult {
  routedTo: {
    service: string;
    action: string;
  };
  nluResult: NLUResult;
  eventId?: string;
  requiresClarification: boolean;
  clarificationQuestion?: string;
  suggestedOptions?: string[];
}

/**
 * Publish event to EventBridge for service routing
 */
async function publishServiceEvent(
  service: string,
  action: string,
  farmerId: string,
  parameters: Record<string, any>,
  sessionId: string
): Promise<string> {
  const event = {
    Time: new Date(),
    Source: 'voice-interface',
    DetailType: `voice.${service}.${action}`,
    Detail: JSON.stringify({
      farmerId,
      sessionId,
      parameters,
      timestamp: new Date().toISOString(),
    }),
    EventBusName: EVENT_BUS_NAME,
  };

  const response = await eventBridgeClient.send(
    new PutEventsCommand({
      Entries: [event],
    })
  );

  if (response.FailedEntryCount && response.FailedEntryCount > 0) {
    throw new Error(`Failed to publish event: ${JSON.stringify(response.Entries)}`);
  }

  return response.Entries?.[0]?.EventId || 'unknown';
}

/**
 * Validate required entities for intent
 */
function validateRequiredEntities(
  intent: string,
  entities: Array<{ entityType: string; value: string }>
): {
  valid: boolean;
  missingEntities: string[];
} {
  const requiredEntitiesMap: Record<string, string[]> = {
    'crop_diagnosis': ['crop_type'],
    'market_query': ['crop_type'],
    'price_alert': ['crop_type', 'price'],
    'grievance': [],
    'profile_update': [],
    'general_query': [],
  };

  const required = requiredEntitiesMap[intent] || [];
  const extractedTypes = entities.map(e => e.entityType);
  const missing = required.filter(r => !extractedTypes.includes(r));

  return {
    valid: missing.length === 0,
    missingEntities: missing,
  };
}

/**
 * Build clarification question for missing entities
 */
function buildClarificationForMissingEntities(
  intent: string,
  missingEntities: string[],
  language: string
): {
  question: string;
  suggestedOptions: string[];
} {
  const clarificationMap: Record<string, Record<string, { question: string; suggestedOptions: string[] }>> = {
    'en': {
      'crop_type': {
        question: 'Which crop are you asking about?',
        suggestedOptions: ['Rice', 'Wheat', 'Potato', 'Tomato', 'Other'],
      },
      'price': {
        question: 'What price target would you like to set?',
        suggestedOptions: ['₹1000 per quintal', '₹1500 per quintal', '₹2000 per quintal'],
      },
      'location': {
        question: 'Which location or market are you interested in?',
        suggestedOptions: ['Local market', 'District market', 'State market'],
      },
    },
    'bn': {
      'crop_type': {
        question: 'আপনি কোন ফসল সম্পর্কে জিজ্ঞাসা করছেন?',
        suggestedOptions: ['ধান', 'গম', 'আলু', 'টমেটো', 'অন্যান্য'],
      },
      'price': {
        question: 'আপনি কোন মূল্য লক্ষ্য নির্ধারণ করতে চান?',
        suggestedOptions: ['প্রতি কুইন্টাল ₹১০০০', 'প্রতি কুইন্টাল ₹১৫০০', 'প্রতি কুইন্টাল ₹২০০০'],
      },
      'location': {
        question: 'আপনি কোন স্থান বা বাজারে আগ্রহী?',
        suggestedOptions: ['স্থানীয় বাজার', 'জেলা বাজার', 'রাজ্য বাজার'],
      },
    },
    'hi': {
      'crop_type': {
        question: 'आप किस फसल के बारे में पूछ रहे हैं?',
        suggestedOptions: ['चावल', 'गेहूं', 'आलू', 'टमाटर', 'अन्य'],
      },
      'price': {
        question: 'आप कौन सा मूल्य लक्ष्य निर्धारित करना चाहते हैं?',
        suggestedOptions: ['₹1000 प्रति क्विंटल', '₹1500 प्रति क्विंटल', '₹2000 प्रति क्विंटल'],
      },
      'location': {
        question: 'आप किस स्थान या बाजार में रुचि रखते हैं?',
        suggestedOptions: ['स्थानीय बाजार', 'जिला बाजार', 'राज्य बाजार'],
      },
    },
  };

  const langMap = clarificationMap[language] || clarificationMap['en'];
  const firstMissing = missingEntities[0];
  const clarification = langMap[firstMissing] || {
    question: 'Could you please provide more information?',
    suggestedOptions: [],
  };

  return clarification;
}

/**
 * Main Lambda handler
 */
export async function handler(event: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> {
  console.log('Received voice request routing request');

  try {
    // Parse request body
    const request: RouteVoiceRequestInput = JSON.parse(event.body || '{}');

    // Validate required fields
    if (!request.farmerId || !request.transcription || !request.language || !request.sessionId) {
      return {
        statusCode: 400,
        body: JSON.stringify({
          error: 'Missing required fields: farmerId, transcription, language, sessionId',
        }),
      };
    }

    // Recognize intent and extract entities
    console.log('Recognizing intent...');
    const nluResult = await nluService.recognizeIntent(
      request.transcription,
      request.language,
      request.context
    );

    console.log(`Intent: ${nluResult.intent.category} (confidence: ${nluResult.confidence})`);
    console.log(`Entities: ${JSON.stringify(nluResult.entities)}`);

    // Check if clarification is needed
    if (nluResult.requiresClarification || nluResult.confidence < 0.6) {
      console.log('Clarification needed');

      // Handle ambiguous input
      const clarification = await nluService.handleAmbiguousInput(
        request.transcription,
        request.language,
        nluResult
      );

      return {
        statusCode: 200,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
        },
        body: JSON.stringify({
          requiresClarification: true,
          clarificationQuestion: clarification.clarificationQuestion,
          suggestedOptions: clarification.suggestedOptions,
          nluResult,
          context: clarification.context,
        }),
      };
    }

    // Validate required entities
    const validation = validateRequiredEntities(nluResult.intent.category, nluResult.entities);
    if (!validation.valid) {
      console.log(`Missing required entities: ${validation.missingEntities.join(', ')}`);

      const clarification = buildClarificationForMissingEntities(
        nluResult.intent.category,
        validation.missingEntities,
        request.language
      );

      return {
        statusCode: 200,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
        },
        body: JSON.stringify({
          requiresClarification: true,
          clarificationQuestion: clarification.question,
          suggestedOptions: clarification.suggestedOptions,
          nluResult,
          missingEntities: validation.missingEntities,
        }),
      };
    }

    // Route request to appropriate service
    const routing = nluService.routeRequest(nluResult.intent);
    console.log(`Routing to: ${routing.service}.${routing.action}`);

    // Build parameters from entities
    const parameters: Record<string, any> = {
      ...nluResult.intent.parameters,
      language: request.language,
    };

    nluResult.entities.forEach(entity => {
      parameters[entity.entityType] = entity.normalizedValue || entity.value;
    });

    // Publish event to EventBridge
    const eventId = await publishServiceEvent(
      routing.service,
      routing.action,
      request.farmerId,
      parameters,
      request.sessionId
    );

    console.log(`Event published: ${eventId}`);

    // Prepare response
    const response: RouteVoiceRequestResult = {
      routedTo: {
        service: routing.service,
        action: routing.action,
      },
      nluResult,
      eventId,
      requiresClarification: false,
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
    console.error('Error routing voice request:', error);

    return {
      statusCode: 500,
      body: JSON.stringify({
        error: 'Internal server error',
        message: error instanceof Error ? error.message : 'Unknown error occurred',
      }),
    };
  }
}
