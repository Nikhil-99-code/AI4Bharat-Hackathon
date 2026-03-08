"""
API Gateway Deployment Script for Windows
Python version of deploy_api_gateway.sh
"""

import boto3
import os
import time
from dotenv import load_dotenv

load_dotenv()

def create_api_gateway():
    """Create and configure API Gateway"""
    
    region = os.getenv('AWS_REGION', 'ap-south-1')
    api_name = "AgriNexus API"
    stage_name = "prod"
    
    # Initialize clients
    apigateway = boto3.client(
        'apigateway',
        region_name=region,
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )
    
    lambda_client = boto3.client(
        'lambda',
        region_name=region,
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )
    
    sts = boto3.client(
        'sts',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )
    
    account_id = sts.get_caller_identity()['Account']
    
    print("=" * 80)
    print("API Gateway Deployment")
    print("=" * 80)
    print(f"Region: {region}")
    print(f"Account ID: {account_id}\n")
    
    # Step 1: Create REST API
    print("Step 1: Creating REST API...")
    try:
        api_response = apigateway.create_rest_api(
            name=api_name,
            description="REST API for Agri-Nexus V1 Platform"
        )
        api_id = api_response['id']
        print(f"✓ Created API: {api_id}\n")
    except Exception as e:
        print(f"API might exist, searching...")
        apis = apigateway.get_rest_apis()
        api_id = None
        for api in apis['items']:
            if api['name'] == api_name:
                api_id = api['id']
                break
        if not api_id:
            print(f"✗ Failed: {e}")
            return
        print(f"✓ Found existing API: {api_id}\n")
    
    # Step 2: Get root resource
    print("Step 2: Getting root resource...")
    resources = apigateway.get_resources(restApiId=api_id)
    root_id = resources['items'][0]['id']
    print(f"✓ Root ID: {root_id}\n")
    
    # Step 3: Create resources
    print("Step 3: Creating resources...")
    
    def create_resource(parent_id, path_part):
        try:
            # Check if exists
            resources = apigateway.get_resources(restApiId=api_id)
            for resource in resources['items']:
                if resource.get('pathPart') == path_part:
                    print(f"  ✓ /{path_part} exists: {resource['id']}")
                    return resource['id']
            
            # Create new
            response = apigateway.create_resource(
                restApiId=api_id,
                parentId=parent_id,
                pathPart=path_part
            )
            print(f"  ✓ Created /{path_part}: {response['id']}")
            return response['id']
        except Exception as e:
            print(f"  ✗ Error creating /{path_part}: {e}")
            return None
    
    diagnose_id = create_resource(root_id, 'diagnose')
    history_id = create_resource(root_id, 'history')
    diagnoses_id = create_resource(history_id, 'diagnoses') if history_id else None
    voice_id = create_resource(root_id, 'voice')
    voice_process_id = create_resource(voice_id, 'process') if voice_id else None
    voice_tts_id = create_resource(voice_id, 'tts') if voice_id else None
    market_id = create_resource(root_id, 'market')
    market_ingest_id = create_resource(market_id, 'ingest') if market_id else None
    
    print()
    
    # Step 4: Create methods and integrations
    print("Step 4: Creating methods and integrations...")
    
    def create_method_integration(resource_id, http_method, lambda_function, path):
        if not resource_id:
            print(f"  ✗ Skipping {http_method} {path} (resource not found)")
            return
        
        try:
            # Create method
            apigateway.put_method(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod=http_method,
                authorizationType='NONE'
            )
            
            # Create integration
            lambda_uri = f"arn:aws:apigateway:{region}:lambda:path/2015-03-31/functions/arn:aws:lambda:{region}:{account_id}:function:{lambda_function}/invocations"
            
            apigateway.put_integration(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod=http_method,
                type='AWS_PROXY',
                integrationHttpMethod='POST',
                uri=lambda_uri
            )
            
            # Grant permission
            try:
                lambda_client.add_permission(
                    FunctionName=lambda_function,
                    StatementId=f"apigateway-{path.replace('/', '-')}-{http_method}",
                    Action='lambda:InvokeFunction',
                    Principal='apigateway.amazonaws.com',
                    SourceArn=f"arn:aws:execute-api:{region}:{account_id}:{api_id}/*/{http_method}{path}"
                )
            except lambda_client.exceptions.ResourceConflictException:
                pass  # Permission already exists
            
            print(f"  ✓ {http_method} {path} → {lambda_function}")
        except Exception as e:
            print(f"  ✗ Error: {http_method} {path}: {e}")
    
    create_method_integration(diagnose_id, 'POST', 'analyze_crop_image', '/diagnose')
    create_method_integration(diagnoses_id, 'GET', 'get_diagnosis_history', '/history/diagnoses')
    create_method_integration(voice_process_id, 'POST', 'process_voice_input', '/voice/process')
    create_method_integration(voice_tts_id, 'POST', 'generate_voice_response', '/voice/tts')
    create_method_integration(market_ingest_id, 'POST', 'ingest_market_data', '/market/ingest')
    
    print()
    
    # Step 5: Deploy API
    print("Step 5: Deploying API...")
    try:
        apigateway.create_deployment(
            restApiId=api_id,
            stageName=stage_name
        )
        print(f"✓ Deployed to {stage_name} stage\n")
    except Exception as e:
        print(f"✗ Deployment error: {e}\n")
    
    # Step 6: Display results
    api_url = f"https://{api_id}.execute-api.{region}.amazonaws.com/{stage_name}"
    
    print("=" * 80)
    print("✓ API Gateway Deployment Complete!")
    print("=" * 80)
    print(f"\nAPI Gateway URL:")
    print(f"{api_url}")
    print(f"\nAvailable Endpoints:")
    print(f"  POST   {api_url}/diagnose")
    print(f"  GET    {api_url}/history/diagnoses")
    print(f"  POST   {api_url}/voice/process")
    print(f"  POST   {api_url}/voice/tts")
    print(f"  POST   {api_url}/market/ingest")
    print(f"\nNext Steps:")
    print(f"1. Update .env with: API_GATEWAY_URL={api_url}")
    print(f"2. Test endpoints with curl or Postman")
    print(f"3. Run: streamlit run frontend/streamlit_app.py")
    print()
    
    # Save to file
    with open('.api_gateway_url', 'w') as f:
        f.write(f"API_GATEWAY_URL={api_url}\n")
    
    return api_url


if __name__ == '__main__':
    create_api_gateway()

