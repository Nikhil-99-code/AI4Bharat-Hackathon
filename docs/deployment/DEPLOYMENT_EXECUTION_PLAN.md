# Deployment Execution Plan - Agri-Nexus V1 Platform

## Overview

This document provides a step-by-step execution plan for deploying the Agri-Nexus V1 Platform to AWS. Follow these steps in order to ensure a successful deployment.

---

## Phase 1: Pre-Deployment Checklist

### 1.1 Verify Prerequisites

```bash
# Check Python version (should be 3.9+)
python --version

# Check AWS CLI
aws --version

# Verify AWS credentials
aws sts get-caller-identity

# Check if Bedrock is available in your region
aws bedrock list-foundation-models --region us-east-1
```

### 1.2 Set Environment Variables

Create or update `.env` file:

```bash
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=<your-account-id>
TABLE_NAME=agri-nexus-data
IMAGE_BUCKET=agri-nexus-media-<your-account-id>
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
ENVIRONMENT=development
```

### 1.3 Enable Bedrock Model Access

1. Go to AWS Console → Bedrock → Model access
2. Request access to "Claude 3.5 Sonnet"
3. Wait for approval (usually instant)

---

## Phase 2: Infrastructure Deployment

### 2.1 Deploy DynamoDB Table

```bash
python infrastructure/create_dynamodb_table.py
```

**Expected Output:**
- ✅ Table created: `agri-nexus-data`
- ✅ GSI1, GSI2, GSI3 indexes created
- ✅ Table status: ACTIVE

**Verification:**
```bash
aws dynamodb describe-table --table-name agri-nexus-data --region us-east-1
```

### 2.2 Deploy S3 Bucket

```bash
python infrastructure/create_s3_bucket.py
```

**Expected Output:**
- ✅ Bucket created: `agri-nexus-media-<account-id>`
- ✅ CORS configured
- ✅ Lifecycle policies set

**Verification:**
```bash
aws s3 ls | grep agri-nexus
```

---

## Phase 3: Lambda Deployment

### 3.1 Automated Lambda Deployment

```bash
python infrastructure/deploy_lambdas.py
```

This will deploy all 6 Lambda functions:
1. `analyze_crop_image` (30s, 512MB)
2. `get_diagnosis_history` (15s, 256MB)
3. `process_voice_input` (30s, 512MB)
4. `generate_voice_response` (15s, 256MB)
5. `ingest_market_data` (60s, 512MB)
6. `trigger_alerts` (60s, 512MB)

**Expected Output:**
- ✅ IAM roles created for each function
- ✅ Deployment packages created
- ✅ Functions deployed successfully

**Verification:**
```bash
aws lambda list-functions --region us-east-1 --query 'Functions[?starts_with(FunctionName, `analyze`) || starts_with(FunctionName, `get_`) || starts_with(FunctionName, `process_`) || starts_with(FunctionName, `generate_`) || starts_with(FunctionName, `ingest_`) || starts_with(FunctionName, `trigger_`)].FunctionName'
```

### 3.2 Test Individual Lambda Functions

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

## Phase 4: API Gateway Setup

### 4.1 Create REST API

```bash
# Create API
API_ID=$(aws apigateway create-rest-api \
  --name "AgriNexus API" \
  --description "REST API for Agri-Nexus V1 Platform" \
  --region us-east-1 \
  --query 'id' \
  --output text)

echo "API ID: $API_ID"

# Get root resource ID
ROOT_ID=$(aws apigateway get-resources \
  --rest-api-id $API_ID \
  --region us-east-1 \
  --query 'items[0].id' \
  --output text)

echo "Root Resource ID: $ROOT_ID"
```

### 4.2 Create API Resources

