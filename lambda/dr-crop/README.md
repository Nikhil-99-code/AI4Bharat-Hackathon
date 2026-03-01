# Dr. Crop Service - Lambda Functions

This directory contains AWS Lambda functions for the Dr. Crop service, which provides computer vision-based crop disease diagnosis using Amazon Bedrock with Claude 4.5 Sonnet.

## Functions

### 1. Analyze Crop Image (`analyze-crop-image.ts`)

**Purpose**: Analyzes crop images to identify diseases and provide treatment recommendations.

**Requirements**: 1.1, 1.4, 1.5

**Features**:
- Image preprocessing and validation
- Integration with Amazon Bedrock for visual analysis
- Disease identification with confidence scoring
- Treatment recommendation generation
- Preventive measures suggestions
- Severity level assessment
- Image storage in S3 with metadata
- Diagnosis results storage in DynamoDB

**API Request**:
```json
{
  "farmerId": "string",
  "imageData": "base64-encoded-image",
  "imageFormat": "png|jpeg|gif|webp",
  "cropType": "string (optional)",
  "location": "string (optional)",
  "language": "en|bn|hi (optional, default: en)",
  "additionalContext": "string (optional)"
}
```

**API Response**:
```json
{
  "diagnosisId": "string",
  "diseaseIdentified": true|false,
  "diseaseName": "string (optional)",
  "confidence": 0.0-1.0,
  "treatmentRecommendations": [
    {
      "stepNumber": 1,
      "description": "string",
      "materials": ["string"],
      "timing": "string",
      "precautions": ["string"]
    }
  ],
  "preventiveMeasures": ["string"],
  "followUpRequired": true|false,
  "severityLevel": "low|medium|high|critical",
  "imageUrl": "s3://bucket/key",
  "message": "string"
}
```

### 2. Validate Image Quality (`validate-image-quality.ts`)

**Purpose**: Validates crop image quality before analysis to ensure accurate diagnosis.

**Requirements**: 1.3

**Features**:
- Resolution validation (minimum 800x600, recommended 1920x1080)
- File size validation (10KB - 10MB)
- Format validation (JPEG, PNG, WEBP, GIF)
- Blur detection using Laplacian variance
- Lighting assessment (underexposed, overexposed, optimal)
- Focus quality estimation
- Multilingual guidance messages (English, Bengali, Hindi)
- Specific improvement recommendations

**API Request**:
```json
{
  "imageData": "base64-encoded-image",
  "imageFormat": "png|jpeg|gif|webp",
  "language": "en|bn|hi (optional, default: en)"
}
```

**API Response**:
```json
{
  "valid": true|false,
  "issues": [
    {
      "type": "resolution|format|size|blur|lighting|focus",
      "severity": "error|warning",
      "message": "string"
    }
  ],
  "recommendations": ["string"],
  "metadata": {
    "width": 1920,
    "height": 1080,
    "format": "jpeg",
    "size": 524288,
    "aspectRatio": 1.78,
    "estimatedBlur": 150.5,
    "estimatedBrightness": 0.65
  }
}
```

### 3. Get Diagnosis History (`get-diagnosis-history.ts`)

**Purpose**: Retrieves a farmer's crop diagnosis history with pagination and filtering.

**Requirements**: 1.5

**Features**:
- Pagination support with next token
- Date range filtering (startDate, endDate)
- Disease type filtering
- Severity level filtering
- Diagnosis statistics calculation
- Common disease identification
- Follow-up tracking

**API Request** (Query Parameters):
```
GET /diagnosis-history?farmerId=string&limit=50&nextToken=string&startDate=ISO8601&endDate=ISO8601&diseaseType=string&severityLevel=low|medium|high|critical
```

**API Response**:
```json
{
  "diagnoses": [
    {
      "diagnosisId": "string",
      "farmerId": "string",
      "imageUrl": "string",
      "diseaseIdentified": "string|null",
      "diseaseName": "string",
      "confidence": 0.85,
      "treatmentRecommendations": [...],
      "preventiveMeasures": [...],
      "followUpRequired": true,
      "severityLevel": "high",
      "createdAt": "ISO8601"
    }
  ],
  "count": 25,
  "nextToken": "string (optional)",
  "hasMore": true|false
}
```

**Statistics Endpoint**:
```
GET /diagnosis-statistics?farmerId=string
```

**Statistics Response**:
```json
{
  "totalDiagnoses": 150,
  "diseasesDetected": 45,
  "healthyScans": 105,
  "followUpRequired": 12,
  "severityBreakdown": {
    "low": 20,
    "medium": 15,
    "high": 8,
    "critical": 2
  },
  "commonDiseases": [
    { "disease": "Late Blight", "count": 15 },
    { "disease": "Powdery Mildew", "count": 12 }
  ]
}
```

## Environment Variables

All functions require the following environment variables:

- `TABLE_NAME`: DynamoDB table name for single-table design
- `IMAGE_BUCKET`: S3 bucket name for crop images
- `AWS_REGION`: AWS region (default: us-east-1)

## Dependencies

- `@aws-sdk/client-bedrock-runtime`: Amazon Bedrock integration
- `@aws-sdk/client-s3`: S3 image storage
- `@aws-sdk/client-dynamodb`: DynamoDB data storage
- `sharp`: Image processing and quality analysis
- `uuid`: Unique identifier generation
- `zod`: Runtime validation

## Deployment

These functions are deployed as part of the Agri-Nexus CDK stack. They use:

- Lambda layers for shared dependencies
- API Gateway for HTTP endpoints
- IAM roles with least-privilege access
- CloudWatch for logging and monitoring
- EventBridge for event-driven communication

## Testing

Run tests with:
```bash
npm test
```

## Error Handling

All functions implement:
- Input validation with descriptive error messages
- Circuit breaker pattern for external service calls
- Retry logic with exponential backoff
- Comprehensive logging for debugging
- Graceful degradation for non-critical failures

## Multilingual Support

The service supports three languages:
- English (en)
- Bengali (bn)
- Hindi (hi)

All user-facing messages, treatment recommendations, and guidance are provided in the farmer's preferred language.

## Performance

- Image analysis: < 10 seconds for 95% of requests
- Image validation: < 2 seconds
- History retrieval: < 1 second with pagination

## Security

- All images encrypted at rest in S3
- All data encrypted in transit (HTTPS)
- IAM role-based access control
- Input validation and sanitization
- No sensitive data in logs
