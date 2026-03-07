# Infrastructure Setup Guide - DynamoDB & S3

## Overview

This guide covers the setup of AWS infrastructure components (DynamoDB and S3) for the Agri-Nexus V1 Platform.

---

## Prerequisites

1. **AWS CLI configured**
   ```bash
   aws configure
   aws sts get-caller-identity  # Verify credentials
   ```

2. **Environment variables set**
   ```bash
   # In .env file
   AWS_REGION=us-east-1
   AWS_ACCOUNT_ID=<your-account-id>
   TABLE_NAME=agri-nexus-data
   IMAGE_BUCKET=agri-nexus-media-<your-account-id>
   ENVIRONMENT=development
   ```

3. **Python dependencies installed**
   ```bash
   pip install boto3 python-dotenv
   ```

---

## DynamoDB Table Setup

### What Gets Created

The script creates a single DynamoDB table with:

**Table Name**: `agri-nexus-data` (configurable via `TABLE_NAME` env var)

**Primary Keys**:
- `PK` (String) - Partition key
- `SK` (String) - Sort key

**Global Secondary Indexes (GSIs)**:

1. **GSI1** - Admin Dashboard Queries
   - `GSI1PK` (String) - Entity type
   - `GSI1SK` (String) - Status or timestamp
   - Use case: Query all entities of a specific type

2. **GSI2** - Market Data Queries
   - `GSI2PK` (String) - Crop type
   - `GSI2SK` (String) - Location and timestamp
   - Use case: Query market prices by crop and location

3. **GSI3** - Alert Processing
   - `GSI3PK` (String) - Alert type and status
   - `GSI3SK` (String) - Target price and timestamp
   - Use case: Query active alerts and triggered notifications

**Capacity**:
- Provisioned mode: 5 RCU / 5 WCU (table and each GSI)
- Cost: ~$1-2/month for development

### Create DynamoDB Table

```bash
python infrastructure/create_dynamodb_table.py
```

**Expected Output**:
```
✅ Table 'agri-nexus-data' creation initiated successfully!
Table ARN: arn:aws:dynamodb:us-east-1:123456789012:table/agri-nexus-data
Table Status: CREATING

Waiting for table to become active...
✅ Table 'agri-nexus-data' is now ACTIVE and ready to use!
```

### Verify Table Creation

```bash
# Describe table
aws dynamodb describe-table --table-name agri-nexus-data --region us-east-1

# List tables
aws dynamodb list-tables --region us-east-1

# Check table status
aws dynamodb describe-table \
  --table-name agri-nexus-data \
  --region us-east-1 \
  --query 'Table.TableStatus' \
  --output text
```

### Delete Table (Cleanup)

```bash
python infrastructure/create_dynamodb_table.py delete
```

---

## S3 Bucket Setup

### What Gets Created

The script creates an S3 bucket with:

**Bucket Name**: `agri-nexus-media-<account-id>` (configurable via `IMAGE_BUCKET` env var)

**Configuration**:
1. **CORS** - Allows Streamlit frontend to upload/download files
   - Allowed methods: GET, PUT, POST, DELETE, HEAD
   - Allowed origins: * (restrict in production)
   - Max age: 3000 seconds

2. **Lifecycle Policies**:
   - Images (`images/` prefix): Delete after 90 days
   - Audio (`audio/` prefix): Delete after 30 days

3. **Versioning**: Enabled for data protection

4. **Tags**:
   - Project: Agri-Nexus-V1
   - Environment: development/production

**Cost**: ~$0.50/month for < 1GB storage

### Create S3 Bucket

```bash
python infrastructure/create_s3_bucket.py
```

**Expected Output**:
```
✅ S3 bucket 'agri-nexus-media-123456789012' created successfully!
✅ CORS configuration applied to bucket 'agri-nexus-media-123456789012'
✅ Lifecycle policy applied to bucket 'agri-nexus-media-123456789012'
✅ Versioning enabled for bucket 'agri-nexus-media-123456789012'
✅ Tags applied to bucket 'agri-nexus-media-123456789012'

📦 Bucket URL: https://agri-nexus-media-123456789012.s3.us-east-1.amazonaws.com
```

### Verify Bucket Creation