```bash
# Create /diagnose
DIAGNOSE_ID=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $ROOT_ID \
  --path-part diagnose \
  --region us-east-1 \
  --query 'id' \
  --output text)

# Create /history
HISTORY_ID=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $ROOT_ID \
  --path-part history \
  --region us-east-1 \
  --query 'id' \
  --output text)

# Create /history/diagnoses
DIAGNOSES_ID=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $HISTORY_ID \
  --path-part diagnoses \
  --region us-east-1 \
  --query 'id' \
  --output text)

# Create /voice
VOICE_ID=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $ROOT_ID \
  --path-part voice \
  --region us-east-1 \
  --query 'id' \
  --output text)

# Create /voice/process
VOICE_PROCESS_ID=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $VOICE_ID \
  --path-part process \
  --region us-east-1 \
  --query 'id' \
  --output text)

# Create /voice/tts
VOICE_TTS_ID=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $VOICE_ID \
  --path-part tts \
  --region us-east-1 \
  --query 'id' \
  --output text)

# Create /market
MARKET_ID=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $ROOT_ID \
  --path-part market \
  --region us-east-1 \
  --query 'id' \
  --output text)

# Create /market/ingest
MARKET_INGEST_ID=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $MARKET_ID \
  --path-part ingest \
  --region us-east-1 \
  --query 'id' \
  --output text)

echo "Resources created successfully"
```

### 4.3 Create Methods and Integrations

**Important:** Get your AWS Account ID first:
```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=us-east-1
```

#### POST /diagnose → analyze_crop_image

```bash
# Create POST method
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $DIAGNOSE_ID \
  --http-method POST \
  --authorization-type NONE \
  --region $REGION

# Create Lambda integration
aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $DIAGNOSE_ID \
  --http-method POST \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri "arn:aws:apigateway:$REGION:lambda:path/2015-03-31/functions/arn:aws:lambda:$REGION:$ACCOUNT_ID:function:analyze_crop_image/invocations" \
  --region $REGION

# Grant permission
aws lambda add-permission \
  --function-name analyze_crop_image \
  --statement-id apigateway-invoke-diagnose \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:$REGION:$ACCOUNT_ID:$API_ID/*/POST/diagnose" \
  --region $REGION
```

#### GET /history/diagnoses → get_diagnosis_history

```bash
# Create GET method
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $DIAGNOSES_ID \
  --http-method GET \
  --authorization-type NONE \
  --region $REGION

# Create Lambda integration
aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $DIAGNOSES_ID \
  --http-method GET \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri "arn:aws:apigateway:$REGION:lambda:path/2015-03-31/functions/arn:aws:lambda:$REGION:$ACCOUNT_ID:function:get_diagnosis_history/invocations" \
  --region $REGION

# Grant permission
aws lambda add-permission \
  --function-name get_diagnosis_history \
  --statement-id apigateway-invoke-history \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:$REGION:$ACCOUNT_ID:$API_ID/*/GET/history/diagnoses" \
  --region $REGION
```

#### POST /voice/process → process_voice_input

```bash
# Create POST method
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $VOICE_PROCESS_ID \
  --http-method POST \
  --authorization-type NONE \
  --region $REGION

# Create Lambda integration
aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $VOICE_PROCESS_ID \
  --http-method POST \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri "arn:aws:apigateway:$REGION:lambda:path/2015-03-31/functions/arn:aws:lambda:$REGION:$ACCOUNT_ID:function:process_voice_input/invocations" \
  --region $REGION

# Grant permission
aws lambda add-permission \
  --function-name process_voice_input \
  --statement-id apigateway-invoke-voice-process \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:$REGION:$ACCOUNT_ID:$API_ID/*/POST/voice/process" \
  --region $REGION
```

#### POST /voice/tts → generate_voice_response

```bash
# Create POST method
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $VOICE_TTS_ID \
  --http-method POST \
  --authorization-type NONE \
  --region $REGION

# Create Lambda integration
aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $VOICE_TTS_ID \
  --http-method POST \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri "arn:aws:apigateway:$REGION:lambda:path/2015-03-31/functions/arn:aws:lambda:$REGION:$ACCOUNT_ID:function:generate_voice_response/invocations" \
  --region $REGION

# Grant permission
aws lambda add-permission \
  --function-name generate_voice_response \
  --statement-id apigateway-invoke-voice-tts \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:$REGION:$ACCOUNT_ID:$API_ID/*/POST/voice/tts" \
  --region $REGION
```

#### POST /market/ingest → ingest_market_data

```bash
# Create POST method
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $MARKET_INGEST_ID \
  --http-method POST \
  --authorization-type NONE \
  --region $REGION

# Create Lambda integration
aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $MARKET_INGEST_ID \
  --http-method POST \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri "arn:aws:apigateway:$REGION:lambda:path/2015-03-31/functions/arn:aws:lambda:$REGION:$ACCOUNT_ID:function:ingest_market_data/invocations" \
  --region $REGION

# Grant permission
aws lambda add-permission \
  --function-name ingest_market_data \
  --statement-id apigateway-invoke-market-ingest \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:$REGION:$ACCOUNT_ID:$API_ID/*/POST/market/ingest" \
  --region $REGION
```

