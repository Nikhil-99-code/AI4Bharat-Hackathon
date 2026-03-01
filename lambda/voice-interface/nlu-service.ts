/**
 * Natural Language Understanding Service
 * 
 * This service handles intent recognition, entity extraction, and
 * ambiguous input handling for voice and text inputs.
 * 
 * Requirements: 3.2, 3.4
 */

import { BedrockClient, MultimodalInput } from '../../lib/services/bedrock/bedrock-client';

export interface IntentClassification {
  intentName: string;
  confidence: number;
  category: 'crop_diagnosis' | 'market_query' | 'price_alert' | 'grievance' | 'profile_update' | 'general_query';
  parameters: Record<string, any>;
}

export interface EntityExtraction {
  entityType: 'crop_type' | 'location' | 'price' | 'date' | 'disease' | 'quantity' | 'other';
  value: string;
  confidence: number;
  normalizedValue?: string;
}

export interface NLUResult {
  intent: IntentClassification;
  entities: EntityExtraction[];
  confidence: number;
  requiresClarification: boolean;
  clarificationQuestion?: string;
  suggestedActions?: string[];
}

export interface NLUServiceConfig {
  region?: string;
  enableLogging?: boolean;
}

/**
 * Natural Language Understanding Service
 */
export class NLUService {
  private bedrockClient: BedrockClient;
  private enableLogging: boolean;

  constructor(config: NLUServiceConfig = {}) {
    this.bedrockClient = new BedrockClient({
      region: config.region || process.env.AWS_REGION || 'us-east-1',
    });
    this.enableLogging = config.enableLogging ?? true;
  }

  /**
   * Parse transcribed text for user intent
   */
  async recognizeIntent(
    text: string,
    language: string,
    context?: Record<string, any>
  ): Promise<NLUResult> {
    this.log(`Recognizing intent for text: "${text}" (language: ${language})`);

    const systemPrompt = this.buildIntentRecognitionPrompt(language);
    const userPrompt = this.buildUserPrompt(text, language, context);

    const multimodalInput: MultimodalInput = {
      text: userPrompt,
    };

    const aiResponse = await this.bedrockClient.invoke(multimodalInput, systemPrompt);
    
    return this.parseNLUResponse(aiResponse.content, text, language);
  }

  /**
   * Extract entities from text
   */
  async extractEntities(
    text: string,
    language: string,
    intentCategory?: string
  ): Promise<EntityExtraction[]> {
    this.log(`Extracting entities from: "${text}"`);

    const systemPrompt = this.buildEntityExtractionPrompt(language, intentCategory);
    const userPrompt = `Text: "${text}"\n\nExtract all relevant entities.`;

    const multimodalInput: MultimodalInput = {
      text: userPrompt,
    };

    const aiResponse = await this.bedrockClient.invoke(multimodalInput, systemPrompt);
    
    return this.parseEntities(aiResponse.content);
  }

  /**
   * Route request to appropriate service based on intent
   */
  routeRequest(intent: IntentClassification): {
    service: string;
    action: string;
    parameters: Record<string, any>;
  } {
    const routingMap: Record<string, { service: string; action: string }> = {
      'crop_diagnosis': { service: 'dr-crop', action: 'analyze-crop-image' },
      'market_query': { service: 'market-agent', action: 'get-market-intelligence' },
      'price_alert': { service: 'price-alert', action: 'set-price-target' },
      'grievance': { service: 'grievance', action: 'create-grievance' },
      'profile_update': { service: 'user', action: 'update-profile' },
      'general_query': { service: 'general', action: 'handle-query' },
    };

    const route = routingMap[intent.category] || routingMap['general_query'];

    return {
      service: route.service,
      action: route.action,
      parameters: intent.parameters,
    };
  }

