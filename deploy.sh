#!/bin/bash

################################################################################
# Agri-Nexus V1 Platform - Automated Deployment Script
# 
# This script automates the complete deployment of the Agri-Nexus platform
# including infrastructure, Lambda functions, and API Gateway.
#
# Prerequisites:
# - AWS CLI installed and configured
# - Python 3.9+ installed
# - Appropriate AWS permissions
# - Bedrock access enabled
#
# Usage:
#   ./deploy.sh [OPTIONS]
#
# Options:
#   --region REGION       AWS region (default: ap-south-1)
#   --skip-infra         Skip infrastructure deployment
#   --skip-lambda        Skip Lambda deployment
#   --skip-api           Skip API Gateway deployment
#   --clean              Clean up existing resources
#   --help               Show this help message
#
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default configuration
AWS_REGION="${AWS_REGION:-ap-south-1}"
SKIP_INFRA=false
SKIP_LAMBDA=false
SKIP_API=false
CLEAN_MODE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --region)
            AWS_REGION="$2"
            shift 2
            ;;
        --skip-infra)
            SKIP_INFRA=true
            shift
            ;;
        --skip-lambda)
            SKIP_LAMBDA=true
            shift
            ;;
        --skip-api)
            SKIP_API=true
            shift
            ;;
        --clean)
            CLEAN_MODE=true
            shift
            ;;
        --help)
            grep "^#" "$0" | grep -v "#!/bin/bash" | sed 's/^# //'
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Function to print colored messages
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
}

# Function to check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI not found. Please install it first."
        exit 1
    fi
    print_success "AWS CLI found: $(aws --version)"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 not found. Please install it first."
        exit 1
    fi
    print_success "Python found: $(python3 --version)"
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured. Run 'aws configure' first."
        exit 1
    fi
    
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    print_success "AWS Account ID: $ACCOUNT_ID"
    
    # Check if Bedrock is available in region
    print_info "Checking Bedrock availability in $AWS_REGION..."
    # Note: This is informational, actual check requires API call
    print_warning "Please ensure Bedrock is enabled in your account for region $AWS_REGION"
}

# Function to clean up existing resources
cleanup_resources() {
    print_header "Cleaning Up Existing Resources"
    
    print_warning "This will delete all Agri-Nexus resources. Are you sure? (yes/no)"
    read -r confirmation
    if [[ "$confirmation" != "yes" ]]; then
        print_info "Cleanup cancelled."
        return
    fi
    
    # Delete Lambda functions
    print_info "Deleting Lambda functions..."
    for func in analyze_crop_image get_diagnosis_history process_voice_input generate_voice_response ingest_market_data trigger_alerts; do
        if aws lambda get-function --function-name "$func" --region "$AWS_REGION" &> /dev/null; then
            aws lambda delete-function --function-name "$func" --region "$AWS_REGION"
            print_success "Deleted Lambda function: $func"
        fi
    done
    
    # Delete API Gateway
    print_info "Deleting API Gateway..."
    API_ID=$(aws apigateway get-rest-apis --region "$AWS_REGION" --query "items[?name=='AgriNexus API'].id" --output text)
    if [[ -n "$API_ID" ]]; then
        aws apigateway delete-rest-api --rest-api-id "$API_ID" --region "$AWS_REGION"
        print_success "Deleted API Gateway: $API_ID"
    fi
    
    # Delete IAM role
    print_info "Deleting IAM role..."
    if aws iam get-role --role-name AgriNexusLambdaExecutionRole &> /dev/null; then
        aws iam delete-role-policy --role-name AgriNexusLambdaExecutionRole --policy-name AgriNexusLambdaPermissions
        aws iam delete-role --role-name AgriNexusLambdaExecutionRole
        print_success "Deleted IAM role: AgriNexusLambdaExecutionRole"
    fi
    
    print_success "Cleanup completed!"
}

# Function to deploy infrastructure
deploy_infrastructure() {
    print_header "Deploying Infrastructure (DynamoDB + S3)"
    
    # Create DynamoDB table
    print_info "Creating DynamoDB table..."
    if python3 infrastructure/create_dynamodb_table.py; then
        print_success "DynamoDB table created successfully"
    else
        print_warning "DynamoDB table may already exist or creation failed"
    fi
    
    # Create S3 bucket
    print_info "Creating S3 bucket..."
    if python3 infrastructure/create_s3_bucket.py; then
        print_success "S3 bucket created successfully"
    else
        print_warning "S3 bucket may already exist or creation failed"
    fi
}