```bash
# List buckets
aws s3 ls | grep agri-nexus

# Check bucket configuration
aws s3api get-bucket-cors --bucket agri-nexus-media-<account-id>
aws s3api get-bucket-lifecycle-configuration --bucket agri-nexus-media-<account-id>
aws s3api get-bucket-versioning --bucket agri-nexus-media-<account-id>

# List bucket contents
aws s3 ls s3://agri-nexus-media-<account-id>/
```

### Delete Bucket (Cleanup)

```bash
python infrastructure/create_s3_bucket.py delete
```

**Note**: This will delete ALL objects in the bucket before deleting the bucket itself.

---

## Data Models

### DynamoDB Entity Types

#### 1. Diagnosis Entity
```json
{
  "PK": "USER#farmer123",
  "SK": "DIAGNOSIS#2024-01-15T10:30:00Z",
  "GSI1PK": "DIAGNOSIS",
  "GSI1SK": "2024-01-15T10:30:00Z",
  "entity_type": "diagnosis",
  "disease_name": "Late Blight",
  "confidence": 87.5,
  "treatment": "Apply copper-based fungicide...",
  "image_s3_key": "images/farmer123/2024-01-15-103000.jpg",
  "language": "en",
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### 2. Voice Interaction Entity
```json
{
  "PK": "USER#farmer123",
  "SK": "INTERACTION#2024-01-15T11:00:00Z",
  "GSI1PK": "INTERACTION",
  "GSI1SK": "2024-01-15T11:00:00Z",
  "entity_type": "interaction",
  "transcript": "What fertilizer should I use for wheat?",
  "response_text": "For wheat cultivation, use NPK fertilizer...",
  "audio_s3_key": "audio/farmer123/2024-01-15-110000.mp3",
  "language": "hi",
  "created_at": "2024-01-15T11:00:00Z"
}
```

#### 3. Price Threshold Entity
```json
{
  "PK": "USER#farmer123",
  "SK": "PRICE_TARGET#wheat#delhi",
  "GSI3PK": "ALERT#ACTIVE",
  "GSI3SK": "2500.00#2024-01-15T12:00:00Z",
  "entity_type": "price_threshold",
  "crop_type": "wheat",
  "location": "delhi",
  "target_price": 2500.00,
  "phone_number": "+919876543210",
  "language": "hi",
  "created_at": "2024-01-15T12:00:00Z",
  "status": "active"
}
```

#### 4. Market Data Entity
```json
{
  "PK": "MARKET#wheat",
  "SK": "LOCATION#delhi#2024-01-15T14:00:00Z",
  "GSI2PK": "wheat",
  "GSI2SK": "delhi#2024-01-15T14:00:00Z",
  "entity_type": "market_data",
  "crop_type": "wheat",
  "location": "delhi",
  "price": 2550.00,
  "source": "simulation",
  "timestamp": "2024-01-15T14:00:00Z"
}
```

#### 5. Notification Trigger Entity
```json
{
  "PK": "USER#farmer123",
  "SK": "NOTIFICATION#2024-01-15T14:05:00Z",
  "GSI3PK": "ALERT#TRIGGERED",
  "GSI3SK": "2024-01-15T14:05:00Z",
  "entity_type": "notification",
  "crop_type": "wheat",
  "location": "delhi",
  "target_price": 2500.00,
  "current_price": 2550.00,
  "sms_status": "delivered",
  "retry_count": 0,
  "created_at": "2024-01-15T14:05:00Z"
}
```

### S3 Object Structure

```
agri-nexus-media-<account-id>/
├── images/
│   ├── farmer123/
│   │   ├── 2024-01-15-103000.jpg
│   │   ├── 2024-01-15-110000.jpg
│   │   └── ...
│   └── farmer456/
│       └── ...
└── audio/
    ├── farmer123/
    │   ├── 2024-01-15-110000.mp3
    │   └── ...
    └── farmer456/
        └── ...
