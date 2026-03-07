# AWS Services Overview - Agri-Nexus V1 Platform

## Complete AWS Architecture

### 1. **AWS Bedrock** (AI/ML Service)
**Purpose**: AI-powered crop diagnosis, voice transcription, text generation, and text-to-speech

**Model Used**: Claude 3.5 Sonnet

**Operations**:
- Image analysis for crop disease diagnosis
- Audio transcription (speech-to-text)
- Contextual response generation for farmer queries
- Text-to-speech for voice responses

**Configuration**:
- Temperature: 0.3
- Max Tokens: 2048
- Retry logic with exponential backoff

**Cost Consideration**: Pay-per-use based on tokens processed

---

### 2. **AWS Lambda** (Serverless Compute)
**Purpose**: Backend business logic execution

**Lambda Functions** (5 total):

#### a. **analyze_crop_image**
- **Trigger**: API Gateway POST /diagnose
- **Timeout**: 30 seconds
- **Memory**: 512 MB (recommended)
- **Operations**: 
  - Validate and store image in S3
  - Call Bedrock for disease analysis
  - Store diagnosis in DynamoDB
  - Return structured diagnosis result

#### b. **get_diagnosis_history**
- **Trigger**: API Gateway GET /history/diagnoses
- **Timeout**: 15 seconds
- **Memory**: 256 MB
- **Operations**:
  - Query DynamoDB for user's diagnosis history
  - Return most recent 20 diagnoses

#### c. **process_voice_input**
- **Trigger**: API Gateway POST /voice/process
- **Timeout**: 30 seconds
- **Memory**: 512 MB
- **Operations**:
  - Call Bedrock for audio transcription
  - Generate contextual response using Bedrock
  - Store interaction in DynamoDB
  - Return transcript and response

#### d. **generate_voice_response**
- **Trigger**: API Gateway POST /voice/tts
- **Timeout**: 15 seconds
- **Memory**: 256 MB
- **Operations**:
  - Call Bedrock for text-to-speech
  - Return audio data (base64)

#### e. **ingest_market_data**
- **Trigger**: API Gateway POST /market/ingest
- **Timeout**: 60 seconds
- **Memory**: 512 MB
- **Operations**:
  - Store market price data in DynamoDB
  - Invoke trigger_alerts Lambda

#### f. **trigger_alerts**
- **Trigger**: Invoked by ingest_market_data Lambda
- **Timeout**: 60 seconds
- **Memory**: 512 MB
- **Operations**:
  - Query active price thresholds from DynamoDB
  - Compare prices against thresholds
  - Send SMS via SNS for triggered alerts
  - Store notification triggers in DynamoDB

**IAM Permissions Required**:
- DynamoDB: Read/Write access
- S3: Read/Write access
- Bedrock: InvokeModel access
- SNS: Publish access
- CloudWatch: Logs write access
- Lambda: InvokeFunction (for trigger_alerts)

---

### 3. **Amazon DynamoDB** (NoSQL Database)
**Purpose**: Data persistence with single-table design

**Table Name**: `agri-nexus-data`

