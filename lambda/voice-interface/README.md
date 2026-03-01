# Voice Interface Service

The Voice Interface Service provides multilingual voice processing capabilities for the Agri-Nexus platform, enabling farmers to interact with the system using voice commands in Bengali, Hindi, and English.

## Features

### 1. Voice Input Processing
- **Speech-to-Text**: Converts voice input to text using Amazon Transcribe
- **Language Detection**: Automatically detects Bengali, Hindi, or English
- **Audio Storage**: Stores audio files in S3 with proper metadata
- **Multi-format Support**: Handles MP3, WAV, FLAC, and OGG formats

### 2. Intent Recognition and NLU
- **Intent Classification**: Identifies user intent (crop diagnosis, market query, price alert, grievance, etc.)
- **Entity Extraction**: Extracts key entities (crop types, locations, prices, dates, diseases)
- **Confidence Scoring**: Provides confidence levels for intent and entity recognition
- **Ambiguous Input Handling**: Requests clarification when input is unclear

### 3. Voice Response Generation
- **Text-to-Speech**: Converts text responses to speech using Amazon Polly
- **Multilingual Support**: Generates voice responses in Bengali, Hindi, and English
- **Voice Selection**: Uses appropriate voices for each language
- **Audio Delivery**: Returns audio as base64 or S3 URL

### 4. Offline Voice Processing
- **Local Processing**: Handles basic commands offline using cached models
- **Command Queuing**: Queues complex commands for processing when online
- **Offline Feedback**: Provides voice feedback about offline status
- **Automatic Sync**: Synchronizes queued commands when connectivity is restored

## Lambda Functions

### process-voice-input.ts
Handles voice input processing including transcription, language detection, and intent recognition.

**Endpoint**: `POST /voice/process`

**Request**:
```json
{
  "farmerId": "farmer123",
  "audioData": "base64_encoded_audio",
  "audioFormat": "mp3",
  "language": "bn",
  "sessionId": "session123"
}
```

**Response**:
```json
{
  "transcription": "আমার ধানের রোগ হয়েছে",
  "detectedLanguage": "bn",
  "intent": {
    "intentName": "diagnose_crop_disease",
    "confidence": 0.95,
    "category": "crop_diagnosis"
  },
  "entities": [
    {
      "entityType": "crop_type",
      "value": "ধান",
      "confidence": 0.98
    }
  ],
  "confidence": 0.95,
  "requiresClarification": false,
  "sessionId": "session123",
  "audioUrl": "s3://bucket/voice-recordings/..."
}
```

### generate-voice-response.ts
Converts text responses to speech in the user's preferred language.

**Endpoint**: `POST /voice/generate`

**Request**:
```json
{
  "text": "আপনার ধানে ব্লাস্ট রোগ হয়েছে",
  "language": "bn",
  "farmerId": "farmer123",
  "outputFormat": "mp3"
}
```

**Response**:
```json
{
  "audioUrl": "s3://bucket/voice-responses/...",
  "audioData": "base64_encoded_audio",
  "duration": 5,
  "language": "bn",
  "voiceId": "Aditi"
}
```

### route-voice-request.ts
Routes voice requests to appropriate services based on intent recognition.

**Endpoint**: `POST /voice/route`

**Request**:
```json
{
  "farmerId": "farmer123",
  "transcription": "আলুর দাম কত",
  "language": "bn",
  "sessionId": "session123"
}
```

**Response**:
```json
{
  "routedTo": {
    "service": "market-agent",
    "action": "get-market-intelligence"
  },
  "nluResult": {
    "intent": {
      "intentName": "get_market_price",
      "confidence": 0.92,
      "category": "market_query"
    },
    "entities": [
      {
        "entityType": "crop_type",
        "value": "আলু",
        "confidence": 0.95
      }
    ]
  },
  "eventId": "event-123",
  "requiresClarification": false
}
```

### handle-offline-voice.ts
Handles voice processing in offline mode with command queuing.

**Endpoint**: `POST /voice/offline`

**Request**:
```json
{
  "farmerId": "farmer123",
  "audioData": "base64_encoded_audio",
  "audioFormat": "mp3",
  "language": "bn"
}
```

**Response**:
```json
{
  "result": {
    "commandId": "offline-1234567890-farmer123",
    "status": "queued",
    "localResponse": "Your request has been queued...",
    "queuedForSync": true,
    "estimatedSyncTime": "2024-01-15T10:00:00Z"
  },
  "voiceFeedback": "আপনি বর্তমানে অফলাইন আছেন...",
  "queueStatus": {
    "totalQueued": 3,
    "estimatedSyncTime": "2024-01-15T10:00:00Z"
  }
}
```

## NLU Service

The NLU Service (`nlu-service.ts`) provides natural language understanding capabilities:

