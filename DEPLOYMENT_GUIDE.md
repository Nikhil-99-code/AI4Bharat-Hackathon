# Agri-Nexus V1 Platform - Deployment Guide

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **Python 3.12+** installed
3. **AWS CLI** configured with credentials
4. **pip** package manager

## Step-by-Step Deployment

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.template .env

# Edit .env file with your AWS credentials and configuration
# Required variables:
# - AWS_REGION
# - AWS_ACCESS_KEY_ID
# - AWS_SECRET_ACCESS_KEY
# - TABLE_NAME
# - IMAGE_BUCKET
```

### 3. Create AWS Infrastructure

#### 3.1 Create DynamoDB Table

```bash
python infrastructure/create_dynamodb_table.py
```

This creates a single DynamoDB table with:
- Primary keys: PK (partition key), SK (sort key)
- 3 Global Secondary Indexes (GSI1, GSI2, GSI3)
- Provisioned capacity: 5 RCU/WCU

#### 3.2 Create S3 Bucket

```bash
python infrastructure/create_s3_bucket.py
```

This creates an S3 bucket with:
- CORS configuration for Streamlit access
- Lifecycle policies (90 days for images, 30 days for audio)
- Versioning enabled

### 4. Deploy Lambda Functions

```bash
python infrastructure/deploy_lambdas.py
```

This script will:
1. Package each Lambda function with dependencies
2. Create IAM roles with appropriate permissions
3. Deploy/update all 5 Lambda functions:
   - `analyze_crop_image` (30s timeout, 512MB)
   - `process_voice_input` (15s timeout, 512MB)
   - `generate_voice_response` (15s timeout, 256MB)
   - `ingest_market_data` (10s timeout, 256MB)
   - `trigger_alerts` (60s timeout, 512MB)

**Note:** The deployment script automatically:
- Creates IAM roles with DynamoDB, S3, SNS, and Bedrock permissions
- Sets environment variables for each function
- Handles both new deployments and updates

### 5. Create API Gateway (Manual Step)

Since API Gateway creation requires specific endpoint configurations, follow these steps in AWS Console:

#### 5.1 Create REST API

1. Go to **API Gateway** in AWS Console
2. Click **Create API** → **REST API** → **Build**
3. Name: `agri-nexus-api`
4. Description: `API for Agri-Nexus V1 Platform`

#### 5.2 Create Resources and Methods

Create the following endpoints:

**POST /diagnose**
- Integration: Lambda Function → `analyze_crop_image`
- Enable CORS

**POST /voice/process**
- Integration: Lambda Function → `process_voice_input`
- Enable CORS

**POST /voice/tts**
- Integration: Lambda Function → `generate_voice_response`
- Enable CORS

**POST /market/ingest**
- Integration: Lambda Function → `ingest_market_data`
- Enable CORS

**POST /alerts/trigger**
- Integration: Lambda Function → `trigger_alerts`
- Enable CORS

#### 5.3 Deploy API

1. Click **Actions** → **Deploy API**
2. Stage name: `prod`
3. Copy the **Invoke URL** (e.g., `https://abc123.execute-api.us-east-1.amazonaws.com/prod`)

#### 5.4 Update Environment

Add the API Gateway URL to your `.env` file:

```bash
API_GATEWAY_URL=https://abc123.execute-api.us-east-1.amazonaws.com/prod
```

### 6. Enable AWS Bedrock Access

1. Go to **AWS Bedrock** in AWS Console
2. Navigate to **Model access**
3. Request access to **Claude 3.5 Sonnet** model
4. Wait for approval (usually instant for most accounts)

### 7. Configure SNS for SMS (Optional)

If you want SMS notifications to work:

1. Go to **SNS** in AWS Console
2. Navigate to **Text messaging (SMS)**
3. Set up SMS preferences:
   - Default message type: **Transactional**
   - Account spend limit: Set as needed
4. Verify phone numbers in sandbox mode (if applicable)

### 8. Run Streamlit Application

```bash
streamlit run frontend/streamlit_app.py
```

The application will be available at `http://localhost:8501`

## Testing the Deployment

### Test 1: Dr. Crop (Image Diagnosis)

1. Open the application
2. Go to **Dr. Crop** tab
3. Upload a crop image
4. Click **Analyze Image**
5. Verify diagnosis result appears

### Test 2: Sahayak (Voice Assistant)

1. Go to **Sahayak** tab
2. Type a question (voice recording coming soon)
3. Click **Submit Question**
4. Verify response appears

### Test 3: Alerts (Price Notifications)

