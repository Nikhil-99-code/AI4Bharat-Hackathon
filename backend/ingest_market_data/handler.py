"""
AWS Lambda Handler: ingest_market_data
Ingests market price data and triggers alert checking
"""

import json
import boto3
import os
import sys
from datetime import datetime
import random
import logging

# Add shared directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.dynamodb_repository import get_repository
from shared.config import get_config

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """
    Lambda handler for market data ingestion
    
    Input event format:
    {
        "crop_type": "string",
        "location": "string",
        "price": float,
        "timestamp": "string (ISO 8601, optional)",
        "simulation": bool (optional)
    }
    
    Output format:
    {
        "market_data_id": "string",
        "alerts_triggered": int
    }
    """
    try:
        # Parse input
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event
        
        crop_type = body.get('crop_type')
        location = body.get('location')
        price = body.get('price')
        timestamp = body.get('timestamp', datetime.utcnow().isoformat())
        simulation = body.get('simulation', False)
        
        # Validate input
        if not crop_type:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'crop_type is required'})
            }
        
        if not location:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'location is required'})
            }
        
        if price is None:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'price is required'})
            }
        
        logger.info(f"Ingesting market data: {crop_type} at {location}, price: {price}, simulation: {simulation}")
        
        # If simulation mode, generate random price variation
        if simulation:
            # Add random variation of ±10%
            variation = random.uniform(-0.1, 0.1)
            price = price * (1 + variation)
            logger.info(f"Simulation mode: adjusted price to {price}")
        
        # Store market data in DynamoDB
        repository = get_repository()
        
        market_data = {
            'crop_type': crop_type,
            'location': location,
            'price': price,
            'timestamp': timestamp,
            'source': 'simulation' if simulation else 'manual'
        }
        
        try:
            market_data_id = repository.store_market_data(market_data)
            logger.info(f"Market data stored: {market_data_id}")
        except Exception as e:
            logger.error(f"Failed to store market data: {str(e)}")
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'error': 'Failed to store market data',
                    'details': str(e)
                })
            }
        
        # Trigger alert checking by invoking trigger_alerts Lambda
        config = get_config()
        lambda_client = boto3.client('lambda', region_name=config.aws_region)
        
        trigger_payload = {
            'crop_type': crop_type,
            'location': location,
            'current_price': price
        }
        
        alerts_triggered = 0
        
        try:
            # Invoke trigger_alerts Lambda asynchronously
            response = lambda_client.invoke(
                FunctionName='trigger_alerts',  # Update with actual function name
                InvocationType='Event',  # Asynchronous invocation
                Payload=json.dumps(trigger_payload)
            )
            logger.info(f"Triggered alert checking, status: {response['StatusCode']}")
            
            # For simulation, we can estimate alerts triggered
            # In production, this would come from the trigger_alerts response
            if simulation:
                # Query active thresholds to estimate
                thresholds = repository.get_active_thresholds(crop_type, location)
                alerts_triggered = sum(1 for t in thresholds if t.get('target_price', 0) <= price)
                logger.info(f"Estimated alerts triggered: {alerts_triggered}")
            
        except Exception as e:
            logger.error(f"Failed to trigger alert checking: {str(e)}")
            # Continue even if alert triggering fails
        
        # Prepare response
        response_data = {
            'market_data_id': market_data_id,
            'alerts_triggered': alerts_triggered,
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
        'crop_type': 'Wheat',
        'location': 'Delhi',
        'price': 2550.0,
        'simulation': True
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))