### 4.4 Deploy API

```bash
aws apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name prod \
  --region $REGION

# Get API Gateway URL
API_URL="https://$API_ID.execute-api.$REGION.amazonaws.com/prod"
echo "API Gateway URL: $API_URL"
```

### 4.5 Update Environment Configuration

Add to your `.env` file:
```bash
API_GATEWAY_URL=https://<API_ID>.execute-api.us-east-1.amazonaws.com/prod
```

---

## Phase 5: Integration Testing

### 5.1 Test API Endpoints

```bash
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

### 5.2 Run Integration Tests

```bash
# Run integration test suite
python tests/test_integration.py

# Run end-to-end tests
python tests/test_e2e_dr_crop.py
python tests/test_e2e_sahayak.py
python tests/test_e2e_alerts.py
```

---

## Phase 6: Frontend Deployment

### 6.1 Update Frontend Configuration

Ensure `.env` has the API Gateway URL:
```bash
API_GATEWAY_URL=https://<API_ID>.execute-api.us-east-1.amazonaws.com/prod
```

### 6.2 Run Streamlit Application

```bash
streamlit run frontend/streamlit_app.py
```

### 6.3 Test All Features

1. **Dr. Crop Tab**
   - Upload crop image
   - Verify diagnosis appears
   - Check diagnosis history

2. **Sahayak Tab**
   - Submit voice question
   - Verify response appears
   - Test audio playback

3. **Alerts Tab**
   - Create price alert
   - Simulate price change
   - Verify alert triggers

---

## Phase 7: Monitoring Setup

### 7.1 Enable CloudWatch Logs

```bash
# Enable API Gateway logging
aws apigateway update-stage \
  --rest-api-id $API_ID \
  --stage-name prod \
  --patch-operations op=replace,path=/*/logging/loglevel,value=INFO \
  --region $REGION
```

### 7.2 View Lambda Logs

```bash
# View logs for each function
aws logs tail /aws/lambda/analyze_crop_image --follow --region $REGION
aws logs tail /aws/lambda/process_voice_input --follow --region $REGION
aws logs tail /aws/lambda/ingest_market_data --follow --region $REGION
```

---

## Troubleshooting

### Common Issues

**1. Lambda timeout errors**
```bash
# Increase timeout
aws lambda update-function-configuration \
  --function-name analyze_crop_image \
  --timeout 60 \
  --region $REGION
```

**2. Bedrock access denied**
- Verify Bedrock model access is enabled
- Check IAM role has bedrock:InvokeModel permission

**3. CORS errors**
- Ensure OPTIONS method is configured for each resource
- Verify Access-Control-Allow-Origin header is set

**4. DynamoDB access denied**
- Check IAM role has DynamoDB permissions
- Verify table name matches environment variable

---

## Deployment Checklist

- [ ] Prerequisites verified
- [ ] Environment variables configured
- [ ] Bedrock model access enabled
- [ ] DynamoDB table created
- [ ] S3 bucket created
- [ ] Lambda functions deployed
- [ ] IAM roles configured
- [ ] API Gateway created
- [ ] API endpoints configured
- [ ] API deployed to prod stage
- [ ] Integration tests passed
- [ ] Frontend configured
- [ ] End-to-end testing completed
- [ ] CloudWatch monitoring enabled

---

## Next Steps

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

---

## Cost Monitoring

Monitor costs in AWS Cost Explorer:
- Lambda invocations
- Bedrock API calls
- DynamoDB read/write units
- S3 storage and requests
- API Gateway requests

Expected monthly cost for development: $5-10
Expected monthly cost for production: $80-165

---

## Support Resources

- AWS Lambda Documentation: https://docs.aws.amazon.com/lambda/
- API Gateway Documentation: https://docs.aws.amazon.com/apigateway/
- Bedrock Documentation: https://docs.aws.amazon.com/bedrock/
- DynamoDB Documentation: https://docs.aws.amazon.com/dynamodb/

