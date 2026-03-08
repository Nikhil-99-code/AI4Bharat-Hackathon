"""
Quick test script to verify AWS Bedrock setup
"""

import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv()

def test_bedrock_connection():
    """Test Bedrock connection and model access"""
    
    print("=" * 80)
    print("AWS Bedrock Setup Test")
    print("=" * 80)
    
    # Get configuration
    region = os.getenv('AWS_REGION', 'ap-south-1')
    model_id = os.getenv('BEDROCK_MODEL_ID', 'apac.anthropic.claude-3-5-sonnet-20241022-v2:0')
    
    print(f"\n1. Configuration:")
    print(f"   Region: {region}")
    print(f"   Model ID: {model_id}")
    print(f"   AWS Access Key: {os.getenv('AWS_ACCESS_KEY_ID', 'NOT SET')[:20]}...")
    
    try:
        # Create Bedrock client
        print(f"\n2. Creating Bedrock Runtime client...")
        bedrock_runtime = boto3.client(
            'bedrock-runtime',
            region_name=region,
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        print("   ✅ Client created successfully")
        
        # Test simple text generation
        print(f"\n3. Testing model invocation...")
        print(f"   Sending test prompt to {model_id}...")
        
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 100,
            "temperature": 0.2,
            "messages": [
                {
                    "role": "user",
                    "content": "Say 'Hello, Bedrock is working!' in one sentence."
                }
            ]
        }
        
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body)
        )
        
        # Parse response
        response_body = json.loads(response['body'].read())
        response_text = response_body['content'][0]['text']
        
        print("   ✅ Model invocation successful!")
        print(f"\n4. Model Response:")
        print(f"   {response_text}")
        
        # Check model access
        print(f"\n5. Checking model access permissions...")
        bedrock = boto3.client(
            'bedrock',
            region_name=region,
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        
        try:
            # List foundation models
            models_response = bedrock.list_foundation_models()
            available_models = [m['modelId'] for m in models_response.get('modelSummaries', [])]
            
            print(f"   ✅ Found {len(available_models)} available models in {region}")
            
            # Check if our model is available
            if model_id in available_models:
                print(f"   ✅ Model {model_id} is available!")
            else:
                print(f"   ⚠️  Model {model_id} not found in available models")
                print(f"   Available Claude models:")
                for m in available_models:
                    if 'claude' in m.lower():
                        print(f"      - {m}")
        except Exception as e:
            print(f"   ⚠️  Could not list models: {str(e)}")
            print(f"   (This is OK if you don't have bedrock:ListFoundationModels permission)")
        
        print("\n" + "=" * 80)
        print("✅ BEDROCK SETUP TEST PASSED!")
        print("=" * 80)
        print("\nYour Bedrock setup is working correctly!")
        print("You can now use the Agri-Nexus platform for crop diagnosis.")
        
        return True
        
    except Exception as e:
        print("\n" + "=" * 80)
        print("❌ BEDROCK SETUP TEST FAILED!")
        print("=" * 80)
        print(f"\nError: {str(e)}")
        print("\nPossible issues:")
        print("1. Model not enabled in AWS Bedrock console")
        print("2. IAM user missing bedrock:InvokeModel permission")
        print("3. Model not available in your region")
        print("4. Incorrect model ID in .env file")
        
        print("\nTo fix:")
        print("1. Go to AWS Console → Bedrock → Model access")
        print("2. Request access to Claude 3.5 Sonnet model")
        print("3. Add bedrock:InvokeModel permission to your IAM user")
        print(f"4. Verify model is available in {region} region")
        
        return False


if __name__ == '__main__':
    test_bedrock_connection()
