#!/usr/bin/env python3
"""
Agri-Nexus V1 Platform - Automated Deployment Script (Python)

This script automates the complete deployment of the Agri-Nexus platform
including infrastructure, Lambda functions, and API Gateway.

Prerequisites:
- AWS CLI installed and configured
- Python 3.9+ installed
- boto3 installed (pip install boto3)
- Appropriate AWS permissions
- Bedrock access enabled

Usage:
    python deploy.py [OPTIONS]

Options:
    --region REGION       AWS region (default: ap-south-1)
    --skip-infra         Skip infrastructure deployment
    --skip-lambda        Skip Lambda deployment
    --skip-api           Skip API Gateway deployment
    --clean              Clean up existing resources
    --help               Show this help message
"""

import argparse
import boto3
import json
import os
import sys
import time
import zipfile
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Optional

# Color codes for terminal output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color


class AgriNexusDeployer:
    """Main deployment class for Agri-Nexus platform"""
    
    def __init__(self, region: str = 'ap-south-1'):
        self.region = region
        self.account_id = None
        self.role_arn = None
        self.api_id = None
        self.api_url = None
        
        # Initialize AWS clients
        self.iam = boto3.client('iam', region_name=region)
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.apigateway = boto3.client('apigateway', region_name=region)
        self.sts = boto3.client('sts', region_name=region)
    
    def print_info(self, message: str):
        """Print info message"""
        print(f"{Colors.BLUE}[INFO]{Colors.NC} {message}")
    
    def print_success(self, message: str):
        """Print success message"""
        print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {message}")
    
    def print_warning(self, message: str):
        """Print warning message"""
        print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {message}")
    
    def print_error(self, message: str):
        """Print error message"""
        print(f"{Colors.RED}[ERROR]{Colors.NC} {message}")
    
    def print_header(self, message: str):
        """Print section header"""
        print()
        print(f"{Colors.GREEN}{'=' * 60}{Colors.NC}")
        print(f"{Colors.GREEN}{message}{Colors.NC}")
        print(f"{Colors.GREEN}{'=' * 60}{Colors.NC}")
        print()
    
    def check_prerequisites(self):
        """Check if all prerequisites are met"""
        self.print_header("Checking Prerequisites")
        
        # Check boto3
        try:
            import boto3
            self.print_success(f"boto3 found: {boto3.__version__}")
        except ImportError:
            self.print_error("boto3 not found. Install with: pip install boto3")
            sys.exit(1)
        
        # Check AWS credentials
        try:
            identity = self.sts.get_caller_identity()
            self.account_id = identity['Account']
            self.print_success(f"AWS Account ID: {self.account_id}")
        except Exception as e:
            self.print_error(f"AWS credentials not configured: {e}")
            sys.exit(1)
        
        # Check Python version
        if sys.version_info < (3, 9):
            self.print_error("Python 3.9+ required")
            sys.exit(1)
        self.print_success(f"Python version: {sys.version.split()[0]}")
        
        self.print_warning(f"Please ensure Bedrock is enabled in region {self.region}")
    
    def cleanup_resources(self):
        """Clean up existing resources"""
        self.print_header("Cleaning Up Existing Resources")
        
        confirmation = input("This will delete all Agri-Nexus resources. Are you sure? (yes/no): ")
        if confirmation.lower() != 'yes':
            self.print_info("Cleanup cancelled.")
            return
        
        # Delete Lambda functions
        self.print_info("Deleting Lambda functions...")
        functions = [
            'analyze_crop_image',
            'get_diagnosis_history',
            'process_voice_input',
            'generate_voice_response',
            'ingest_market_data',
            'trigger_alerts'
        ]
        
        for func in functions:
            try:
                self.lambda_client.delete_function(FunctionName=func)
                self.print_success(f"Deleted Lambda function: {func}")
            except self.lambda_client.exceptions.ResourceNotFoundException:
                pass
            except Exception as e:
                self.print_warning(f"Error deleting {func}: {e}")
        
        # Delete API Gateway
        self.print_info("Deleting API Gateway...")
        try:
            apis = self.apigateway.get_rest_apis()
            for api in apis['items']:
                if api['name'] == 'AgriNexus API':
                    self.apigateway.delete_rest_api(restApiId=api['id'])
                    self.print_success(f"Deleted API Gateway: {api['id']}")
        except Exception as e:
            self.print_warning(f"Error deleting API Gateway: {e}")
        
        # Delete IAM role
        self.print_info("Deleting IAM role...")
        try:
            self.iam.delete_role_policy(
                RoleName='AgriNexusLambdaExecutionRole',
                PolicyName='AgriNexusLambdaPermissions'
            )
            self.iam.delete_role(RoleName='AgriNexusLambdaExecutionRole')
            self.print_success("Deleted IAM role: AgriNexusLambdaExecutionRole")
        except self.iam.exceptions.NoSuchEntityException:
            pass
        except Exception as e:
            self.print_warning(f"Error deleting IAM role: {e}")
        
        self.print_success("Cleanup completed!")
    
    def deploy_infrastructure(self):
        """Deploy DynamoDB and S3 infrastructure"""
        self.print_header("Deploying Infrastructure (DynamoDB + S3)")
        
        # Run DynamoDB creation script
        self.print_info("Creating DynamoDB table...")
        try:
            subprocess.run(
                ['python3', 'infrastructure/create_dynamodb_table.py'],
                check=True,
                capture_output=True
            )
            self.print_success("DynamoDB table created successfully")
        except subprocess.CalledProcessError as e:
            self.print_warning("DynamoDB table may already exist or creation failed")
        
        # Run S3 creation script
        self.print_info("Creating S3 bucket...")
        try:
            subprocess.run(
                ['python3', 'infrastructure/create_s3_bucket.py'],
                check=True,
                capture_output=True
            )
            self.print_success("S3 bucket created successfully")
        except subprocess.CalledProcessError as e:
            self.print_warning("S3 bucket may already exist or creation failed")
    
    def create_iam_role(self):
        """Create IAM execution role for Lambda functions"""
        self.print_header("Creating IAM Execution Role")
        
        # Check if role already exists
        try:
            role = self.iam.get_role(RoleName='AgriNexusLambdaExecutionRole')
            self.role_arn = role['Role']['Arn']
            self.print_warning("IAM role already exists. Skipping creation.")
            return
        except self.iam.exceptions.NoSuchEntityException:
            pass
        
        # Trust policy
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "lambda.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        # Create role
        self.print_info("Creating IAM role...")
        role = self.iam.create_role(
            RoleName='AgriNexusLambdaExecutionRole',
            AssumeRolePolicyDocument=json.dumps(trust_policy)
        )
        self.role_arn = role['Role']['Arn']
        
        # Permissions policy
        permissions_policy = {
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
                    "Action": ["bedrock:InvokeModel"],
                    "Resource": "arn:aws:bedrock:*::foundation-model/*"
                },
                {
                    "Effect": "Allow",
                    "Action": ["sns:Publish"],
                    "Resource": "*"
                },
                {
                    "Effect": "Allow",
                    "Action": ["lambda:InvokeFunction"],
                    "Resource": "arn:aws:lambda:*:*:function:trigger_alerts"
                }
            ]
        }
        
        # Attach policy
        self.print_info("Attaching permissions policy...")
        self.iam.put_role_policy(
            RoleName='AgriNexusLambdaExecutionRole',
            PolicyName='AgriNexusLambdaPermissions',
            PolicyDocument=json.dumps(permissions_policy)
        )
        
        self.print_success(f"IAM role created: {self.role_arn}")
        
        # Wait for role to propagate
        self.print_info("Waiting for IAM role to propagate...")
        time.sleep(10)
    
    def package_lambda(self, function_name: str, handler_path: str) -> str:
        """Package Lambda function with dependencies"""
        self.print_info(f"Packaging {function_name}...")
        
        # Create temp directory
        temp_dir = Path(f'/tmp/lambda-{function_name}')
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        temp_dir.mkdir(parents=True)
        
        # Copy handler
        shutil.copy(handler_path, temp_dir / 'handler.py')
        
        # Copy shared modules
        shared_dir = temp_dir / 'shared'
        shared_dir.mkdir()
        for py_file in Path('shared').glob('*.py'):
            shutil.copy(py_file, shared_dir)
        
        # Install dependencies
        subprocess.run(
            ['pip3', 'install', '--target', str(temp_dir), 'boto3', 'pillow', '-q'],
            check=True,
            capture_output=True
        )
        
        # Create zip file
        zip_path = f'/tmp/{function_name}.zip'
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(temp_dir)
                    zipf.write(file_path, arcname)
        
        self.print_success(f"Packaged {function_name}")
        return zip_path
    
    def deploy_lambda_function(
        self,
        function_name: str,
        zip_path: str,
        timeout: int,
        memory: int,
        env_vars: Dict[str, str]
    ):
        """Deploy or update Lambda function"""
        self.print_info(f"Deploying Lambda function: {function_name}...")
        
        with open(zip_path, 'rb') as f:
            zip_content = f.read()
        
        try:
            # Try to get existing function
            self.lambda_client.get_function(FunctionName=function_name)
            
            # Update existing function
            self.print_info("Updating existing function...")
            self.lambda_client.update_function_code(
                FunctionName=function_name,
                ZipFile=zip_content
            )
            
            self.lambda_client.update_function_configuration(
                FunctionName=function_name,
                Timeout=timeout,
                MemorySize=memory,
                Environment={'Variables': env_vars}
            )
        except self.lambda_client.exceptions.ResourceNotFoundException:
            # Create new function
            self.lambda_client.create_function(
                FunctionName=function_name,
                Runtime='python3.9',
                Role=self.role_arn,
                Handler='handler.lambda_handler',
                Code={'ZipFile': zip_content},
                Timeout=timeout,
                MemorySize=memory,
                Environment={'Variables': env_vars}
            )
        
        self.print_success(f"Deployed Lambda function: {function_name}")
    
    def deploy_lambda_functions(self):
        """Deploy all Lambda functions"""
        self.print_header("Deploying Lambda Functions")
        
        functions = [
            {
                'name': 'analyze_crop_image',
                'handler': 'backend/analyze_crop_image/handler.py',
                'timeout': 30,
                'memory': 512,
                'env': {
                    'TABLE_NAME': 'agri-nexus-data',
                    'IMAGE_BUCKET': f'agri-nexus-media-{self.account_id}',
                    'BEDROCK_MODEL_ID': 'anthropic.claude-3-5-sonnet-20240620-v1:0',
                    'AWS_REGION': self.region
                }
            },
            {
                'name': 'get_diagnosis_history',
                'handler': 'backend/get_diagnosis_history/handler.py',
                'timeout': 15,
                'memory': 256,
                'env': {
                    'TABLE_NAME': 'agri-nexus-data',
                    'AWS_REGION': self.region
                }
            },
            {
                'name': 'process_voice_input',
                'handler': 'backend/process_voice_input/handler.py',
                'timeout': 30,
                'memory': 512,
                'env': {
                    'TABLE_NAME': 'agri-nexus-data',
                    'BEDROCK_MODEL_ID': 'anthropic.claude-3-5-sonnet-20240620-v1:0',
                    'AWS_REGION': self.region
                }
            },
            {
                'name': 'generate_voice_response',
                'handler': 'backend/generate_voice_response/handler.py',
                'timeout': 15,
                'memory': 256,
                'env': {
                    'BEDROCK_MODEL_ID': 'anthropic.claude-3-5-sonnet-20240620-v1:0',
                    'AWS_REGION': self.region
                }
            },
            {
                'name': 'ingest_market_data',
                'handler': 'backend/ingest_market_data/handler.py',
                'timeout': 60,
                'memory': 512,
                'env': {
                    'TABLE_NAME': 'agri-nexus-data',
                    'TRIGGER_ALERTS_FUNCTION': 'trigger_alerts',
                    'AWS_REGION': self.region
                }
            },
            {
                'name': 'trigger_alerts',
                'handler': 'backend/trigger_alerts/handler.py',
                'timeout': 60,
                'memory': 512,
                'env': {
                    'TABLE_NAME': 'agri-nexus-data',
                    'AWS_REGION': self.region
                }
            }
        ]
        
        for func in functions:
            zip_path = self.package_lambda(func['name'], func['handler'])
            self.deploy_lambda_function(
                func['name'],
                zip_path,
                func['timeout'],
                func['memory'],
                func['env']
            )
        
        self.print_success("All Lambda functions deployed!")
    
    def create_api_gateway(self):
        """Create API Gateway with all endpoints"""
        self.print_header("Creating API Gateway")
        
        # Check if API already exists
        apis = self.apigateway.get_rest_apis()
        for api in apis['items']:
            if api['name'] == 'AgriNexus API':
                self.api_id = api['id']
                self.print_warning(f"API Gateway already exists: {self.api_id}")
                break
        
        if not self.api_id:
            # Create REST API
            self.print_info("Creating REST API...")
            api = self.apigateway.create_rest_api(
                name='AgriNexus API',
                description='REST API for Agri-Nexus V1 Platform'
            )
            self.api_id = api['id']
            self.print_success(f"Created API Gateway: {self.api_id}")
        
        # Get root resource
        resources = self.apigateway.get_resources(restApiId=self.api_id)
        root_id = [r['id'] for r in resources['items'] if r['path'] == '/'][0]
        
        # Create endpoints
        self.create_endpoint(root_id, 'diagnose', 'POST', 'analyze_crop_image')
        
        # /history/diagnoses
        history_id = self.create_resource(root_id, 'history')
        diagnoses_id = self.create_resource(history_id, 'diagnoses')
        self.create_method(diagnoses_id, 'GET', 'get_diagnosis_history')
        
        # /voice/process and /voice/tts
        voice_id = self.create_resource(root_id, 'voice')
        process_id = self.create_resource(voice_id, 'process')
        self.create_method(process_id, 'POST', 'process_voice_input')
        tts_id = self.create_resource(voice_id, 'tts')
        self.create_method(tts_id, 'POST', 'generate_voice_response')
        
        # /market/ingest
        market_id = self.create_resource(root_id, 'market')
        ingest_id = self.create_resource(market_id, 'ingest')
        self.create_method(ingest_id, 'POST', 'ingest_market_data')
        
        # Deploy API
        self.print_info("Deploying API to prod stage...")
        self.apigateway.create_deployment(
            restApiId=self.api_id,
            stageName='prod'
        )
        
        self.api_url = f"https://{self.api_id}.execute-api.{self.region}.amazonaws.com/prod"
        self.print_success(f"API Gateway deployed: {self.api_url}")
        
        # Save to .env file
        with open('.env', 'a') as f:
            f.write(f"\nAPI_GATEWAY_URL={self.api_url}\n")
        self.print_success("API Gateway URL saved to .env file")
    
    def create_resource(self, parent_id: str, path_part: str) -> str:
        """Create API Gateway resource"""
        # Check if resource already exists
        resources = self.apigateway.get_resources(restApiId=self.api_id)
        for resource in resources['items']:
            if resource.get('pathPart') == path_part:
                return resource['id']
        
        # Create resource
        resource = self.apigateway.create_resource(
            restApiId=self.api_id,
            parentId=parent_id,
            pathPart=path_part
        )
        return resource['id']
    
    def create_endpoint(self, parent_id: str, path_part: str, method: str, lambda_function: str):
        """Create complete endpoint (resource + method)"""
        resource_id = self.create_resource(parent_id, path_part)
        self.create_method(resource_id, method, lambda_function)
    
    def create_method(self, resource_id: str, http_method: str, lambda_function: str):
        """Create API Gateway method and Lambda integration"""
        self.print_info(f"Creating {http_method} method for {lambda_function}...")
        
        try:
            # Create method
            self.apigateway.put_method(
                restApiId=self.api_id,
                resourceId=resource_id,
                httpMethod=http_method,
                authorizationType='NONE'
            )
        except self.apigateway.exceptions.ConflictException:
            pass
        
        # Create integration
        lambda_uri = f"arn:aws:apigateway:{self.region}:lambda:path/2015-03-31/functions/arn:aws:lambda:{self.region}:{self.account_id}:function:{lambda_function}/invocations"
        
        try:
            self.apigateway.put_integration(
                restApiId=self.api_id,
                resourceId=resource_id,
                httpMethod=http_method,
                type='AWS_PROXY',
                integrationHttpMethod='POST',
                uri=lambda_uri
            )
        except self.apigateway.exceptions.ConflictException:
            pass
        
        # Grant permission
        try:
            self.lambda_client.add_permission(
                FunctionName=lambda_function,
                StatementId=f'apigateway-invoke-{int(time.time())}',
                Action='lambda:InvokeFunction',
                Principal='apigateway.amazonaws.com',
                SourceArn=f"arn:aws:execute-api:{self.region}:{self.account_id}:{self.api_id}/*/{http_method}/*"
            )
        except self.lambda_client.exceptions.ResourceConflictException:
            pass
    
    def display_summary(self):
        """Display deployment summary"""
        self.print_header("Deployment Summary")
        
        print(f"{Colors.GREEN}✓{Colors.NC} Infrastructure deployed")
        print(f"{Colors.GREEN}✓{Colors.NC} Lambda functions deployed (6 functions)")
        print(f"{Colors.GREEN}✓{Colors.NC} API Gateway created")
        print()
        print(f"{Colors.BLUE}API Gateway URL:{Colors.NC}")
        print(f"  {self.api_url}")
        print()
        print(f"{Colors.BLUE}Next Steps:{Colors.NC}")
        print("  1. Update .env file with the API Gateway URL (already done)")
        print("  2. Run: streamlit run frontend/streamlit_app.py")
        print("  3. Test the application")
        print()
        print(f"{Colors.YELLOW}Important:{Colors.NC}")
        print("  - Ensure Bedrock is enabled in your AWS account")
        print("  - Verify all Lambda functions have proper permissions")
        print("  - Check CloudWatch logs for any errors")
        print()
    
    def deploy(self, skip_infra: bool = False, skip_lambda: bool = False, skip_api: bool = False):
        """Main deployment flow"""
        self.print_header("Agri-Nexus V1 Platform Deployment")
        
        print(f"Configuration:")
        print(f"  AWS Region: {self.region}")
        print(f"  Account ID: {self.account_id}")
        print()
        
        # Check prerequisites
        self.check_prerequisites()
        
        # Deploy infrastructure
        if not skip_infra:
            self.deploy_infrastructure()
        else:
            self.print_warning("Skipping infrastructure deployment")
        
        # Create IAM role
        self.create_iam_role()
        
        # Deploy Lambda functions
        if not skip_lambda:
            self.deploy_lambda_functions()
        else:
            self.print_warning("Skipping Lambda deployment")
        
        # Create API Gateway
        if not skip_api:
            self.create_api_gateway()
        else:
            self.print_warning("Skipping API Gateway deployment")
        
        # Display summary
        self.display_summary()
        
        self.print_success("Deployment completed successfully!")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Deploy Agri-Nexus V1 Platform to AWS',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        '--region',
        default='ap-south-1',
        help='AWS region (default: ap-south-1)'
    )
    parser.add_argument(
        '--skip-infra',
        action='store_true',
        help='Skip infrastructure deployment'
    )
    parser.add_argument(
        '--skip-lambda',
        action='store_true',
        help='Skip Lambda deployment'
    )
    parser.add_argument(
        '--skip-api',
        action='store_true',
        help='Skip API Gateway deployment'
    )
    parser.add_argument(
        '--clean',
        action='store_true',
        help='Clean up existing resources'
    )
    
    args = parser.parse_args()
    
    # Create deployer
    deployer = AgriNexusDeployer(region=args.region)
    
    # Clean up if requested
    if args.clean:
        deployer.cleanup_resources()
        return
    
    # Deploy
    deployer.deploy(
        skip_infra=args.skip_infra,
        skip_lambda=args.skip_lambda,
        skip_api=args.skip_api
    )


if __name__ == '__main__':
    main()
