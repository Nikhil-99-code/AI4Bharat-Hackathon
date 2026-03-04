"""
AWS Lambda Handler: trigger_alerts
Checks price thresholds and sends SMS notifications
"""

import json
import os
import sys
from datetime import datetime
import logging

# Add shared directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.dynamodb_repository import get_repository
from shared.sns_client import get_sns_client

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """
    Lambda handler for alert triggering
    
    Input event format:
    {
        "crop_type": "string",
        "location": "string",
        "current_price": float
    }
    
    Output format:
    {
        "alerts_triggered": int,
        "notifications_sent": int,
        "failures": list
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
        current_price = body.get('current_price')
        
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
        
        if current_price is None:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'current_price is required'})
            }
        
        logger.info(f"Checking alerts for {crop_type} at {location}, price: {current_price}")
        
        # Query active price thresholds using GSI3
        repository = get_repository()
        
        try:
            thresholds = repository.get_active_thresholds(crop_type, location)
            logger.info(f"Found {len(thresholds)} active thresholds")
        except Exception as e:
            logger.error(f"Failed to query thresholds: {str(e)}")
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'error': 'Failed to query thresholds',
                    'details': str(e)
                })
            }
        
        # Compare current price against thresholds
        alerts_triggered = 0
        notifications_sent = 0
        failures = []
        
        sns_client = get_sns_client()
        processed_users = set()  # Deduplication
        
        for threshold in thresholds:
            target_price = threshold.get('target_price', 0)
            user_id = threshold.get('PK', '').replace('USER#', '')
            phone_number = threshold.get('phone_number')
            language = threshold.get('language', 'en')
            
            # Check if price meets or exceeds target
            if current_price >= target_price:
                alerts_triggered += 1
                
                # Deduplication: process each user only once per price update
                if user_id in processed_users:
                    logger.info(f"Skipping duplicate alert for user {user_id}")
                    continue
                
                processed_users.add(user_id)
                
                logger.info(f"Alert triggered for user {user_id}: target={target_price}, current={current_price}")
                
                # Store notification trigger in DynamoDB
                trigger_data = {
                    'crop_type': crop_type,
                    'location': location,
                    'target_price': target_price,
                    'current_price': current_price,
                    'sms_status': 'pending',
                    'retry_count': 0
                }
                
                try:
                    notification_id = repository.store_notification_trigger(user_id, trigger_data)
                    logger.info(f"Notification trigger stored: {notification_id}")
                except Exception as e:
                    logger.error(f"Failed to store notification trigger: {str(e)}")
                    failures.append({
                        'user_id': user_id,
                        'error': 'Failed to store notification',
                        'details': str(e)
                    })
                    continue
                
                # Send SMS notification
                if phone_number:
                    try:
                        sms_result = sns_client.send_price_alert(
                            phone_number=phone_number,
                            crop_type=crop_type,
                            target_price=target_price,
                            current_price=current_price,
                            location=location,
                            language=language
                        )
                        
                        if sms_result.get('status') == 'delivered':
                            notifications_sent += 1
                            logger.info(f"SMS sent successfully to {phone_number}")
                            
                            # Update notification status in DynamoDB
                            trigger_data['sms_status'] = 'delivered'
                            repository.store_notification_trigger(user_id, trigger_data)
                        else:
                            logger.error(f"SMS delivery failed: {sms_result}")
                            failures.append({
                                'user_id': user_id,
                                'phone_number': phone_number,
                                'error': 'SMS delivery failed',
                                'details': sms_result.get('error', 'Unknown error')
                            })
                            
                            # Update notification status
                            trigger_data['sms_status'] = 'failed'
                            trigger_data['retry_count'] = sms_result.get('attempt', 0)
                            repository.store_notification_trigger(user_id, trigger_data)
                    
                    except Exception as e:
                        logger.error(f"Failed to send SMS: {str(e)}")
                        failures.append({
                            'user_id': user_id,
                            'phone_number': phone_number,
                            'error': 'SMS sending exception',
                            'details': str(e)
                        })
                else:
                    logger.warning(f"No phone number for user {user_id}")
                    failures.append({
                        'user_id': user_id,
                        'error': 'No phone number configured'
                    })
        
        # Prepare response
        response_data = {
            'alerts_triggered': alerts_triggered,
            'notifications_sent': notifications_sent,
            'failures': failures
        }
        
        logger.info(f"Alert processing complete: {response_data}")
        
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
        'current_price': 2550.0
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))
