"""
Lambda handler for retrieving diagnosis history
"""

import json
import sys
import os
from typing import Dict

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.dynamodb_repository import get_repository
from shared.error_handler import ErrorCode, handle_error


def lambda_handler(event: dict, context) -> dict:
    """
    Get diagnosis history for a user
    
    Input (query parameters):
    {
        "user_id": str,
        "limit": int (optional, default: 20)
    }
    
    Output:
    {
        "diagnoses": [
            {
                "diagnosis_id": str,
                "disease_name": str,
                "confidence": float,
                "treatment": str,
                "timestamp": str,
                "created_at": str
            }
        ]
    }
    """
    try:
        # Parse query parameters
        query_params = event.get('queryStringParameters', {}) or {}
        user_id = query_params.get('user_id')
        limit = int(query_params.get('limit', 20))
        
        # Validate required parameters
        if not user_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': {
                        'code': 'INVALID_REQUEST',
                        'message': 'user_id is required'
                    }
                })
            }
        
        # Get repository
        repository = get_repository()
        
        # Retrieve diagnosis history
        diagnoses = repository.get_diagnosis_history(user_id, limit)
        
        # Format response
        formatted_diagnoses = []
        for diagnosis in diagnoses:
            formatted_diagnoses.append({
                'diagnosis_id': diagnosis.get('SK', ''),
                'disease_name': diagnosis.get('disease_name', 'Unknown'),
                'confidence': float(diagnosis.get('confidence', 0)),
                'treatment': diagnosis.get('treatment', ''),
                'timestamp': diagnosis.get('created_at', ''),
                'created_at': diagnosis.get('created_at', ''),
                'image_s3_key': diagnosis.get('image_s3_key', '')
            })
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'diagnoses': formatted_diagnoses,
                'count': len(formatted_diagnoses)
            })
        }
        
    except Exception as e:
        # Handle errors
        error_info = handle_error(
            error=e,
            error_code=ErrorCode.STORAGE_FAILED,
            language='en',
            context={'operation': 'get_diagnosis_history'},
            user_id=user_id if 'user_id' in locals() else None
        )
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': {
                    'code': error_info['error_code'],
                    'message': error_info['message']
                }
            })
        }


# For local testing
if __name__ == '__main__':
    # Test event
    test_event = {
        'queryStringParameters': {
            'user_id': 'demo_user',
            'limit': '20'
        }
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))
