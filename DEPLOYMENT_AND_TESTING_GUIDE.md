# Agri-Nexus V1 Platform - Deployment and Testing Guide

## Overview

This guide provides step-by-step instructions for deploying the Agri-Nexus V1 Platform to AWS and running comprehensive integration tests. Follow these steps in order for a successful deployment.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Phase 1: Infrastructure Deployment](#phase-1-infrastructure-deployment)
3. [Phase 2: Lambda Deployment](#phase-2-lambda-deployment)
4. [Phase 3: API Gateway Setup](#phase-3-api-gateway-setup)
5. [Phase 4: Integration Testing](#phase-4-integration-testing)
6. [Phase 5: Frontend Configuration](#phase-5-frontend-configuration)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### 1. AWS Account Setup

```bash
# Verify AWS CLI is installed
aws --version

# Configure AWS credentials
aws configure

# Verify credentials
aws sts get-caller-identity
```

### 2. Enable Bedrock Model Access

1. Go to AWS Console → Bedrock → Model access
2. Request access to "Claude 3.5 Sonnet"
3. Wait for approval (usually instant)

### 3. Install Python Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create `.env` file:

```bash
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=<your-account-id>
TABLE_NAME=agri-nexus-data
IMAGE_BUCKET=agri-nexus-media-<your-account-id>
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
ENVIRONMENT=development
```

---

## Phase 1: Infrastructure Deployment

### Step 1.1: Deploy DynamoDB Table

```bash
python infrastructure/create_dynamodb_table.py
```

**Expected Output:**
```
✓ DynamoDB table created: agri-nexus-data
✓ GSI1, GSI2, GSI3 indexes created
✓ Table status: ACTIVE
```

**Verification:**
```bash
aws dynamodb describe-table --table-name agri-nexus-data --region us-east-1
```

### Step 1.2: Deploy S3 Bucket

```bash
python infrastructure/create_s3_bucket.py
```

**Expected Output:**
```
✓ S3 bucket created: agri-nexus-media-<account-id>
✓ CORS configured
✓ Lifecycle policies set
```

**Verification:**
```bash
aws s3 ls | grep agri-nexus
```

---

## Phase 2: Lambda Deployment

### Step 2.1: Deploy All Lambda Functions

```bash
python infrastructure/deploy_lambdas.py
```

This will deploy 6 Lambda functions:
- `analyze_crop_image` (30s, 512MB)
- `get_diagnosis_history` (15s, 256MB)
- `process_voice_input` (30s, 512MB)
- `generate_voice_response` (15s, 256MB)
- `ingest_market_data` (60s, 512MB)
- `trigger_alerts` (60s, 512MB)

**Expected Output:**
```
📦 Creating package for analyze_crop_image...
✅ Package created: analyze_crop_image.zip
🆕 Creating Lambda function: analyze_crop_image
✅ Function created successfully
...
✅ Lambda deployment complete!
```

**Verification:**
```bash
aws lambda list-functions --region us-east-1 --query 'Functions[].FunctionName'
```

### Step 2.2: Test Individual Lambda Functions

```bash
# Test analyze_crop_image
aws lambda invoke \
  --function-name analyze_crop_image \
  --payload '{"user_id":"test_user","image_data":"","language":"en"}' \
  --region us-east-1 \
  response.json

cat response.json
```

---

## Phase 3: API Gateway Setup

### Option A: Automated Deployment (Recommended)

```bash
# Make script executable (Linux/Mac)
chmod +x deploy_api_gateway.sh

# Run deployment script
./deploy_api_gateway.sh
```

**Expected Output:**
```
========================================
✓ API Gateway Deployment Complete!
========================================

API Gateway URL:
https://abc123xyz.execute-api.us-east-1.amazonaws.com/prod

Available Endpoints:
  POST   https://abc123xyz.execute-api.us-east-1.amazonaws.com/prod/diagnose
  GET    https://abc123xyz.execute-api.us-east-1.amazonaws.com/prod/history/diagnoses
  POST   https://abc123xyz.execute-api.us-east-1.amazonaws.com/prod/voice/process
  POST   https://abc123xyz.execute-api.us-east-1.amazonaws.com/prod/voice/tts
  POST   https://abc123xyz.execute-api.us-east-1.amazonaws.com/prod/market/ingest
```

### Option B: Manual Deployment

Follow the detailed steps in `LAMBDA_API_GATEWAY_SETUP.md`

### Step 3.1: Update Environment Configuration

Add the API Gateway URL to your `.env` file:

```bash
API_GATEWAY_URL=https://<API_ID>.execute-api.us-east-1.amazonaws.com/prod
```

---

## Phase 4: Integration Testing

### Step 4.1: Test API Endpoints

```bash
# Set API URL
export API_URL="https://<API_ID>.execute-api.us-east-1.amazonaws.com/prod"

# Test POST /diagnose
curl -X POST \
  $API_URL/diagnose \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test_user","image_data":"","language":"en"}'

# Test GET /history/diagnoses
curl -X GET \
  "$API_URL/history/diagnoses?user_id=test_user&limit=20"

# Test POST /voice/process
curl -X POST \
  $API_URL/voice/process \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test_user","audio_data":"","language":"en"}'

# Test POST /market/ingest
curl -X POST \
  $API_URL/market/ingest \
  -H "Content-Type: application/json" \
  -d '{"crop_type":"wheat","location":"delhi","price":2500,"timestamp":"2024-01-15T10:00:00Z","simulation":true}'
```

### Step 4.2: Run Integration Test Suite

```bash
# Run all integration tests
python tests/test_integration.py
```

**Expected Output:**
```
========================================
AGRI-NEXUS V1 PLATFORM - INTEGRATION TEST SUITE
========================================

API Base URL: https://abc123xyz.execute-api.us-east-1.amazonaws.com/prod
Test User ID: test_user_integration

tests/test_integration.py::TestDrCropIntegration::test_diagnose_endpoint_exists PASSED
tests/test_integration.py::TestDrCropIntegration::test_diagnose_with_valid_image PASSED
tests/test_integration.py::TestDrCropIntegration::test_diagnosis_history_retrieval PASSED
...
======================== 20 passed in 45.23s ========================
```

### Step 4.3: Run End-to-End Tests

#### Test Dr. Crop Feature

```bash
python tests/test_e2e_dr_crop.py
```

**Expected Output:**
```
========================================
DR. CROP FEATURE - END-TO-END TEST SUITE
========================================

[TEST 1] Uploading and diagnosing valid crop image...
Response status: 200
✅ Diagnosis successful:
   Disease: Late Blight
   Confidence: 87.5%
   Treatment: Apply copper-based fungicide...

[TEST 2] Retrieving diagnosis history...
✅ Retrieved 5 diagnoses

[TEST 3] Verifying diagnosis persistence...
✅ Diagnosis persisted and retrieved successfully

======================== 8 passed in 120.45s ========================
```

#### Test Sahayak Feature

```bash
python tests/test_e2e_sahayak.py
```

**Expected Output:**
```
========================================
SAHAYAK VOICE ASSISTANT - END-TO-END TEST SUITE
========================================

[TEST 1] Testing voice process endpoint accessibility...
✅ Endpoint accessible (status: 200)

[TEST 2] Testing voice input processing...
✅ Voice processing successful:
   Interaction ID: int_123456
   Transcript: What fertilizer should I use?
   Response: For wheat cultivation, use NPK fertilizer...

[TEST 3] Testing text-to-speech conversion...
✅ TTS conversion successful:
   Audio data length: 12345 characters
   Duration: 5.2 seconds

======================== 10 passed in 95.32s ========================
```

#### Test Alerts Feature

```bash
python tests/test_e2e_alerts.py
```

**Expected Output:**
```
========================================
PRICE ALERTS FEATURE - END-TO-END TEST SUITE
========================================

[TEST 1] Testing market ingest endpoint accessibility...
✅ Endpoint accessible (status: 200)

[TEST 2] Testing market data ingestion...
✅ Market data ingested successfully:
   Market Data ID: mkt_123456
   Alerts Triggered: 0

[TEST 4] Testing price alert simulation...
✅ Price simulation successful:
   Price: ₹2600
   Alerts Triggered: 2
   🔔 2 alert(s) were triggered!

======================== 12 passed in 78.56s ========================
```

---

## Phase 5: Frontend Configuration

### Step 5.1: Update Frontend Configuration

Ensure `.env` has the API Gateway URL:

```bash
API_GATEWAY_URL=https://<API_ID>.execute-api.us-east-1.amazonaws.com/prod
```

### Step 5.2: Run Streamlit Application

```bash
streamlit run frontend/streamlit_app.py
```

The application will be available at `http://localhost:8501`

### Step 5.3: Test All Features in UI

#### Test 1: Dr. Crop Tab

1. Navigate to "Dr. Crop" tab
2. Upload a crop image (JPEG/PNG, min 224x224)
3. Click "Analyze Image"
4. Verify diagnosis appears with:
   - Disease name
   - Confidence percentage
   - Treatment recommendation
5. Check diagnosis history section

#### Test 2: Sahayak Tab

1. Navigate to "Sahayak" tab
2. Type a question (e.g., "What fertilizer for wheat?")
3. Click "Submit Question"
4. Verify response appears with:
   - Transcribed question
   - Text response
   - Audio playback (if TTS enabled)

#### Test 3: Alerts Tab

1. Navigate to "Alerts" tab
2. Configure a price alert:
   - Crop: Wheat
   - Location: Delhi
   - Target Price: 2500
   - Phone: +919876543210
3. Click "Create Alert"
4. Click "Simulate Price Change"
5. Verify alert triggers (check phone for SMS if SNS configured)

---

## Troubleshooting

### Issue 1: Lambda Timeout Errors

**Symptom:** Lambda functions timing out

**Solution:**
```bash
# Increase timeout for specific function
aws lambda update-function-configuration \
  --function-name analyze_crop_image \
  --timeout 60 \
  --region us-east-1
```

### Issue 2: Bedrock Access Denied

**Symptom:** "Access denied" errors when calling Bedrock

**Solution:**
1. Verify Bedrock model access is enabled in AWS Console
2. Check IAM role has `bedrock:InvokeModel` permission
3. Verify model ID is correct: `anthropic.claude-3-5-sonnet-20241022-v2:0`

### Issue 3: CORS Errors in Browser

**Symptom:** CORS errors when calling API from Streamlit

**Solution:**
1. Ensure OPTIONS method is configured for each resource
2. Verify `Access-Control-Allow-Origin: *` header is set
3. Re-deploy API Gateway after CORS changes

### Issue 4: DynamoDB Access Denied

**Symptom:** "Access denied" errors when accessing DynamoDB

**Solution:**
1. Check IAM role has DynamoDB permissions
2. Verify table name matches environment variable
3. Ensure GSI indexes are created

### Issue 5: API Gateway 404 Errors

**Symptom:** 404 errors when calling API endpoints

**Solution:**
1. Verify API is deployed to correct stage
2. Check endpoint paths match exactly
3. Ensure Lambda permissions are granted to API Gateway

### View Lambda Logs

```bash
# View logs for specific function
aws logs tail /aws/lambda/analyze_crop_image --follow --region us-east-1
```

### View API Gateway Logs

```bash
# Enable CloudWatch logging
aws apigateway update-stage \
  --rest-api-id <API_ID> \
  --stage-name prod \
  --patch-operations op=replace,path=/*/logging/loglevel,value=INFO \
  --region us-east-1
```

---

## Deployment Checklist

Use this checklist to track your deployment progress:

- [ ] Prerequisites verified
  - [ ] AWS CLI installed and configured
  - [ ] Python 3.9+ installed
  - [ ] Bedrock model access enabled
  - [ ] Environment variables configured

- [ ] Infrastructure deployed
  - [ ] DynamoDB table created
  - [ ] S3 bucket created
  - [ ] IAM roles configured

- [ ] Lambda functions deployed
  - [ ] analyze_crop_image
  - [ ] get_diagnosis_history
  - [ ] process_voice_input
  - [ ] generate_voice_response
  - [ ] ingest_market_data
  - [ ] trigger_alerts

- [ ] API Gateway configured
  - [ ] REST API created
  - [ ] Resources created
  - [ ] Methods configured
  - [ ] Lambda integrations set up
  - [ ] API deployed to prod stage

- [ ] Testing completed
  - [ ] Individual Lambda functions tested
  - [ ] API endpoints tested with curl
  - [ ] Integration test suite passed
  - [ ] Dr. Crop E2E tests passed
  - [ ] Sahayak E2E tests passed
  - [ ] Alerts E2E tests passed

- [ ] Frontend configured
  - [ ] API Gateway URL updated in .env
  - [ ] Streamlit app runs successfully
  - [ ] All three tabs functional
  - [ ] End-to-end user flows tested

- [ ] Monitoring enabled
  - [ ] CloudWatch logs configured
  - [ ] CloudWatch metrics enabled
  - [ ] Alarms set up (optional)

---

## Cost Monitoring

Monitor your AWS costs in Cost Explorer:

### Expected Costs (Development)

- **Lambda**: ~$0-1/month (free tier covers most testing)
- **DynamoDB**: ~$1-2/month (5 RCU/WCU)
- **S3**: ~$0.50/month (< 1GB storage)
- **Bedrock**: ~$3-5/month (Claude 3.5 Sonnet usage)
- **SNS**: ~$0.10/month (100 SMS in sandbox)
- **API Gateway**: ~$0-1/month (free tier: 1M requests)

**Total**: ~$5-10/month for development

### Expected Costs (Production)

- **Lambda**: ~$5-10/month (1M requests)
- **DynamoDB**: ~$10-20/month (on-demand pricing)
- **S3**: ~$5-10/month (10GB storage + requests)
- **Bedrock**: ~$50-100/month (depends on usage)
- **SNS**: ~$10-20/month (1000 SMS)
- **API Gateway**: ~$3-5/month (1M requests)

**Total**: ~$80-165/month for moderate production use

---

## Next Steps

After successful deployment:

1. **Production Hardening**
   - Add authentication (AWS Cognito)
   - Implement rate limiting
   - Add caching layer
   - Set up CloudWatch alarms

2. **Performance Optimization**
   - Enable API Gateway caching
   - Optimize Lambda memory allocation
   - Implement DynamoDB auto-scaling

3. **Security Enhancements**
   - Enable AWS WAF
   - Implement API key authentication
   - Add request validation
   - Enable CloudTrail logging

4. **Feature Enhancements**
   - Add real voice recording
   - Implement real-time market data feeds
   - Add user authentication
   - Create admin dashboard

---

## Support Resources

- **AWS Lambda Documentation**: https://docs.aws.amazon.com/lambda/
- **API Gateway Documentation**: https://docs.aws.amazon.com/apigateway/
- **Bedrock Documentation**: https://docs.aws.amazon.com/bedrock/
- **DynamoDB Documentation**: https://docs.aws.amazon.com/dynamodb/
- **Project Documentation**: See `README.md`, `AWS_SERVICES_OVERVIEW.md`, `LAMBDA_API_GATEWAY_SETUP.md`

---

## Quick Reference Commands

```bash
# Deploy infrastructure
python infrastructure/create_dynamodb_table.py
python infrastructure/create_s3_bucket.py

# Deploy Lambda functions
python infrastructure/deploy_lambdas.py

# Deploy API Gateway
./deploy_api_gateway.sh

# Run tests
python tests/test_integration.py
python tests/test_e2e_dr_crop.py
python tests/test_e2e_sahayak.py
python tests/test_e2e_alerts.py

# Run Streamlit app
streamlit run frontend/streamlit_app.py

# View logs
aws logs tail /aws/lambda/analyze_crop_image --follow --region us-east-1

# List Lambda functions
aws lambda list-functions --region us-east-1

# Describe DynamoDB table
aws dynamodb describe-table --table-name agri-nexus-data --region us-east-1

# List S3 buckets
aws s3 ls | grep agri-nexus
```

---

**Good luck with your deployment! 🚀**

