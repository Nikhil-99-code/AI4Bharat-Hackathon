# Agri-Nexus Serverless Infrastructure

This repository contains the AWS CDK infrastructure code for the Agri-Nexus Multimodal AI Operating System. The infrastructure is built using serverless, event-driven architecture patterns to ensure high availability, automatic scaling, and fault tolerance.

## Architecture Overview

The Agri-Nexus infrastructure consists of the following components:

### Core Infrastructure

1. **DynamoDB Single-Table Design**
   - Primary table with composite keys (PK, SK)
   - Three Global Secondary Indexes (GSI1, GSI2, GSI3)
   - Point-in-time recovery enabled
   - DynamoDB Streams for event processing
   - Pay-per-request billing for variable workloads

2. **S3 Storage Buckets**
   - Image bucket for crop photos
   - Audio bucket for voice recordings
   - Lifecycle policies for cost optimization
   - Versioning enabled for data protection
   - Server access logging for audit trails

3. **EventBridge Event Bus**
   - Custom event bus for inter-service communication
   - Event rules for different service types
   - Event archiving for replay and debugging
   - CloudWatch Logs integration

4. **Lambda Layers**
   - Python layer with common dependencies (boto3, Pillow, numpy)
   - Node.js layer with AWS SDK and utilities
   - Compatible with multiple runtime versions

5. **CloudWatch Monitoring**
   - Comprehensive dashboard for system metrics
   - Alarms for critical thresholds
   - SNS topic for alarm notifications
   - Metrics for DynamoDB, S3, and EventBridge

## Prerequisites

- Node.js 18.x or later
- AWS CLI configured with appropriate credentials
- AWS CDK CLI installed (`npm install -g aws-cdk`)
- TypeScript installed

## Installation

1. Clone the repository and install dependencies:

```bash
npm install
```

2. Configure AWS credentials:

```bash
aws configure
```

3. Bootstrap CDK (first time only):

```bash
cdk bootstrap
```

## Deployment

### Deploy the infrastructure:

```bash
npm run deploy
```

### View the CloudFormation template:

```bash
npm run synth
```

### Check differences before deployment:

```bash
npm run diff
```

### Destroy the infrastructure:

```bash
npm run destroy
```

## Infrastructure Components

### DynamoDB Table Schema

The single-table design uses the following key structure:

**Primary Keys:**
- `PK`: Partition key (Entity type and identifier)
- `SK`: Sort key (Entity subtype or relationship)

**Global Secondary Indexes:**

1. **GSI1 - Admin Dashboard Queries**
   - `GSI1PK`: Entity type (e.g., "GRIEVANCE", "DIAGNOSIS")
   - `GSI1SK`: Status or timestamp

2. **GSI2 - Market Data Queries**
   - `GSI2PK`: Crop type
   - `GSI2SK`: Location and timestamp

3. **GSI3 - Alert Processing**
   - `GSI3PK`: Alert type and status
   - `GSI3SK`: Target price and timestamp

**Entity Examples:**

```typescript
// User Profile
PK: "USER#<farmerId>"
SK: "PROFILE"

// Crop Diagnosis
PK: "USER#<farmerId>"
SK: "DIAGNOSIS#<timestamp>"

// Price Target
PK: "USER#<farmerId>"
SK: "PRICE_TARGET#<cropType>"

// Market Data
PK: "MARKET#<cropType>#<location>"
SK: "PRICE#<timestamp>"

// Grievance Ticket
PK: "USER#<farmerId>"
SK: "GRIEVANCE#<ticketId>"
```

### S3 Bucket Lifecycle Policies

**Image Bucket:**
- Transition to Infrequent Access after 90 days
- Archive to Glacier after 365 days
- Delete old versions after 90 days

**Audio Bucket:**
- Transition to Infrequent Access after 30 days
- Archive to Glacier after 180 days
- Delete old versions after 30 days

### EventBridge Event Patterns

The event bus routes events based on source and detail type:

**Dr. Crop Service:**
- Source: `agri-nexus.dr-crop`
- Detail Types: `Diagnosis Completed`, `Diagnosis Failed`

**Market Agent:**
- Source: `agri-nexus.market-agent`
- Detail Types: `Price Update`, `Market Alert`, `Trend Detected`

**Price Alert Service:**
- Source: `agri-nexus.price-alert`
- Detail Types: `Target Reached`, `Alert Sent`, `Target Updated`

**Grievance Service:**
- Source: `agri-nexus.grievance`
- Detail Types: `Ticket Created`, `Ticket Updated`, `Ticket Resolved`

**Multimodal AI:**
- Source: `agri-nexus.multimodal`
- Detail Types: `Context Updated`, `Modality Transition`, `Proactive Alert`

## Stack Outputs

After deployment, the following outputs are available:

- `TableName`: DynamoDB table name
- `ImageBucketName`: S3 bucket for images
- `AudioBucketName`: S3 bucket for audio
- `EventBusName`: EventBridge event bus name
- `PythonLayerArn`: Lambda layer ARN for Python
- `NodeLayerArn`: Lambda layer ARN for Node.js
- `DashboardUrl`: CloudWatch dashboard URL

## Monitoring and Alarms

### CloudWatch Dashboard

The dashboard includes widgets for:
- DynamoDB read/write capacity
- DynamoDB throttles
- S3 storage metrics
- EventBridge invocations and failures

### Alarms

Two critical alarms are configured:

1. **DynamoDB Throttle Alarm**
   - Triggers when throttles exceed 10 in 10 minutes
   - Sends notification to SNS topic

2. **EventBridge Failure Alarm**
   - Triggers when failed invocations exceed 5 in 10 minutes
   - Sends notification to SNS topic

## Security

- All S3 buckets have public access blocked
- Encryption at rest enabled for DynamoDB and S3
- Server access logging enabled for S3 buckets
- IAM roles follow least privilege principle
- Versioning enabled for data protection

## Cost Optimization

- DynamoDB uses pay-per-request billing
- S3 lifecycle policies transition data to cheaper storage classes
- Lambda layers reduce deployment package sizes
- CloudWatch log retention set to 30 days

## Next Steps

After deploying the infrastructure, you can:

1. Deploy Lambda functions for each service (Dr. Crop, Market Agent, etc.)
2. Configure API Gateway for HTTP endpoints
3. Set up Cognito for user authentication
4. Integrate with Amazon Bedrock for AI capabilities
5. Configure SNS for SMS notifications

## Troubleshooting

### CDK Bootstrap Issues

If you encounter bootstrap errors:

```bash
cdk bootstrap aws://ACCOUNT-NUMBER/REGION
```

### Permission Errors

Ensure your AWS credentials have the following permissions:
- CloudFormation full access
- DynamoDB full access
- S3 full access
- EventBridge full access
- Lambda full access
- CloudWatch full access
- IAM role creation

### Layer Build Issues

If Lambda layers fail to build, ensure Docker is running (CDK uses Docker for bundling).

## Contributing

When adding new infrastructure components:

1. Create a new construct in `lib/constructs/`
2. Import and instantiate in `lib/agri-nexus-stack.ts`
3. Add appropriate tags and monitoring
4. Update this README with documentation

## License

MIT License - See LICENSE file for details

## Support

For issues and questions, please open a GitHub issue or contact the Agri-Nexus team.