  /**
   * Handle ambiguous inputs with clarification requests
   */
  async handleAmbiguousInput(
    text: string,
    language: string,
    nluResult: NLUResult
  ): Promise<{
    clarificationQuestion: string;
    suggestedOptions: string[];
    context: Record<string, any>;
  }> {
    this.log(`Handling ambiguous input: "${text}"`);

    const systemPrompt = `You are a clarification assistant for an agricultural AI system.
When user input is ambiguous or unclear, generate helpful clarification questions.

Guidelines:
- Ask specific, focused questions
- Provide 2-3 suggested options when possible
- Use simple, clear language appropriate for farmers
- Consider the detected intent and entities
- Be respectful and patient

Language: ${language}

Respond in JSON format:
{
  "clarificationQuestion": "clear question in user's language",
  "suggestedOptions": ["option1", "option2", "option3"],
  "context": {
    "ambiguityType": "missing_info|multiple_interpretations|unclear_intent",
    "detectedIntent": "what was detected",
    "missingEntities": ["entity1", "entity2"]
  }
}`;

    const userPrompt = `User said: "${text}"

Detected intent: ${nluResult.intent.intentName} (confidence: ${nluResult.intent.confidence})
Detected entities: ${JSON.stringify(nluResult.entities)}

Generate a clarification question to help understand what the user wants.`;

    const multimodalInput: MultimodalInput = {
      text: userPrompt,
    };

    const aiResponse = await this.bedrockClient.invoke(multimodalInput, systemPrompt);
    
    return this.parseClarificationResponse(aiResponse.content, language);
  }

  /**
   * Build intent recognition prompt
   */
  private buildIntentRecognitionPrompt(language: string): string {
    return `You are an intent recognition system for an agricultural AI assistant serving farmers.

Your task is to analyze farmer input and identify:
1. Primary intent and category
2. Confidence level
3. Key parameters
4. Whether clarification is needed

Intent Categories:
- crop_diagnosis: Farmer wants to diagnose crop disease or health issues
- market_query: Farmer wants market prices, trends, or intelligence
- price_alert: Farmer wants to set price targets or alerts
- grievance: Farmer wants to report a problem or complaint
- profile_update: Farmer wants to update their profile information
- general_query: General questions or unclear intent

Entity Types:
- crop_type: Names of crops (rice, wheat, potato, tomato, etc.)
- location: Places, districts, markets
- price: Price values and amounts
- date: Time references (today, tomorrow, next week, etc.)
- disease: Disease names or symptoms
- quantity: Amounts and measurements

Language: ${language}

Respond in JSON format:
{
  "intent": {
    "intentName": "specific action description",
    "confidence": 0.0-1.0,
    "category": "one of the categories above",
    "parameters": {
      "key": "value"
    }
  },
  "entities": [
    {
      "entityType": "crop_type|location|price|date|disease|quantity|other",
      "value": "extracted value",
      "confidence": 0.0-1.0,
      "normalizedValue": "standardized value (optional)"
    }
  ],
  "confidence": 0.0-1.0,
  "requiresClarification": true/false,
  "clarificationReason": "why clarification is needed (if applicable)"
}`;
  }

  /**
   * Build entity extraction prompt
   */
  private buildEntityExtractionPrompt(language: string, intentCategory?: string): string {
    return `You are an entity extraction system for agricultural data.

Extract all relevant entities from the text:
- crop_type: Crop names
- location: Places, districts, markets
- price: Price values
- date: Time references
- disease: Disease names or symptoms
- quantity: Amounts and measurements

${intentCategory ? `Context: User intent is ${intentCategory}` : ''}

Language: ${language}

Respond in JSON format:
{
  "entities": [
    {
      "entityType": "type",
      "value": "extracted value",
      "confidence": 0.0-1.0,
      "normalizedValue": "standardized value"
    }
  ]
}`;
  }