# Function to create IAM role
create_iam_role() {
    print_header "Creating IAM Execution Role"
    
    # Check if role already exists
    if aws iam get-role --role-name AgriNexusLambdaExecutionRole &> /dev/null; then
        print_warning "IAM role already exists. Skipping creation."
        ROLE_ARN=$(aws iam get-role --role-name AgriNexusLambdaExecutionRole --query 'Role.Arn' --output text)
        return
    fi
    
    # Create trust policy
    cat > /tmp/lambda-trust-policy.json <<EOF
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
EOF
    
    # Create role
    print_info "Creating IAM role..."
    aws iam create-role \
        --role-name AgriNexusLambdaExecutionRole \
        --assume-role-policy-document file:///tmp/lambda-trust-policy.json \
        > /dev/null
    
    # Create permissions policy
    cat > /tmp/lambda-permissions-policy.json <<EOF
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
EOF
    
    # Attach policy
    print_info "Attaching permissions policy..."
    aws iam put-role-policy \
        --role-name AgriNexusLambdaExecutionRole \
        --policy-name AgriNexusLambdaPermissions \
        --policy-document file:///tmp/lambda-permissions-policy.json
    
    # Get role ARN
    ROLE_ARN=$(aws iam get-role --role-name AgriNexusLambdaExecutionRole --query 'Role.Arn' --output text)
    print_success "IAM role created: $ROLE_ARN"
    
    # Wait for role to be available
    print_info "Waiting for IAM role to propagate..."
    sleep 10
}

