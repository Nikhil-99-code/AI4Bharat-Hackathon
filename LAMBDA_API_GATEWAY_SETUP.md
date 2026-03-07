# Lambda and API Gateway Setup Guide

## Prerequisites

Before starting, ensure you have:

1. **AWS Account** with appropriate permissions
2. **AWS CLI** installed and configured
   ```bash
   aws --version
   aws configure
   ```
3. **Python 3.9+** installed
4. **Bedrock Access** enabled in your AWS account
5. **IAM Permissions** to create Lambda, API Gateway, IAM roles

---

## Part 1: Prepare Lambda Deployment Packages

### Step 1.1: Create Lambda Deployment Directory

```bash
mkdir lambda-packages
cd lambda-packages
```

### Step 1.2: Package Each Lambda Function

We need to create deployment packages for each Lambda function with dependencies.

#### Package 1: analyze_crop_image

```bash
# Create directory
mkdir analyze_crop_image
cd analyze_crop_image

# Copy handler
cp ../../backend/analyze_crop_image/handler.py .

# Copy shared modules
mkdir shared
cp ../../shared/*.py shared/

# Install dependencies
pip install --target . boto3 pillow

# Create deployment package
zip -r ../analyze_crop_image.zip .

cd ..
```

#### Package 2: get_diagnosis_history

```bash
mkdir get_diagnosis_history
cd get_diagnosis_history

cp ../../backend/get_diagnosis_history/handler.py .
mkdir shared
cp ../../shared/*.py shared/

pip install --target . boto3

zip -r ../get_diagnosis_history.zip .

cd ..
```

#### Package 3: process_voice_input

```bash
mkdir process_voice_input
cd process_voice_input

cp ../../backend/process_voice_input/handler.py .
mkdir shared
cp ../../shared/*.py shared/

pip install --target . boto3

zip -r ../process_voice_input.zip .

cd ..
```

#### Package 4: generate_voice_response

```bash
mkdir generate_voice_response
cd generate_voice_response

cp ../../backend/generate_voice_response/handler.py .
mkdir shared
cp ../../shared/*.py shared/

pip install --target . boto3

zip -r ../generate_voice_response.zip .

cd ..
```

#### Package 5: ingest_market_data

```bash
mkdir ingest_market_data
cd ingest_market_data

cp ../../backend/ingest_market_data/handler.py .
mkdir shared
cp ../../shared/*.py shared/

pip install --target . boto3

zip -r ../ingest_market_data.zip .

cd ..
```

#### Package 6: trigger_alerts

```bash
mkdir trigger_alerts
cd trigger_alerts

cp ../../backend/trigger_alerts/handler.py .
mkdir shared
cp ../../shared/*.py shared/

pip install --target . boto3

zip -r ../trigger_alerts.zip .

cd ..
```

---

## Part 2: Create IAM Execution Role

### Step 2.1: Create IAM Policy Document

Create a file `lambda-trust-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

### Step 2.2: Create IAM Role

```bash
aws iam create-role \
  --role-name AgriNexusLambdaExecutionRole \
  --assume-role-policy-document file://lambda-trust-policy.json
```

### Step 2.3: Create Custom Policy for Lambda

Create a file `lambda-permissions-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:Query",
        "dynamodb:Scan",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem"
      ],
      "Resource": [
        "arn:aws:dynamodb:*:*:table/agri-nexus-data",
        "arn:aws:dynamodb:*:*:table/agri-nexus-data/index/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::agri-nexus-media-*/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "arn:aws:bedrock:*::foundation-model/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "sns:Publish"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "lambda:InvokeFunction"
      ],
      "Resource": "arn:aws:lambda:*:*:function:trigger_alerts"
    }
  ]
}
```

### Step 2.4: Attach Policy to Role

```bash
aws iam put-role-policy \
  --role-name AgriNexusLambdaExecutionRole \
  --policy-name AgriNexusLambdaPermissions \
  --policy-document file://lambda-permissions-policy.json