1. Go to **Alerts** tab
2. Configure a price alert:
   - Crop: Wheat
   - Location: Delhi
   - Target Price: 2500
   - Phone: +919876543210
3. Click **Create Alert**
4. Click **Simulate Price Change**
5. Check phone for SMS (if SNS configured)

## Troubleshooting

### Lambda Deployment Issues

**Error: "Role not found"**
- Wait 10-15 seconds after role creation
- Re-run deployment script

**Error: "Access denied to Bedrock"**
- Ensure Bedrock model access is enabled
- Check IAM role has Bedrock permissions

### DynamoDB Issues

**Error: "Table already exists"**
- Table was created previously
- Use existing table or delete and recreate

### S3 Issues

**Error: "Bucket name already taken"**
- S3 bucket names are globally unique
- Change `IMAGE_BUCKET` in `.env` to a unique name

### API Gateway Issues

**Error: "CORS error in browser"**
- Ensure CORS is enabled for all methods
- Add `Access-Control-Allow-Origin: *` header

### Bedrock Issues

**Error: "Model not found"**
- Verify model ID: `anthropic.claude-3-5-sonnet-20241022-v2:0`
- Check Bedrock model access is approved

**Error: "Throttling exception"**
- Bedrock has rate limits
- Retry logic is built-in (3 attempts with exponential backoff)

## Cost Estimation

### Development/Testing (Low Usage)

- **DynamoDB**: ~$1-2/month (5 RCU/WCU)
- **S3**: ~$0.50/month (< 1GB storage)
- **Lambda**: ~$0-1/month (free tier covers most testing)
- **Bedrock**: ~$3-5/month (Claude 3.5 Sonnet: $3/1M input tokens, $15/1M output tokens)
- **SNS**: ~$0.10/month (100 SMS in sandbox)
- **API Gateway**: ~$0-1/month (free tier: 1M requests)

**Total**: ~$5-10/month for development

### Production (Moderate Usage)

- **DynamoDB**: ~$10-20/month (on-demand pricing)
- **S3**: ~$5-10/month (10GB storage + requests)
- **Lambda**: ~$5-10/month (1M requests)
- **Bedrock**: ~$50-100/month (depends on usage)
- **SNS**: ~$10-20/month (1000 SMS)
- **API Gateway**: ~$3-5/month (1M requests)

**Total**: ~$80-165/month for moderate production use

## Monitoring

### CloudWatch Logs

All Lambda functions log to CloudWatch:
- `/aws/lambda/analyze_crop_image`
- `/aws/lambda/process_voice_input`
- `/aws/lambda/generate_voice_response`
- `/aws/lambda/ingest_market_data`
- `/aws/lambda/trigger_alerts`

### Metrics to Monitor

- Lambda invocation count
- Lambda error rate
- Lambda duration
- DynamoDB read/write capacity
- S3 storage size
- Bedrock API calls
- SNS delivery rate

## Cleanup (Optional)

To remove all resources:

```bash
# Delete Lambda functions
aws lambda delete-function --function-name analyze_crop_image
aws lambda delete-function --function-name process_voice_input
aws lambda delete-function --function-name generate_voice_response
aws lambda delete-function --function-name ingest_market_data
aws lambda delete-function --function-name trigger_alerts

# Delete DynamoDB table
python infrastructure/create_dynamodb_table.py delete

# Delete S3 bucket
python infrastructure/create_s3_bucket.py delete

# Delete API Gateway (manual in console)
```

## Next Steps

1. **Integrate Frontend with API Gateway**
   - Update `frontend/streamlit_app.py` to call real APIs
   - Replace placeholder responses with actual API calls

2. **Add Authentication**
   - Implement AWS Cognito user pools
   - Add login/logout functionality

3. **Implement Voice Recording**
   - Add audio recording widget to Streamlit
   - Integrate with Amazon Transcribe for better transcription

4. **Add Testing**
   - Write unit tests for shared utilities
   - Write integration tests for Lambda functions
   - Implement property-based tests

5. **Production Hardening**
   - Add rate limiting
   - Implement caching
   - Add monitoring dashboards
   - Set up alerts for errors

## Support

For issues or questions:
1. Check CloudWatch logs for errors
2. Review this deployment guide
3. Check AWS service quotas
4. Verify IAM permissions

## Security Best Practices

1. **Never commit `.env` file** to version control
2. **Use IAM roles** instead of access keys where possible
3. **Enable MFA** on AWS account
4. **Restrict S3 bucket** access in production
5. **Use HTTPS** for all API calls
6. **Rotate credentials** regularly
7. **Enable CloudTrail** for audit logging