# Function to package Lambda function
package_lambda() {
    local function_name=$1
    local handler_path=$2
    
    print_info "Packaging $function_name..."
    
    # Create temp directory
    local temp_dir="/tmp/lambda-$function_name"
    rm -rf "$temp_dir"
    mkdir -p "$temp_dir"
    
    # Copy handler
    cp "$handler_path" "$temp_dir/handler.py"
    
    # Copy shared modules
    mkdir -p "$temp_dir/shared"
    cp shared/*.py "$temp_dir/shared/"
    
    # Install dependencies
    cd "$temp_dir"
    pip3 install --target . boto3 pillow -q
    
    # Create zip
    zip -r -q "/tmp/$function_name.zip" .
    
    cd - > /dev/null
    
    print_success "Packaged $function_name"
}

# Function to deploy Lambda function
deploy_lambda_function() {
    local function_name=$1
    local timeout=$2
    local memory=$3
    local env_vars=$4
    
    print_info "Deploying Lambda function: $function_name..."
    
    # Check if function exists
    if aws lambda get-function --function-name "$function_name" --region "$AWS_REGION" &> /dev/null; then
        # Update existing function
        print_info "Updating existing function..."
        aws lambda update-function-code \
            --function-name "$function_name" \
            --zip-file "fileb:///tmp/$function_name.zip" \
            --region "$AWS_REGION" \
            > /dev/null
        
        aws lambda update-function-configuration \
            --function-name "$function_name" \
            --timeout "$timeout" \
            --memory-size "$memory" \
            --environment "Variables={$env_vars}" \
            --region "$AWS_REGION" \
            > /dev/null
    else
        # Create new function
        aws lambda create-function \
            --function-name "$function_name" \
            --runtime python3.9 \
            --role "$ROLE_ARN" \
            --handler handler.lambda_handler \
            --zip-file "fileb:///tmp/$function_name.zip" \
            --timeout "$timeout" \
            --memory-size "$memory" \
            --environment "Variables={$env_vars}" \
            --region "$AWS_REGION" \
            > /dev/null
    fi
    
    print_success "Deployed Lambda function: $function_name"
}

# Function to deploy all Lambda functions
deploy_lambda_functions() {
    print_header "Deploying Lambda Functions"
    
    # Package functions
    package_lambda "analyze_crop_image" "backend/analyze_crop_image/handler.py"
    package_lambda "get_diagnosis_history" "backend/get_diagnosis_history/handler.py"
    package_lambda "process_voice_input" "backend/process_voice_input/handler.py"
    package_lambda "generate_voice_response" "backend/generate_voice_response/handler.py"
    package_lambda "ingest_market_data" "backend/ingest_market_data/handler.py"
    package_lambda "trigger_alerts" "backend/trigger_alerts/handler.py"
    
    # Deploy functions
    deploy_lambda_function "analyze_crop_image" 30 512 \
        "TABLE_NAME=agri-nexus-data,IMAGE_BUCKET=agri-nexus-media-$ACCOUNT_ID,BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20240620-v1:0,AWS_REGION=$AWS_REGION"
    
    deploy_lambda_function "get_diagnosis_history" 15 256 \
        "TABLE_NAME=agri-nexus-data,AWS_REGION=$AWS_REGION"
    
    deploy_lambda_function "process_voice_input" 30 512 \
        "TABLE_NAME=agri-nexus-data,BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20240620-v1:0,AWS_REGION=$AWS_REGION"
    
    deploy_lambda_function "generate_voice_response" 15 256 \
        "BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20240620-v1:0,AWS_REGION=$AWS_REGION"
    
    deploy_lambda_function "ingest_market_data" 60 512 \
        "TABLE_NAME=agri-nexus-data,TRIGGER_ALERTS_FUNCTION=trigger_alerts,AWS_REGION=$AWS_REGION"
    
    deploy_lambda_function "trigger_alerts" 60 512 \
        "TABLE_NAME=agri-nexus-data,AWS_REGION=$AWS_REGION"
    
    print_success "All Lambda functions deployed!"
}

# Function to create API Gateway
create_api_gateway() {
    print_header "Creating API Gateway"
    
    # Check if API already exists
    API_ID=$(aws apigateway get-rest-apis --region "$AWS_REGION" --query "items[?name=='AgriNexus API'].id" --output text)
    
    if [[ -n "$API_ID" ]]; then
        print_warning "API Gateway already exists: $API_ID"
    else
        # Create REST API
        print_info "Creating REST API..."
        API_ID=$(aws apigateway create-rest-api \
            --name "AgriNexus API" \
            --description "REST API for Agri-Nexus V1 Platform" \
            --region "$AWS_REGION" \
            --query 'id' \
            --output text)
        print_success "Created API Gateway: $API_ID"
    fi
    
    # Get root resource
    ROOT_RESOURCE_ID=$(aws apigateway get-resources \
        --rest-api-id "$API_ID" \
        --region "$AWS_REGION" \
        --query 'items[?path==`/`].id' \
        --output text)
    
    print_info "Root resource ID: $ROOT_RESOURCE_ID"
    
    # Create resources and methods
    create_api_resource_and_method "$API_ID" "$ROOT_RESOURCE_ID" "diagnose" "POST" "analyze_crop_image"
    
    # Create /history
    HISTORY_ID=$(create_api_resource "$API_ID" "$ROOT_RESOURCE_ID" "history")
    DIAGNOSES_ID=$(create_api_resource "$API_ID" "$HISTORY_ID" "diagnoses")
    create_api_method "$API_ID" "$DIAGNOSES_ID" "GET" "get_diagnosis_history"
    
    # Create /voice
    VOICE_ID=$(create_api_resource "$API_ID" "$ROOT_RESOURCE_ID" "voice")
    VOICE_PROCESS_ID=$(create_api_resource "$API_ID" "$VOICE_ID" "process")
    create_api_method "$API_ID" "$VOICE_PROCESS_ID" "POST" "process_voice_input"
    
    VOICE_TTS_ID=$(create_api_resource "$API_ID" "$VOICE_ID" "tts")
    create_api_method "$API_ID" "$VOICE_TTS_ID" "POST" "generate_voice_response"
    
    # Create /market
    MARKET_ID=$(create_api_resource "$API_ID" "$ROOT_RESOURCE_ID" "market")
    MARKET_INGEST_ID=$(create_api_resource "$API_ID" "$MARKET_ID" "ingest")
    create_api_method "$API_ID" "$MARKET_INGEST_ID" "POST" "ingest_market_data"
    
    # Deploy API
    print_info "Deploying API to prod stage..."
    aws apigateway create-deployment \
        --rest-api-id "$API_ID" \
        --stage-name prod \
        --region "$AWS_REGION" \
        > /dev/null
    
    API_URL="https://$API_ID.execute-api.$AWS_REGION.amazonaws.com/prod"
    print_success "API Gateway deployed: $API_URL"
    
    # Save to .env file
    echo "API_GATEWAY_URL=$API_URL" >> .env
    print_success "API Gateway URL saved to .env file"
}

# Helper function to create API resource
create_api_resource() {
    local api_id=$1
    local parent_id=$2
    local path_part=$3
    
    # Check if resource already exists
    local resource_id=$(aws apigateway get-resources \
        --rest-api-id "$api_id" \
        --region "$AWS_REGION" \
        --query "items[?pathPart=='$path_part'].id" \
        --output text)
    
    if [[ -n "$resource_id" ]]; then
        echo "$resource_id"
        return
    fi
    
    # Create resource
    resource_id=$(aws apigateway create-resource \
        --rest-api-id "$api_id" \
        --parent-id "$parent_id" \
        --path-part "$path_part" \
        --region "$AWS_REGION" \
        --query 'id' \
        --output text)
    
    echo "$resource_id"
}

# Helper function to create API method
create_api_method() {
    local api_id=$1
    local resource_id=$2
    local http_method=$3
    local lambda_function=$4
    
    print_info "Creating $http_method method for $lambda_function..."
    
    # Create method
    aws apigateway put-method \
        --rest-api-id "$api_id" \
        --resource-id "$resource_id" \
        --http-method "$http_method" \
        --authorization-type NONE \
        --region "$AWS_REGION" \
        2>/dev/null || true
    
    # Create integration
    aws apigateway put-integration \
        --rest-api-id "$api_id" \
        --resource-id "$resource_id" \
        --http-method "$http_method" \
        --type AWS_PROXY \
        --integration-http-method POST \
        --uri "arn:aws:apigateway:$AWS_REGION:lambda:path/2015-03-31/functions/arn:aws:lambda:$AWS_REGION:$ACCOUNT_ID:function:$lambda_function/invocations" \
        --region "$AWS_REGION" \
        2>/dev/null || true
    
    # Grant permission
    aws lambda add-permission \
        --function-name "$lambda_function" \
        --statement-id "apigateway-invoke-$(date +%s)" \
        --action lambda:InvokeFunction \
        --principal apigateway.amazonaws.com \
        --source-arn "arn:aws:execute-api:$AWS_REGION:$ACCOUNT_ID:$api_id/*/$http_method/*" \
        --region "$AWS_REGION" \
        2>/dev/null || true
}

# Helper function to create resource and method
create_api_resource_and_method() {
    local api_id=$1
    local parent_id=$2
    local path_part=$3
    local http_method=$4
    local lambda_function=$5
    
    local resource_id=$(create_api_resource "$api_id" "$parent_id" "$path_part")
    create_api_method "$api_id" "$resource_id" "$http_method" "$lambda_function"
}

# Function to display deployment summary
display_summary() {
    print_header "Deployment Summary"
    
    echo -e "${GREEN}✓${NC} Infrastructure deployed"
    echo -e "${GREEN}✓${NC} Lambda functions deployed (6 functions)"
    echo -e "${GREEN}✓${NC} API Gateway created"
    echo ""
    echo -e "${BLUE}API Gateway URL:${NC}"
    echo -e "  $API_URL"
    echo ""
    echo -e "${BLUE}Next Steps:${NC}"
    echo "  1. Update .env file with the API Gateway URL (already done)"
    echo "  2. Run: streamlit run frontend/streamlit_app.py"
    echo "  3. Test the application"
    echo ""
    echo -e "${YELLOW}Important:${NC}"
    echo "  - Ensure Bedrock is enabled in your AWS account"
    echo "  - Verify all Lambda functions have proper permissions"
    echo "  - Check CloudWatch logs for any errors"
    echo ""
}

# Main deployment flow
main() {
    print_header "Agri-Nexus V1 Platform Deployment"
    
    echo "Configuration:"
    echo "  AWS Region: $AWS_REGION"
    echo "  Account ID: $ACCOUNT_ID"
    echo ""
    
    # Check prerequisites
    check_prerequisites
    
    # Clean up if requested
    if [[ "$CLEAN_MODE" == true ]]; then
        cleanup_resources
        exit 0
    fi
    
    # Deploy infrastructure
    if [[ "$SKIP_INFRA" == false ]]; then
        deploy_infrastructure
    else
        print_warning "Skipping infrastructure deployment"
    fi
    
    # Create IAM role
    create_iam_role
    
    # Deploy Lambda functions
    if [[ "$SKIP_LAMBDA" == false ]]; then
        deploy_lambda_functions
    else
        print_warning "Skipping Lambda deployment"
    fi
    
    # Create API Gateway
    if [[ "$SKIP_API" == false ]]; then
        create_api_gateway
    else
        print_warning "Skipping API Gateway deployment"
    fi
    
    # Display summary
    display_summary
    
    print_success "Deployment completed successfully!"
}

# Run main function
main