  /**
   * Build user prompt with context
   */
  private buildUserPrompt(
    text: string,
    language: string,
    context?: Record<string, any>
  ): string {
    let prompt = `Language: ${language}\nUser input: "${text}"\n`;

    if (context) {
      prompt += `\nContext:\n${JSON.stringify(context, null, 2)}\n`;
    }

    prompt += '\nAnalyze this input and extract intent and entities.';

    return prompt;
  }

  /**
   * Parse NLU response from AI
   */
  private parseNLUResponse(response: string, originalText: string, language: string): NLUResult {
    try {
      const jsonMatch = response.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        const parsed = JSON.parse(jsonMatch[0]);
        
        return {
          intent: parsed.intent || this.getDefaultIntent(),
          entities: parsed.entities || [],
          confidence: parsed.confidence || 0.5,
          requiresClarification: parsed.requiresClarification || false,
          clarificationQuestion: parsed.clarificationReason,
        };
      }
    } catch (e) {
      this.log('Failed to parse NLU response, using fallback');
    }

    // Fallback: basic keyword matching
    return this.fallbackIntentRecognition(originalText, language);
  }

  /**
   * Parse entities from AI response
   */
  private parseEntities(response: string): EntityExtraction[] {
    try {
      const jsonMatch = response.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        const parsed = JSON.parse(jsonMatch[0]);
        return parsed.entities || [];
      }
    } catch (e) {
      this.log('Failed to parse entities');
    }

    return [];
  }

  /**
   * Parse clarification response
   */
  private parseClarificationResponse(
    response: string,
    language: string
  ): {
    clarificationQuestion: string;
    suggestedOptions: string[];
    context: Record<string, any>;
  } {
    try {
      const jsonMatch = response.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        const parsed = JSON.parse(jsonMatch[0]);
        return {
          clarificationQuestion: parsed.clarificationQuestion || 'Could you please provide more details?',
          suggestedOptions: parsed.suggestedOptions || [],
          context: parsed.context || {},
        };
      }
    } catch (e) {
      this.log('Failed to parse clarification response');
    }

    return {
      clarificationQuestion: 'Could you please provide more details?',
      suggestedOptions: [],
      context: {},
    };
  }

  /**
   * Fallback intent recognition using keyword matching
   */
  private fallbackIntentRecognition(text: string, language: string): NLUResult {
    const lowerText = text.toLowerCase();

    // Keyword patterns for different intents
    const patterns = {
      crop_diagnosis: ['disease', 'sick', 'problem', 'leaf', 'spot', 'yellow', 'dying', 'রোগ', 'बीमारी'],
      market_query: ['price', 'market', 'sell', 'rate', 'cost', 'দাম', 'বাজার', 'कीमत', 'बाजार'],
      price_alert: ['alert', 'notify', 'target', 'reach', 'সতর্ক', 'सूचना'],
      grievance: ['complaint', 'problem', 'issue', 'delay', 'অভিযোগ', 'समस्या'],
      profile_update: ['update', 'change', 'profile', 'information', 'আপডেট', 'अपडेट'],
    };

    for (const [category, keywords] of Object.entries(patterns)) {
      if (keywords.some(keyword => lowerText.includes(keyword))) {
        return {
          intent: {
            intentName: category,
            confidence: 0.6,
            category: category as any,
            parameters: {},
          },
          entities: [],
          confidence: 0.6,
          requiresClarification: true,
          clarificationQuestion: 'Could you please provide more details about your request?',
        };
      }
    }

    return {
      intent: this.getDefaultIntent(),
      entities: [],
      confidence: 0.3,
      requiresClarification: true,
      clarificationQuestion: 'I did not understand your request. Could you please rephrase?',
    };
  }

  /**
   * Get default intent
   */
  private getDefaultIntent(): IntentClassification {
    return {
      intentName: 'general_query',
      confidence: 0.5,
      category: 'general_query',
      parameters: {},
    };
  }

  /**
   * Log message if logging is enabled
   */
  private log(message: string): void {
    if (this.enableLogging) {
      console.log(`[NLUService] ${message}`);
    }
  }
}