```

### Step 2.5: Get Role ARN (save this for later)

```bash
aws iam get-role --role-name AgriNexusLambdaExecutionRole --query 'Role.Arn' --output text
```

Save the output (e.g., `arn:aws:iam::123456789012:role/AgriNexusLambdaExecutionRole`)

---

## Part 3: Deploy Lambda Functions

Replace `<ROLE_ARN>` with the ARN from Step 2.5 and `<REGION>` with your AWS region (e.g., `ap-south-1`).

### Step 3.1: Deploy analyze_crop_image

```bash
aws lambda create-function \
  --function-name analyze_crop_image \
  --runtime python3.9 \
  --role <ROLE_ARN> \
  --handler handler.lambda_handler \
  --zip-file fileb://analyze_crop_image.zip \
  --timeout 30 \
  --memory-size 512 \
  --environment Variables="{
    TABLE_NAME=agri-nexus-data,
    IMAGE_BUCKET=agri-nexus-media-<ACCOUNT_ID>,
    BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20240620-v1:0,
    AWS_REGION=<REGION>
  }" \
  --region <REGION>
```

### Step 3.2: Deploy get_diagnosis_history

```bash
aws lambda create-function \
  --function-name get_diagnosis_history \
  --runtime python3.9 \
  --role <ROLE_ARN> \
  --handler handler.lambda_handler \
  --zip-file fileb://get_diagnosis_history.zip \
  --timeout 15 \
  --memory-size 256 \
  --environment Variables="{
    TABLE_NAME=agri-nexus-data,
    AWS_REGION=<REGION>
  }" \
  --region <REGION>
```

### Step 3.3: Deploy process_voice_input

```bash
aws lambda create-function \
  --function-name process_voice_input \
  --runtime python3.9 \
  --role <ROLE_ARN> \
  --handler handler.lambda_handler \
  --zip-file fileb://process_voice_input.zip \
  --timeout 30 \
  --memory-size 512 \
  --environment Variables="{
    TABLE_NAME=agri-nexus-data,
    BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20240620-v1:0,
    AWS_REGION=<REGION>
  }" \
  --region <REGION>
```

### Step 3.4: Deploy generate_voice_response

```bash
aws lambda create-function \
  --function-name generate_voice_response \
  --runtime python3.9 \
  --role <ROLE_ARN> \
  --handler handler.lambda_handler \
  --zip-file fileb://generate_voice_response.zip \
  --timeout 15 \
  --memory-size 256 \
  --environment Variables="{
    BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20240620-v1:0,
    AWS_REGION=<REGION>
  }" \
  --region <REGION>
```

### Step 3.5: Deploy ingest_market_data

```bash
aws lambda create-function \
  --function-name ingest_market_data \
  --runtime python3.9 \
  --role <ROLE_ARN> \
  --handler handler.lambda_handler \
  --zip-file fileb://ingest_market_data.zip \
  --timeout 60 \
  --memory-size 512 \
  --environment Variables="{
    TABLE_NAME=agri-nexus-data,
    TRIGGER_ALERTS_FUNCTION=trigger_alerts,
    AWS_REGION=<REGION>
  }" \
  --region <REGION>
```

### Step 3.6: Deploy trigger_alerts

```bash
aws lambda create-function \
  --function-name trigger_alerts \
  --runtime python3.9 \
  --role <ROLE_ARN> \
  --handler handler.lambda_handler \
  --zip-file fileb://trigger_alerts.zip \
  --timeout 60 \
  --memory-size 512 \
  --environment Variables="{
    TABLE_NAME=agri-nexus-data,
    AWS_REGION=<REGION>
  }" \
  --region <REGION>
```

### Step 3.7: Verify Lambda Functions

```bash
aws lambda list-functions --region <REGION> --query 'Functions[?starts_with(FunctionName, `analyze`) || starts_with(FunctionName, `get_`) || starts_with(FunctionName, `process_`) || starts_with(FunctionName, `generate_`) || starts_with(FunctionName, `ingest_`) || starts_with(FunctionName, `trigger_`)].FunctionName'
```

---

## Part 4: Create API Gateway REST API

### Step 4.1: Create REST API

```bash
aws apigateway create-rest-api \
  --name "AgriNexus API" \
  --description "REST API for Agri-Nexus V1 Platform" \
  --region <REGION>