### Intent Categories
- **crop_diagnosis**: Crop disease diagnosis requests
- **market_query**: Market price and intelligence queries
- **price_alert**: Price target and alert management
- **grievance**: Problem reporting and complaints
- **profile_update**: User profile updates
- **general_query**: General questions

### Entity Types
- **crop_type**: Crop names (rice, wheat, potato, etc.)
- **location**: Places, districts, markets
- **price**: Price values and amounts
- **date**: Time references
- **disease**: Disease names or symptoms
- **quantity**: Amounts and measurements

### Clarification Handling
When input is ambiguous or confidence is low, the system:
1. Identifies missing or unclear information
2. Generates clarification questions in the user's language
3. Provides suggested options for quick response
4. Maintains conversation context

## Offline Voice Processor

The Offline Voice Processor (`offline-voice-processor.ts`) handles offline scenarios:

### Cached Models
- Basic greetings and responses
- Status checks
- Help requests
- Simple queries

### Command Queuing
- Stores commands in DynamoDB
- Tracks processing status
- Manages retry logic
- Synchronizes when online

### Offline Capabilities
- Basic pattern matching for common commands
- Local response generation
- Queue management
- Status feedback

## Integration with Other Services

### EventBridge Integration
Voice requests are routed to appropriate services via EventBridge:
- Event source: `voice-interface`
- Detail type: `voice.{service}.{action}`
- Event payload includes farmer ID, session ID, and extracted parameters

### S3 Storage
Audio files are stored in S3 with organized structure:
- Voice recordings: `voice-recordings/{farmerId}/{timestamp}-{uuid}.{format}`
- Voice responses: `voice-responses/{farmerId}/{timestamp}-{uuid}.{format}`
- Offline audio: `offline-voice/{farmerId}/{timestamp}-{uuid}.{format}`

### DynamoDB Storage
Offline commands are stored in DynamoDB:
- PK: `OFFLINE_QUEUE#{farmerId}`
- SK: `COMMAND#{commandId}`
- GSI for status-based queries

## Supported Languages

### Bengali (bn)
- Language code: `bn-IN`
- Transcribe support: Yes
- Polly voice: Aditi

### Hindi (hi)
- Language code: `hi-IN`
- Transcribe support: Yes
- Polly voice: Aditi

### English (en)
- Language code: `en-IN`
- Transcribe support: Yes
- Polly voice: Kajal

## Error Handling

### Transcription Errors
- Timeout after 60 seconds
- Retry with exponential backoff
- Fallback to offline processing

### Intent Recognition Errors
- Low confidence triggers clarification
- Fallback to keyword matching
- Default to general query category

### Offline Processing Errors
- Queue commands for later processing
- Provide user feedback
- Track retry attempts

## Requirements Validation

### Requirement 3.1: Voice Transcription
✅ Implemented in `process-voice-input.ts` using Amazon Transcribe

### Requirement 3.2: Intent Recognition
✅ Implemented in `nlu-service.ts` with entity extraction

### Requirement 3.3: Text-to-Speech
✅ Implemented in `generate-voice-response.ts` using Amazon Polly

### Requirement 3.4: Ambiguous Input Handling
✅ Implemented in `nlu-service.ts` with clarification requests

### Requirement 3.5: Offline Voice Processing
✅ Implemented in `offline-voice-processor.ts` with command queuing

### Requirement 8.1: Offline Functionality
✅ Implemented with cached models and queue synchronization

## Testing

### Unit Tests
Test individual functions:
- Voice transcription accuracy
- Intent recognition precision
- Entity extraction completeness
- Offline processing logic

### Integration Tests
Test end-to-end flows:
- Voice input to service routing
- Offline to online synchronization
- Multi-language support
- Error handling scenarios

### Property Tests
Verify universal properties:
- All voice inputs produce valid transcriptions
- Intent confidence is between 0 and 1
- Entities are properly extracted
- Offline commands are queued correctly

## Performance Considerations

### Transcription
- Average latency: 5-10 seconds
- Concurrent job limit: 100
- Max audio duration: 4 hours

### Text-to-Speech
- Average latency: 1-2 seconds
- Max text length: 3000 characters
- Concurrent request limit: 80

### Offline Processing
- Local processing: <1 second
- Queue storage: Unlimited
- Sync batch size: 25 commands

## Future Enhancements

1. **Advanced Offline Models**: Deploy lightweight ML models for better offline transcription
2. **Voice Biometrics**: Add voice-based authentication
3. **Conversation Memory**: Maintain longer conversation context
4. **Multi-turn Dialogues**: Support complex multi-step interactions
5. **Custom Vocabulary**: Add agricultural terminology for better recognition
6. **Real-time Streaming**: Support streaming audio for faster response
