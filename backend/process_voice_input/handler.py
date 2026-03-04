"""
AWS Lambda Handler: process_voice_input
Processes voice input, transcribes, and generates contextual responses
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


def lambda_handler(event, context):
    """
    Lambda handler for voice input processing
    
    Input event format:
    {
        "user_id": "string",
        "audio_data": "string (base64)",
        "language": "string (en|bn|hi)"
    }
    
    Output format:
    {
        "interaction_id": "string",
        "transcript": "string",
        "response_text": "string",
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
        audio_data_base64 = body.get('audio_data')
        language = body.get('language', 'en')
        
        # Validate input
        if not user_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'user_id is required'})
            }
        
        if not audio_data_base64:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'audio_data is required'})
            }
        
        logger.info(f"Processing voice input for user: {user_id}, language: {language}")
        
        # Decode audio
        try:
            audio_bytes = base64.b64decode(audio_data_base64)
        except Exception as e:
            logger.error(f"Failed to decode audio: {str(e)}")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Invalid base64 audio data'})
            }
        
        # Store audio in S3 (optional)
        config = get_config()
        s3_client = boto3.client('s3', region_name=config.aws_region)
        timestamp = datetime.utcnow().isoformat()
        s3_key = f"audio/{user_id}/{timestamp}.wav"
        
        try:
            s3_client.put_object(
                Bucket=config.image_bucket,
                Key=s3_key,
                Body=audio_bytes,
                ContentType='audio/wav'
            )
            logger.info(f"Audio stored in S3: {s3_key}")
        except Exception as e:
            logger.error(f"Failed to store audio in S3: {str(e)}")
            s3_key = None
        
        # Transcribe audio using Bedrock
        bedrock_client = get_bedrock_client()
        
        try:
            transcript = bedrock_client.transcribe_audio(
                audio_bytes=audio_bytes,
                language=language
            )
            logger.info(f"Audio transcribed: {transcript}")
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'error': 'Transcription failed',
                    'details': str(e)
                })
            }
        
        # Generate contextual response using Bedrock
        try:
            response_text = bedrock_client.generate_response(
                prompt=transcript,
                context="You are helping a farmer with agricultural questions.",
                language=language
            )
            logger.info(f"Response generated: {response_text[:100]}...")
        except Exception as e:
            logger.error(f"Response generation failed: {str(e)}")
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'error': 'Response generation failed',
                    'details': str(e)
                })
            }
        
        # Store interaction in DynamoDB
        repository = get_repository()
        
        interaction_data = {
            'transcript': transcript,
            'response_text': response_text,
            'audio_s3_key': s3_key,
            'language': language
        }
        
        try:
            interaction_id = repository.store_interaction(user_id, interaction_data)
            logger.info(f"Interaction stored in DynamoDB: {interaction_id}")
        except Exception as e:
            logger.error(f"Failed to store interaction in DynamoDB: {str(e)}")
            interaction_id = f"INTERACTION#{timestamp}"
        
        # Prepare response
        response_data = {
            'interaction_id': interaction_id,
            'transcript': transcript,
            'response_text': response_text,
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
    test_event = {
        'user_id': 'test_user',
        'audio_data': '',  # Add base64 audio data here for testing
        'language': 'en'
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))