```

Save the `id` from the output (e.g., `abc123xyz`)

```bash
export API_ID=<your-api-id>
```

### Step 4.2: Get Root Resource ID

```bash
aws apigateway get-resources \
  --rest-api-id $API_ID \
  --region <REGION>
```

Save the root resource `id`:

```bash
export ROOT_RESOURCE_ID=<root-resource-id>
```

### Step 4.3: Create Resources

#### Create /diagnose resource

```bash
aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $ROOT_RESOURCE_ID \
  --path-part diagnose \
  --region <REGION>
```

Save the resource `id`:
```bash
export DIAGNOSE_RESOURCE_ID=<diagnose-resource-id>
```

#### Create /history resource

```bash
aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $ROOT_RESOURCE_ID \
  --path-part history \
  --region <REGION>
```

Save the resource `id`:
```bash
export HISTORY_RESOURCE_ID=<history-resource-id>
```

#### Create /history/diagnoses resource

```bash
aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $HISTORY_RESOURCE_ID \
  --path-part diagnoses \
  --region <REGION>
```

Save the resource `id`:
```bash
export DIAGNOSES_RESOURCE_ID=<diagnoses-resource-id>
```

#### Create /voice resource

```bash
aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $ROOT_RESOURCE_ID \
  --path-part voice \
  --region <REGION>
```

Save the resource `id`:
```bash
export VOICE_RESOURCE_ID=<voice-resource-id>
```

#### Create /voice/process resource

```bash
aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $VOICE_RESOURCE_ID \
  --path-part process \
  --region <REGION>
```

Save the resource `id`:
```bash
export VOICE_PROCESS_RESOURCE_ID=<voice-process-resource-id>
```

#### Create /voice/tts resource

```bash
aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $VOICE_RESOURCE_ID \
  --path-part tts \
  --region <REGION>
```

Save the resource `id`:
```bash
export VOICE_TTS_RESOURCE_ID=<voice-tts-resource-id>
```

#### Create /market resource

```bash
aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $ROOT_RESOURCE_ID \
  --path-part market \
  --region <REGION>
```

Save the resource `id`:
```bash
export MARKET_RESOURCE_ID=<market-resource-id>
```

#### Create /market/ingest resource

```bash
aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $MARKET_RESOURCE_ID \
  --path-part ingest \
  --region <REGION>
```

Save the resource `id`:
```bash
export MARKET_INGEST_RESOURCE_ID=<market-ingest-resource-id>
```

### Step 4.4: Create Methods and Integrations

Get your AWS Account ID:
```bash
export ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
```

#### POST /diagnose → analyze_crop_image

```bash
# Create POST method
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $DIAGNOSE_RESOURCE_ID \
  --http-method POST \
  --authorization-type NONE \
  --region <REGION>

# Create Lambda integration
aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $DIAGNOSE_RESOURCE_ID \
  --http-method POST \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri "arn:aws:apigateway:<REGION>:lambda:path/2015-03-31/functions/arn:aws:lambda:<REGION>:$ACCOUNT_ID:function:analyze_crop_image/invocations" \
  --region <REGION>

# Grant API Gateway permission to invoke Lambda
aws lambda add-permission \
  --function-name analyze_crop_image \
  --statement-id apigateway-invoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:<REGION>:$ACCOUNT_ID:$API_ID/*/POST/diagnose" \
  --region <REGION>
```

#### GET /history/diagnoses → get_diagnosis_history

```bash
# Create GET method
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $DIAGNOSES_RESOURCE_ID \
  --http-method GET \
  --authorization-type NONE \
  --request-parameters method.request.querystring.user_id=true,method.request.querystring.limit=false \
  --region <REGION>

# Create Lambda integration
aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $DIAGNOSES_RESOURCE_ID \
  --http-method GET \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri "arn:aws:apigateway:<REGION>:lambda:path/2015-03-31/functions/arn:aws:lambda:<REGION>:$ACCOUNT_ID:function:get_diagnosis_history/invocations" \
  --region <REGION>

# Grant permission
aws lambda add-permission \
  --function-name get_diagnosis_history \
  --statement-id apigateway-invoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:<REGION>:$ACCOUNT_ID:$API_ID/*/GET/history/diagnoses" \
  --region <REGION>
