#!/bin/bash

# API Gateway Deployment Script for Agri-Nexus V1 Platform
# This script automates the API Gateway setup following the manual deployment guide

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REGION=${AWS_REGION:-us-east-1}
API_NAME="AgriNexus API"
STAGE_NAME="prod"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}API Gateway Deployment Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Get AWS Account ID
echo -e "${YELLOW}Getting AWS Account ID...${NC}"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✓ Account ID: $ACCOUNT_ID${NC}"
echo ""

# Step 1: Create REST API
echo -e "${YELLOW}Step 1: Creating REST API...${NC}"
API_ID=$(aws apigateway create-rest-api \
  --name "$API_NAME" \
  --description "REST API for Agri-Nexus V1 Platform" \
  --region $REGION \
  --query 'id' \
  --output text 2>/dev/null || echo "")

if [ -z "$API_ID" ]; then
  # API might already exist, try to find it
  echo -e "${YELLOW}API might already exist, searching...${NC}"
  API_ID=$(aws apigateway get-rest-apis --region $REGION --query "items[?name=='$API_NAME'].id" --output text)
  
  if [ -z "$API_ID" ]; then
    echo -e "${RED}✗ Failed to create or find API${NC}"
    exit 1
  fi
  echo -e "${GREEN}✓ Found existing API: $API_ID${NC}"
else
  echo -e "${GREEN}✓ Created API: $API_ID${NC}"
fi
echo ""

# Step 2: Get Root Resource ID
echo -e "${YELLOW}Step 2: Getting root resource...${NC}"
ROOT_ID=$(aws apigateway get-resources \
  --rest-api-id $API_ID \
  --region $REGION \
  --query 'items[0].id' \
  --output text)
echo -e "${GREEN}✓ Root Resource ID: $ROOT_ID${NC}"
echo ""

# Step 3: Create Resources
echo -e "${YELLOW}Step 3: Creating API resources...${NC}"

# Function to create resource
create_resource() {
  local parent_id=$1
  local path_part=$2
  local resource_name=$3
  
  # Check if resource already exists
  existing_id=$(aws apigateway get-resources \
    --rest-api-id $API_ID \
    --region $REGION \
    --query "items[?pathPart=='$path_part'].id" \
    --output text 2>/dev/null || echo "")
  
  if [ -n "$existing_id" ]; then
    echo -e "${GREEN}  ✓ $resource_name already exists: $existing_id${NC}"
    echo "$existing_id"
  else
    resource_id=$(aws apigateway create-resource \
      --rest-api-id $API_ID \
      --parent-id $parent_id \
      --path-part $path_part \
      --region $REGION \
      --query 'id' \
      --output text)
    echo -e "${GREEN}  ✓ Created $resource_name: $resource_id${NC}"
    echo "$resource_id"
  fi
}

DIAGNOSE_ID=$(create_resource $ROOT_ID "diagnose" "/diagnose")
HISTORY_ID=$(create_resource $ROOT_ID "history" "/history")
DIAGNOSES_ID=$(create_resource $HISTORY_ID "diagnoses" "/history/diagnoses")
VOICE_ID=$(create_resource $ROOT_ID "voice" "/voice")
VOICE_PROCESS_ID=$(create_resource $VOICE_ID "process" "/voice/process")
VOICE_TTS_ID=$(create_resource $VOICE_ID "tts" "/voice/tts")
MARKET_ID=$(create_resource $ROOT_ID "market" "/market")
MARKET_INGEST_ID=$(create_resource $MARKET_ID "ingest" "/market/ingest")

echo ""

# Step 4: Create Methods and Integrations
echo -e "${YELLOW}Step 4: Creating methods and Lambda integrations...${NC}"

# Function to create method and integration
create_method_integration() {
  local resource_id=$1
  local http_method=$2
  local lambda_function=$3
  local path=$4
  
  echo -e "${BLUE}  Configuring $http_method $path → $lambda_function${NC}"
  
  # Create method
  aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $resource_id \
    --http-method $http_method \
    --authorization-type NONE \
    --region $REGION \
    --no-cli-pager 2>/dev/null || true
  
  # Create integration
  aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $resource_id \
    --http-method $http_method \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri "arn:aws:apigateway:$REGION:lambda:path/2015-03-31/functions/arn:aws:lambda:$REGION:$ACCOUNT_ID:function:$lambda_function/invocations" \
    --region $REGION \
    --no-cli-pager 2>/dev/null || true
  
  # Grant permission
  aws lambda add-permission \
    --function-name $lambda_function \
    --statement-id "apigateway-invoke-$(echo $path | tr '/' '-')-$http_method" \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:$REGION:$ACCOUNT_ID:$API_ID/*/$http_method$path" \
    --region $REGION \
    --no-cli-pager 2>/dev/null || true
  
  echo -e "${GREEN}  ✓ Configured $http_method $path${NC}"
}

# Create all method integrations
create_method_integration $DIAGNOSE_ID "POST" "analyze_crop_image" "/diagnose"
create_method_integration $DIAGNOSES_ID "GET" "get_diagnosis_history" "/history/diagnoses"
create_method_integration $VOICE_PROCESS_ID "POST" "process_voice_input" "/voice/process"
create_method_integration $VOICE_TTS_ID "POST" "generate_voice_response" "/voice/tts"
create_method_integration $MARKET_INGEST_ID "POST" "ingest_market_data" "/market/ingest"

echo ""

# Step 5: Deploy API
echo -e "${YELLOW}Step 5: Deploying API to $STAGE_NAME stage...${NC}"
aws apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name $STAGE_NAME \
  --region $REGION \
  --no-cli-pager 2>/dev/null || true

echo -e "${GREEN}✓ API deployed to $STAGE_NAME stage${NC}"
echo ""

# Step 6: Display API URL
API_URL="https://$API_ID.execute-api.$REGION.amazonaws.com/$STAGE_NAME"
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✓ API Gateway Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}API Gateway URL:${NC}"
echo -e "${GREEN}$API_URL${NC}"
echo ""
echo -e "${BLUE}Available Endpoints:${NC}"
echo -e "  POST   $API_URL/diagnose"
echo -e "  GET    $API_URL/history/diagnoses"
echo -e "  POST   $API_URL/voice/process"
echo -e "  POST   $API_URL/voice/tts"
echo -e "  POST   $API_URL/market/ingest"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo -e "1. Update your .env file with:"
echo -e "   ${GREEN}API_GATEWAY_URL=$API_URL${NC}"
echo -e "2. Test the endpoints:"
echo -e "   ${GREEN}curl -X POST $API_URL/diagnose -H 'Content-Type: application/json' -d '{\"user_id\":\"test\",\"image_data\":\"\",\"language\":\"en\"}'${NC}"
echo -e "3. Run integration tests:"
echo -e "   ${GREEN}python tests/test_integration.py${NC}"
echo ""

# Save API URL to file
echo "API_GATEWAY_URL=$API_URL" > .api_gateway_url
echo -e "${GREEN}✓ API URL saved to .api_gateway_url${NC}"
echo ""