```

---

## Access Patterns

### DynamoDB Query Patterns

1. **Get user's diagnosis history**
   ```python
   response = dynamodb.query(
       TableName='agri-nexus-data',
       KeyConditionExpression='PK = :pk AND begins_with(SK, :sk)',
       ExpressionAttributeValues={
           ':pk': 'USER#farmer123',
           ':sk': 'DIAGNOSIS#'
       }
   )
   ```

2. **Get user's price alerts**
   ```python
   response = dynamodb.query(
       TableName='agri-nexus-data',
       KeyConditionExpression='PK = :pk AND begins_with(SK, :sk)',
       ExpressionAttributeValues={
           ':pk': 'USER#farmer123',
           ':sk': 'PRICE_TARGET#'
       }
   )
   ```

3. **Get all active alerts (using GSI3)**
   ```python
   response = dynamodb.query(
       TableName='agri-nexus-data',
       IndexName='GSI3',
       KeyConditionExpression='GSI3PK = :gsi3pk',
       ExpressionAttributeValues={
           ':gsi3pk': 'ALERT#ACTIVE'
       }
   )
   ```

4. **Get latest market price for crop (using GSI2)**
   ```python
   response = dynamodb.query(
       TableName='agri-nexus-data',
       IndexName='GSI2',
       KeyConditionExpression='GSI2PK = :gsi2pk AND begins_with(GSI2SK, :gsi2sk)',
       ExpressionAttributeValues={
           ':gsi2pk': 'wheat',
           ':gsi2sk': 'delhi#'
       },
       ScanIndexForward=False,  # Descending order
       Limit=1
   )
   ```

---

## Troubleshooting

### Issue 1: Table Already Exists

**Error**: `ResourceInUseException: Table already exists`

**Solution**: 
- Table was created previously
- Use existing table or delete and recreate:
  ```bash
  python infrastructure/create_dynamodb_table.py delete
  python infrastructure/create_dynamodb_table.py
  ```

### Issue 2: Bucket Name Already Taken

**Error**: `BucketAlreadyExists: Bucket name already exists`

**Solution**:
- S3 bucket names are globally unique
- Change `IMAGE_BUCKET` in `.env` to a unique name:
  ```bash
  IMAGE_BUCKET=agri-nexus-media-<your-account-id>-<random-suffix>
  ```

### Issue 3: Insufficient Permissions

**Error**: `AccessDeniedException: User is not authorized`

**Solution**:
- Ensure your AWS credentials have permissions for:
  - `dynamodb:CreateTable`
  - `dynamodb:DescribeTable`
  - `s3:CreateBucket`
  - `s3:PutBucketCors`
  - `s3:PutBucketLifecycleConfiguration`

### Issue 4: Region Mismatch

**Error**: `InvalidLocationConstraint`

**Solution**:
- Ensure `AWS_REGION` in `.env` matches your AWS CLI configuration
- For `us-east-1`, no LocationConstraint is needed (script handles this)

---

## Cost Optimization

### DynamoDB

**Development**:
- Use provisioned capacity (5 RCU/WCU): ~$1-2/month
- Enable auto-scaling if usage varies

**Production**:
- Switch to on-demand pricing: ~$10-20/month
- Or use provisioned with auto-scaling

### S3

**Development**:
- < 1GB storage: ~$0.50/month
- Lifecycle policies reduce costs automatically

**Production**:
- 10GB storage: ~$5-10/month
- Consider S3 Intelligent-Tiering for cost optimization

---

## Monitoring

### DynamoDB Metrics

```bash
# View table metrics in CloudWatch
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name ConsumedReadCapacityUnits \
  --dimensions Name=TableName,Value=agri-nexus-data \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600 \
  --statistics Sum
```

### S3 Metrics

```bash
# View bucket metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/S3 \
  --metric-name BucketSizeBytes \
  --dimensions Name=BucketName,Value=agri-nexus-media-<account-id> Name=StorageType,Value=StandardStorage \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 86400 \
  --statistics Average
```

---

## Next Steps

After infrastructure setup:

1. ✅ DynamoDB table created
2. ✅ S3 bucket created
3. ⏭️ Deploy Lambda functions (`python infrastructure/deploy_lambdas.py`)
4. ⏭️ Create API Gateway (`./deploy_api_gateway.sh`)
5. ⏭️ Run integration tests (`python tests/test_integration.py`)

---

## Quick Reference

```bash
# Create infrastructure
python infrastructure/create_dynamodb_table.py
python infrastructure/create_s3_bucket.py

# Verify creation
aws dynamodb describe-table --table-name agri-nexus-data
aws s3 ls | grep agri-nexus

# Delete infrastructure (cleanup)
python infrastructure/create_dynamodb_table.py delete
python infrastructure/create_s3_bucket.py delete

# View table items (after data is added)
aws dynamodb scan --table-name agri-nexus-data --limit 10

# View bucket contents
aws s3 ls s3://agri-nexus-media-<account-id>/ --recursive
```

---

**Infrastructure setup complete! Ready for Lambda deployment.** 🚀