```

#### POST /voice/process → process_voice_input

```bash
# Create POST method
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $VOICE_PROCESS_RESOURCE_ID \
  --http-method POST \
  --authorization-type NONE \
  --region <REGION>

# Create Lambda integration
aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $VOICE_PROCESS_RESOURCE_ID \
  --http-method POST \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri "arn:aws:apigateway:<REGION>:lambda:path/2015-03-31/functions/arn:aws:lambda:<REGION>:$ACCOUNT_ID:function:process_voice_input/invocations" \
  --region <REGION>

# Grant permission
aws lambda add-permission \
  --function-name process_voice_input \
  --statement-id apigateway-invoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:<REGION>:$ACCOUNT_ID:$API_ID/*/POST/voice/process" \
  --region <REGION>
```

#### POST /voice/tts → generate_voice_response

```bash
# Create POST method
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $VOICE_TTS_RESOURCE_ID \
  --http-method POST \
  --authorization-type NONE \
  --region <REGION>

# Create Lambda integration
aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $VOICE_TTS_RESOURCE_ID \
  --http-method POST \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri "arn:aws:apigateway:<REGION>:lambda:path/2015-03-31/functions/arn:aws:lambda:<REGION>:$ACCOUNT_ID:function:generate_voice_response/invocations" \
  --region <REGION>

# Grant permission
aws lambda add-permission \
  --function-name generate_voice_response \
  --statement-id apigateway-invoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:<REGION>:$ACCOUNT_ID:$API_ID/*/POST/voice/tts" \
  --region <REGION>
```

#### POST /market/ingest → ingest_market_data

```bash
# Create POST method
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $MARKET_INGEST_RESOURCE_ID \
  --http-method POST \
  --authorization-type NONE \
  --region <REGION>

# Create Lambda integration
aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $MARKET_INGEST_RESOURCE_ID \
  --http-method POST \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri "arn:aws:apigateway:<REGION>:lambda:path/2015-03-31/functions/arn:aws:lambda:<REGION>:$ACCOUNT_ID:function:ingest_market_data/invocations" \
  --region <REGION>

# Grant permission
aws lambda add-permission \
  --function-name ingest_market_data \
  --statement-id apigateway-invoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:<REGION>:$ACCOUNT_ID:$API_ID/*/POST/market/ingest" \
  --region <REGION>
```

### Step 4.5: Enable CORS

For each resource, enable CORS:

```bash
# Example for /diagnose
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $DIAGNOSE_RESOURCE_ID \
  --http-method OPTIONS \
  --authorization-type NONE \
  --region <REGION>

aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $DIAGNOSE_RESOURCE_ID \
  --http-method OPTIONS \
  --type MOCK \
  --request-templates '{"application/json": "{\"statusCode\": 200}"}' \
  --region <REGION>

aws apigateway put-method-response \
  --rest-api-id $API_ID \
  --resource-id $DIAGNOSE_RESOURCE_ID \
  --http-method OPTIONS \
  --status-code 200 \
  --response-parameters method.response.header.Access-Control-Allow-Headers=true,method.response.header.Access-Control-Allow-Methods=true,method.response.header.Access-Control-Allow-Origin=true \
  --region <REGION>

aws apigateway put-integration-response \
  --rest-api-id $API_ID \
  --resource-id $DIAGNOSE_RESOURCE_ID \
  --http-method OPTIONS \
  --status-code 200 \
  --response-parameters '{"method.response.header.Access-Control-Allow-Headers":"'"'"'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"'"'","method.response.header.Access-Control-Allow-Methods":"'"'"'POST,OPTIONS'"'"'","method.response.header.Access-Control-Allow-Origin":"'"'"'*'"'"'"}' \
  --region <REGION>
```

Repeat for all other resources (diagnoses, voice/process, voice/tts, market/ingest).

### Step 4.6: Deploy API

```bash
aws apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name prod \
  --region <REGION>
```

### Step 4.7: Get API Gateway URL

```bash
echo "https://$API_ID.execute-api.<REGION>.amazonaws.com/prod"
```

Save this URL - you'll need it for the Streamlit app configuration!

---

## Part 5: Update Streamlit Configuration

Create or update `.env` file:

```bash
AWS_REGION=<REGION>
TABLE_NAME=agri-nexus-data
IMAGE_BUCKET=agri-nexus-media-<ACCOUNT_ID>
API_GATEWAY_URL=https://<API_ID>.execute-api.<REGION>.amazonaws.com/prod
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20240620-v1:0
```

---

## Part 6: Test the Deployment

### Test Lambda Functions Directly

```bash
# Test analyze_crop_image
aws lambda invoke \
  --function-name analyze_crop_image \
  --payload '{"user_id":"test_user","image_data":"base64_encoded_image","language":"en"}' \
  --region <REGION> \
  response.json

cat response.json
```

### Test API Gateway Endpoints

```bash
# Test POST /diagnose
curl -X POST \
  https://<API_ID>.execute-api.<REGION>.amazonaws.com/prod/diagnose \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test_user","image_data":"base64_encoded_image","language":"en"}'

# Test GET /history/diagnoses
curl -X GET \
  "https://<API_ID>.execute-api.<REGION>.amazonaws.com/prod/history/diagnoses?user_id=test_user&limit=20"
```

---

## Part 7: Monitor and Debug

### View Lambda Logs

```bash
aws logs tail /aws/lambda/analyze_crop_image --follow --region <REGION>
```

### View API Gateway Logs

Enable CloudWatch logging for API Gateway:

```bash
aws apigateway update-stage \
  --rest-api-id $API_ID \
  --stage-name prod \
  --patch-operations op=replace,path=/*/logging/loglevel,value=INFO \
  --region <REGION>
