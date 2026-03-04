"""
AWS Lambda Handler: analyze_crop_image
Analyzes crop images for disease diagnosis using AWS Bedrock
"""

import json
import base64
import boto3
import os
import sys
from datetime import datetime
import logging

# Add shared directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.bedrock_client import get_bedrock_client
from shared.dynamodb_repository import get_repository
from shared.config import get_config

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def construct_diagnosis_prompt(language: str = 'en') -> str:
    """
    Construct structured prompt for Bedrock diagnosis
    
    Args:
        language: Response language (en, bn, hi)
        
    Returns:
        Formatted prompt string
    """
    language_instructions = {
        'en': 'Provide the response in English.',
        'hi': 'Provide the response in Hindi.',
        'bn': 'Provide the response in Bengali.'
    }
    
    prompt = f"""You are an expert agricultural pathologist. Analyze the provided crop image and diagnose any diseases.

Return your response in the following JSON format:
{{
  "disease_name": "Name of the disease or 'Healthy' if no disease detected",
  "confidence": <percentage between 0 and 100>,
  "treatment": "Detailed treatment recommendation"
}}

{language_instructions.get(language, language_instructions['en'])}

Important:
- Be specific about the disease name
- Provide confidence as a number between 0 and 100
- Give practical, actionable treatment recommendations
- If the image is unclear or not a crop, indicate this in the disease_name

Return ONLY the JSON object, no additional text."""
    
    return prompt


def lambda_handler(event, context):
    """
    Lambda handler for crop image analysis
    
    Input event format:
    {
        "user_id": "string",
        "image_data": "string (base64)",
        "language": "string (en|bn|hi)"
    }
    
    Output format:
    {
        "diagnosis_id": "string",
        "disease_name": "string",
        "confidence": float,
        "treatment": "string",
        "timestamp": "string (ISO 8601)"
    }
    """
    try:
        # Parse input
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event
        
        user_id = body.get('user_id')
        image_data_base64 = body.get('image_data')
        language = body.get('language', 'en')
        
        # Validate input
        if not user_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'user_id is required'})
            }
        
        if not image_data_base64:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'image_data is required'})
            }
        
        logger.info(f"Processing diagnosis request for user: {user_id}, language: {language}")
        
        # Decode image
        try:
            image_bytes = base64.b64decode(image_data_base64)
        except Exception as e:
            logger.error(f"Failed to decode image: {str(e)}")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Invalid base64 image data'})
            }
        
        # Store image in S3
        config = get_config()
        s3_client = boto3.client('s3', region_name=config.aws_region)
        timestamp = datetime.utcnow().isoformat()
        s3_key = f"images/{user_id}/{timestamp}.jpg"
        
        try:
            s3_client.put_object(
                Bucket=config.image_bucket,
                Key=s3_key,
                Body=image_bytes,
                ContentType='image/jpeg'
            )
            logger.info(f"Image stored in S3: {s3_key}")
        except Exception as e:
            logger.error(f"Failed to store image in S3: {str(e)}")
            # Continue with diagnosis even if S3 upload fails
            s3_key = None
        
        # Construct prompt
        prompt = construct_diagnosis_prompt(language)
        
        # Analyze image with Bedrock
        bedrock_client = get_bedrock_client()
        
        try:
            diagnosis_result = bedrock_client.analyze_image(
                image_bytes=image_bytes,
                prompt=prompt,
                language=language
            )
            logger.info(f"Bedrock analysis complete: {diagnosis_result}")
        except Exception as e:
            logger.error(f"Bedrock analysis failed: {str(e)}")
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'error': 'Diagnosis failed',
                    'details': str(e)
                })
            }
        
        # Validate diagnosis result
        required_fields = ['disease_name', 'confidence', 'treatment']
        for field in required_fields:
            if field not in diagnosis_result:
                logger.error(f"Missing required field in diagnosis: {field}")
                return {
                    'statusCode': 500,
                    'body': json.dumps({
                        'error': 'Invalid diagnosis response',
                        'details': f'Missing field: {field}'
                    })
                }
        
        # Ensure confidence is a number between 0 and 100
        try:
            confidence = float(diagnosis_result['confidence'])
            if confidence < 0 or confidence > 100:
                confidence = max(0, min(100, confidence))
        except (ValueError, TypeError):
            confidence = 50.0  # Default if invalid
        
        # Store diagnosis in DynamoDB
        repository = get_repository()
        
        diagnosis_data = {
            'disease_name': diagnosis_result['disease_name'],
            'confidence': confidence,
            'treatment': diagnosis_result['treatment'],
            'image_s3_key': s3_key,
            'language': language
        }
        
        try:
            diagnosis_id = repository.store_diagnosis(user_id, diagnosis_data)
            logger.info(f"Diagnosis stored in DynamoDB: {diagnosis_id}")
        except Exception as e:
            logger.error(f"Failed to store diagnosis in DynamoDB: {str(e)}")
            # Continue and return result even if storage fails
            diagnosis_id = f"DIAGNOSIS#{timestamp}"
        
        # Prepare response
        response_data = {
            'diagnosis_id': diagnosis_id,
            'disease_name': diagnosis_result['disease_name'],
            'confidence': confidence,
            'treatment': diagnosis_result['treatment'],
            'timestamp': timestamp
        }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(response_data)
        }
        
    except Exception as e:
        logger.error(f"Unexpected error in lambda_handler: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Internal server error',
                'details': str(e)
            })
        }


# For local testing
if __name__ == '__main__':
    # Test event
    test_event = {
        'user_id': 'test_user',
        'image_data': '',  # Add base64 image data here for testing
        'language': 'en'
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))