**Primary Key**:
- **PK** (Partition Key): String - Entity identifier (e.g., USER#user123)
- **SK** (Sort Key): String - Entity type and timestamp (e.g., DIAGNOSIS#2024-01-15T10:30:00Z)

**Global Secondary Indexes (GSIs)**:

#### GSI1: Admin Queries
- **GSI1PK**: entity_type (e.g., "diagnosis", "interaction")
- **GSI1SK**: status_or_timestamp
- **Use Case**: Query all diagnoses, filter by status

#### GSI2: Market Data Queries
- **GSI2PK**: crop_type (e.g., "wheat", "rice")
- **GSI2SK**: location_timestamp (e.g., "delhi#2024-01-15T10:30:00Z")
- **Use Case**: Get latest prices by crop and location

#### GSI3: Alert Processing
- **GSI3PK**: alert_type_status (e.g., "price_alert#active")
- **GSI3SK**: target_price_timestamp
- **Use Case**: Query active price thresholds for alert triggering

**Capacity Mode**: On-Demand (recommended for MVP)

**Data Entities Stored**:
- User diagnoses
- Voice interactions
- Price thresholds (alerts)
- Market data
- Notification triggers

---

### 4. **Amazon S3** (Object Storage)
**Purpose**: Store crop images and audio files

**Bucket Name**: `agri-nexus-media-{account-id}`

**Folder Structure**:
```
/images/
  /{user_id}/
    /{timestamp}_{filename}.jpg
/audio/
  /{user_id}/
    /{timestamp}_{filename}.mp3
```

**Configuration**:
- **CORS**: Enabled for Streamlit frontend access
- **Lifecycle Policy**: Delete objects older than 90 days (optional)
- **Encryption**: Server-side encryption (SSE-S3)
- **Versioning**: Disabled (not needed for MVP)

**Access Pattern**: Pre-signed URLs for secure access

---

### 5. **Amazon SNS** (Simple Notification Service)
**Purpose**: Send SMS notifications for price alerts

**Topic**: Not required (using direct SMS publish)

**Configuration**:
- **SMS Type**: Transactional (for critical alerts)
- **Default Sender ID**: "AgriNexus" (if supported in region)
- **Monthly SMS Spend Limit**: Set appropriate limit

**Message Format**:
```
🌾 AgriNexus Alert
{crop_type} price in {location} has reached ₹{price}/quintal
Your target: ₹{target_price}/quintal
```

**Multilingual Support**: Messages sent in user's preferred language

**Cost**: ~$0.00645 per SMS in India

---

### 6. **Amazon API Gateway** (REST API)
**Purpose**: HTTP API for frontend-backend communication

**API Type**: REST API (not HTTP API)

**Endpoints**:

#### Dr. Crop Service
- `POST /diagnose` → analyze_crop_image Lambda
- `GET /history/diagnoses` → get_diagnosis_history Lambda

#### Sahayak Service
- `POST /voice/process` → process_voice_input Lambda
- `POST /voice/tts` → generate_voice_response Lambda

#### Alert Service
- `POST /market/ingest` → ingest_market_data Lambda

**Configuration**:
- **CORS**: Enabled for all origins (or specific Streamlit domain)
- **Authorization**: None (for MVP) or API Key
- **Throttling**: 1000 requests/second (default)
- **Stage**: `prod`

**URL Format**: `https://{api-id}.execute-api.{region}.amazonaws.com/prod`

---

### 7. **Amazon CloudWatch** (Monitoring & Logging)
**Purpose**: Application monitoring, logging, and alerting

**Log Groups** (one per Lambda):
- `/aws/lambda/analyze_crop_image`
- `/aws/lambda/get_diagnosis_history`
- `/aws/lambda/process_voice_input`
- `/aws/lambda/generate_voice_response`
- `/aws/lambda/ingest_market_data`
- `/aws/lambda/trigger_alerts`

**Metrics Tracked**:
- Lambda invocations
- Lambda duration
- Lambda errors
- API Gateway requests
- API Gateway latency
- DynamoDB read/write capacity
- Bedrock API calls

**Alarms** (Optional):
- Lambda error rate > 5%
- API Gateway 5xx errors > 10
- DynamoDB throttling events

**Retention**: 7 days (default) or 30 days for production

---

## AWS Services Summary

| Service | Purpose | Estimated Monthly Cost (MVP) |
|---------|---------|------------------------------|
| **Bedrock** | AI/ML inference | $20-50 (based on usage) |
| **Lambda** | Serverless compute | $5-10 (free tier covers most) |
| **DynamoDB** | NoSQL database | $2-5 (on-demand pricing) |
| **S3** | Object storage | $1-3 (storage + requests) |
| **SNS** | SMS notifications | $0.65 per 100 SMS |
| **API Gateway** | REST API | $3.50 per million requests |
| **CloudWatch** | Monitoring/Logging | $1-2 (logs + metrics) |
| **Total** | | **~$35-75/month** |

*Note: Costs assume moderate usage (100-500 requests/day). Free tier covers significant portion for first 12 months.*

---

## Regional Considerations

**Recommended Region**: `ap-south-1` (Mumbai, India)

**Reasons**:
1. Lowest latency for Indian users
2. Bedrock availability (verify Claude 3.5 Sonnet availability)
3. SNS SMS support for India
4. Data residency compliance

**Alternative Regions**:
- `us-east-1` (N. Virginia) - Most Bedrock models available
- `us-west-2` (Oregon) - Good Bedrock support

---

## Security Considerations

### IAM Roles
- **Lambda Execution Role**: Least privilege access to required services
- **API Gateway Role**: Invoke Lambda permissions
- **No hardcoded credentials**: Use IAM roles and environment variables

### Data Protection
- **Encryption at Rest**: DynamoDB and S3 use AWS-managed keys
- **Encryption in Transit**: HTTPS for all API calls
- **PII Handling**: Phone numbers stored securely in DynamoDB

### Network Security
- **API Gateway**: CORS configured for specific origins
- **Lambda**: VPC not required (using AWS service endpoints)
- **S3**: Bucket policy restricts access to Lambda execution role

---

## Scalability

### Current Architecture Supports:
- **Concurrent Users**: 100-1000 (Lambda auto-scales)
- **Requests/Second**: 1000+ (API Gateway default limit)
- **Data Storage**: Unlimited (DynamoDB and S3 scale automatically)
- **Geographic Distribution**: Single region (can add CloudFront for global CDN)

### Scaling Considerations:
- **Lambda Concurrency**: Reserve concurrency if needed
- **DynamoDB**: Switch to provisioned capacity for predictable workloads
- **API Gateway**: Request limit increase if needed
- **Bedrock**: Monitor rate limits and request quota increase

---

## Disaster Recovery

### Backup Strategy:
- **DynamoDB**: Enable point-in-time recovery (PITR)
- **S3**: Enable versioning for critical data
- **Lambda**: Code stored in version control (Git)
- **Infrastructure**: Use Infrastructure as Code (CDK/CloudFormation)

### Recovery Time Objective (RTO): 1-2 hours
### Recovery Point Objective (RPO): 5 minutes (DynamoDB PITR)

---

## Next Steps

1. **Setup AWS Account**: Ensure account has necessary service limits
2. **Enable Bedrock**: Request access to Claude 3.5 Sonnet model
3. **Create IAM Roles**: Set up execution roles with proper permissions
4. **Deploy Infrastructure**: Run infrastructure scripts (DynamoDB, S3)
5. **Deploy Lambda Functions**: Package and deploy all 6 Lambda functions
6. **Configure API Gateway**: Create REST API with all endpoints
7. **Test Integration**: Verify end-to-end functionality
8. **Monitor & Optimize**: Set up CloudWatch dashboards and alarms

---

## Support & Documentation

- **AWS Bedrock**: https://docs.aws.amazon.com/bedrock/
- **AWS Lambda**: https://docs.aws.amazon.com/lambda/
- **Amazon DynamoDB**: https://docs.aws.amazon.com/dynamodb/
- **Amazon S3**: https://docs.aws.amazon.com/s3/
- **Amazon SNS**: https://docs.aws.amazon.com/sns/
- **API Gateway**: https://docs.aws.amazon.com/apigateway/
- **CloudWatch**: https://docs.aws.amazon.com/cloudwatch/