```

---

## Troubleshooting

### Common Issues:

1. **Lambda timeout**: Increase timeout in Lambda configuration
2. **Permission denied**: Check IAM role has correct permissions
3. **CORS errors**: Verify CORS is enabled for all methods
4. **Bedrock access denied**: Ensure Bedrock is enabled in your account
5. **DynamoDB not found**: Verify table name matches environment variable

### Useful Commands:

```bash
# List Lambda functions
aws lambda list-functions --region <REGION>

# Get Lambda function details
aws lambda get-function --function-name analyze_crop_image --region <REGION>

# Update Lambda environment variables
aws lambda update-function-configuration \
  --function-name analyze_crop_image \
  --environment Variables="{TABLE_NAME=agri-nexus-data}" \
  --region <REGION>

# Delete and recreate if needed
aws lambda delete-function --function-name analyze_crop_image --region <REGION>
```

---

## Cost Optimization Tips

1. **Use Lambda reserved concurrency** for predictable workloads
2. **Enable DynamoDB auto-scaling** if using provisioned capacity
3. **Set S3 lifecycle policies** to delete old files
4. **Monitor CloudWatch metrics** to identify optimization opportunities
5. **Use API Gateway caching** for frequently accessed data

---

## Next Steps

1. ✅ Deploy infrastructure (DynamoDB, S3)
2. ✅ Deploy Lambda functions
3. ✅ Create API Gateway
4. ⏭️ Test end-to-end functionality
5. ⏭️ Run Streamlit application
6. ⏭️ Monitor and optimize

---

## Quick Reference

### API Endpoints:
- `POST /diagnose` - Analyze crop image
- `GET /history/diagnoses` - Get diagnosis history
- `POST /voice/process` - Process voice input
- `POST /voice/tts` - Generate voice response
- `POST /market/ingest` - Ingest market data

### Lambda Functions:
- `analyze_crop_image` - 30s timeout, 512MB
- `get_diagnosis_history` - 15s timeout, 256MB
- `process_voice_input` - 30s timeout, 512MB
- `generate_voice_response` - 15s timeout, 256MB
- `ingest_market_data` - 60s timeout, 512MB
- `trigger_alerts` - 60s timeout, 512MB

### Environment Variables:
- `TABLE_NAME` - DynamoDB table name
- `IMAGE_BUCKET` - S3 bucket for images
- `BEDROCK_MODEL_ID` - Bedrock model identifier
- `AWS_REGION` - AWS region
- `TRIGGER_ALERTS_FUNCTION` - Name of trigger_alerts Lambda
