"""
AWS Lambda Handler: generate_voice_response
Converts text responses to speech audio
"""

import json
import base64
import os
import sys
from datetime import datetime
import logging

# Add shared directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.bedrock_client import get_bedrock_client

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """
    Lambda handler for text-to-speech conversion
    
    Input event format:
    {
        "text": "string",
        "language": "string (en|bn|hi)"
    }
    
    Output format:
    {
        "audio_data": "string (base64)",
        "duration_seconds": float
    }
    """
    try:
        # Parse input
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event
        
        text = body.get('text')
        language = body.get('language', 'en')
        
        # Validate input
        if not text:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'text is required'})
            }
        
        logger.info(f"Converting text to speech, language: {language}, text length: {len(text)}")
        
        # Convert text to speech using Bedrock
        bedrock_client = get_bedrock_client()
        
        try:
            audio_bytes = bedrock_client.text_to_speech(
                text=text,
                language=language
            )
            logger.info(f"Text-to-speech conversion complete, audio size: {len(audio_bytes)} bytes")
        except Exception as e:
            logger.error(f"Text-to-speech conversion failed: {str(e)}")
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'error': 'Text-to-speech conversion failed',
                    'details': str(e)
                })
            }
        
        # Encode audio to base64
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        # Estimate duration (rough estimate: 150 words per minute)
        word_count = len(text.split())
        duration_seconds = (word_count / 150) * 60
        
        # Prepare response
        response_data = {
            'audio_data': audio_base64,
            'duration_seconds': round(duration_seconds, 2)
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
        'text': 'Hello, this is a test message for text-to-speech conversion.',
        'language': 'en'
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))
