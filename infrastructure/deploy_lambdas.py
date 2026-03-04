"""
Lambda Deployment Script for Agri-Nexus V1 Platform
Packages and deploys all Lambda functions with dependencies
"""

import boto3
import os
import zipfile
import shutil
from pathlib import Path
import json
from dotenv import load_dotenv

load_dotenv()


def create_lambda_package(function_name: str, handler_path: str) -> str:
    """
    Create deployment package for Lambda function
    
    Args:
        function_name: Name of the Lambda function
        handler_path: Path to handler.py file
        
    Returns:
        Path to the created zip file
    """
    print(f"\n📦 Creating package for {function_name}...")
    
    # Create temporary directory for packaging
    package_dir = Path(f"temp_{function_name}")
    package_dir.mkdir(exist_ok=True)
    
    try:
        # Copy handler file
        handler_file = Path(handler_path)
        shutil.copy(handler_file, package_dir / "handler.py")
        
        # Copy shared directory
        shared_src = Path("shared")
        shared_dst = package_dir / "shared"
        if shared_src.exists():
            shutil.copytree(shared_src, shared_dst, dirs_exist_ok=True)
        
        # Install dependencies if requirements.txt exists
        requirements_file = handler_file.parent / "requirements.txt"
        if requirements_file.exists():
            print(f"  Installing dependencies from {requirements_file}...")
            os.system(f"pip install -r {requirements_file} -t {package_dir} --quiet")
        
        # Create zip file
        zip_path = f"{function_name}.zip"
        print(f"  Creating zip file: {zip_path}")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(package_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(package_dir)
                    zipf.write(file_path, arcname)
        
        print(f"  ✅ Package created: {zip_path}")
        return zip_path
        
    finally:
        # Cleanup temporary directory
        if package_dir.exists():
            shutil.rmtree(package_dir)


def create_lambda_function(
    function_name: str,
    zip_path: str,
    handler: str = "handler.lambda_handler",
    timeout: int = 30,
    memory_size: int = 512
):
    """
    Create or update Lambda function
    
    Args:
        function_name: Name of the Lambda function
        zip_path: Path to deployment package
        handler: Handler function path
        timeout: Function timeout in seconds
        memory_size: Memory allocation in MB
    """
    lambda_client = boto3.client('lambda', region_name=os.getenv('AWS_REGION', 'us-east-1'))
    
    # Read zip file
    with open(zip_path, 'rb') as f:
        zip_content = f.read()
    
    # Get or create IAM role
    role_arn = get_or_create_lambda_role(function_name)
    
    try:
        # Try to update existing function
        print(f"\n🔄 Updating Lambda function: {function_name}")
        
        lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_content
        )
        
        lambda_client.update_function_configuration(
            FunctionName=function_name,
            Handler=handler,
            Timeout=timeout,
            MemorySize=memory_size,
            Environment={
                'Variables': {
                    'AWS_REGION': os.getenv('AWS_REGION', 'us-east-1'),
                    'TABLE_NAME': os.getenv('TABLE_NAME', 'agri-nexus-data'),
                    'IMAGE_BUCKET': os.getenv('IMAGE_BUCKET', 'agri-nexus-images'),
                    'BEDROCK_MODEL_ID': os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-5-sonnet-20241022-v2:0'),
                }
            }
        )
        
        print(f"  ✅ Function updated successfully")
        
    except lambda_client.exceptions.ResourceNotFoundException:
        # Create new function
        print(f"\n🆕 Creating Lambda function: {function_name}")
        
        response = lambda_client.create_function(
            FunctionName=function_name,
            Runtime='python3.12',
            Role=role_arn,
            Handler=handler,
            Code={'ZipFile': zip_content},
            Timeout=timeout,
            MemorySize=memory_size,
            Environment={
                'Variables': {
                    'AWS_REGION': os.getenv('AWS_REGION', 'us-east-1'),
                    'TABLE_NAME': os.getenv('TABLE_NAME', 'agri-nexus-data'),
                    'IMAGE_BUCKET': os.getenv('IMAGE_BUCKET', 'agri-nexus-images'),
                    'BEDROCK_MODEL_ID': os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-5-sonnet-20241022-v2:0'),
                }
            },
            Tags={
                'Project': 'Agri-Nexus-V1',
                'Environment': os.getenv('ENVIRONMENT', 'development')
            }
        )
        
        print(f"  ✅ Function created successfully")
        print(f"  Function ARN: {response['FunctionArn']}")


def get_or_create_lambda_role(function_name: str) -> str:
    """
    Get or create IAM role for Lambda function
    
    Args:
        function_name: Name of the Lambda function
        
    Returns:
        Role ARN
    """
    iam_client = boto3.client('iam')
    role_name = f"{function_name}-role"
    
    try:
        # Try to get existing role
        response = iam_client.get_role(RoleName=role_name)
        return response['Role']['Arn']
    except iam_client.exceptions.NoSuchEntityException:
        # Create new role
        print(f"  Creating IAM role: {role_name}")
        
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
        
        response = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description=f"Role for {function_name} Lambda function"
        )
        
        # Attach policies
        policies = [
            'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
            'arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess',
            'arn:aws:iam::aws:policy/AmazonS3FullAccess',
            'arn:aws:iam::aws:policy/AmazonSNSFullAccess',
        ]
        
        for policy_arn in policies:
            iam_client.attach_role_policy(
                RoleName=role_name,
                PolicyArn=policy_arn
            )
        
        # Add Bedrock permissions
        bedrock_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:InvokeModel",
                        "bedrock:InvokeModelWithResponseStream"
                    ],
                    "Resource": "*"
                }
            ]
        }
        
        iam_client.put_role_policy(
            RoleName=role_name,
            PolicyName='BedrockAccess',
            PolicyDocument=json.dumps(bedrock_policy)
        )
        
        print(f"  ✅ IAM role created: {role_name}")
        
        # Wait for role to be available
        import time
        time.sleep(10)
        
        return response['Role']['Arn']


def deploy_all_lambdas():
    """Deploy all Lambda functions"""
    
    functions = [
        {
            'name': 'analyze_crop_image',
            'handler_path': 'backend/analyze_crop_image/handler.py',
            'timeout': 30,
            'memory': 512
        },
        {
            'name': 'process_voice_input',
            'handler_path': 'backend/process_voice_input/handler.py',
            'timeout': 15,
            'memory': 512
        },
        {
            'name': 'generate_voice_response',
            'handler_path': 'backend/generate_voice_response/handler.py',
            'timeout': 15,
            'memory': 256
        },
        {
            'name': 'ingest_market_data',
            'handler_path': 'backend/ingest_market_data/handler.py',
            'timeout': 10,
            'memory': 256
        },
        {
            'name': 'trigger_alerts',
            'handler_path': 'backend/trigger_alerts/handler.py',
            'timeout': 60,
            'memory': 512
        }
    ]
    
    print("🚀 Starting Lambda deployment...")
    print(f"Region: {os.getenv('AWS_REGION', 'us-east-1')}")
    
    for func in functions:
        try:
            # Create package
            zip_path = create_lambda_package(func['name'], func['handler_path'])
            
            # Deploy function
            create_lambda_function(
                function_name=func['name'],
                zip_path=zip_path,
                timeout=func['timeout'],
                memory_size=func['memory']
            )
            
            # Cleanup zip file
            if os.path.exists(zip_path):
                os.remove(zip_path)
                
        except Exception as e:
            print(f"  ❌ Error deploying {func['name']}: {str(e)}")
            continue
    
    print("\n✅ Lambda deployment complete!")
    print("\nNext steps:")
    print("1. Create API Gateway and connect to Lambda functions")
    print("2. Update frontend with API Gateway URL")
    print("3. Test end-to-end functionality")


if __name__ == '__main__':
    deploy_all_lambdas()
