"""
AWS SNS Client for SMS Notifications - Agri-Nexus V1 Platform
Handles SMS delivery with multilingual support and retry logic
"""

import boto3
import time
import logging
from typing import Dict, Optional

from .config import get_config

logger = logging.getLogger(__name__)


class SNSClient:
    """
    Wrapper for AWS SNS SMS operations with retry logic
    """
    
    def __init__(self):
        """Initialize SNS client"""
        config = get_config()
        self.sns = boto3.client('sns', region_name=config.aws_region)
        self.max_retries = config.max_sms_retries
        self.backoff_multiplier = 2
    
    def format_alert_message(
        self,
        crop_type: str,
        target_price: float,
        current_price: float,
        location: str,
        language: str = 'en'
    ) -> str:
        """
        Format alert message in specified language
        
        Args:
            crop_type: Type of crop
            target_price: Target price set by user
            current_price: Current market price
            location: Market location
            language: Message language (en, bn, hi)
            
        Returns:
            Formatted SMS message
        """
        templates = {
            'en': (
                f"Price Alert: {crop_type} has reached ₹{current_price:.2f}/quintal at {location}. "
                f"Your target was ₹{target_price:.2f}."
            ),
            'bn': (
                f"মূল্য সতর্কতা: {crop_type} {location} এ ₹{current_price:.2f}/কুইন্টাল পৌঁছেছে। "
                f"আপনার লক্ষ্য ছিল ₹{target_price:.2f}।"
            ),
            'hi': (
                f"मूल्य अलर्ट: {crop_type} {location} में ₹{current_price:.2f}/क्विंटल तक पहुंच गया है। "
                f"आपका लक्ष्य ₹{target_price:.2f} था।"
            )
        }
        
        return templates.get(language, templates['en'])
    
    def send_sms(
        self,
        phone_number: str,
        message: str,
        language: str = 'en'
    ) -> Dict:
        """
        Send SMS notification with retry logic
        
        Args:
            phone_number: Recipient phone number (E.164 format: +919876543210)
            message: SMS message text
            language: Message language
            
        Returns:
            Dictionary with status and message_id
        """
        for attempt in range(self.max_retries):
            try:
                response = self.sns.publish(
                    PhoneNumber=phone_number,
                    Message=message,
                    MessageAttributes={
                        'AWS.SNS.SMS.SMSType': {
                            'DataType': 'String',
                            'StringValue': 'Transactional'  # For critical alerts
                        }
                    }
                )
                
                message_id = response.get('MessageId')
                logger.info(f"SMS sent successfully to {phone_number}. MessageId: {message_id}")
                
                return {
                    'status': 'delivered',
                    'message_id': message_id,
                    'attempt': attempt + 1
                }
                
            except Exception as e:
                error_message = str(e)
                logger.error(f"SMS delivery failed (Attempt {attempt + 1}/{self.max_retries}): {error_message}")
                
                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    wait_time = (self.backoff_multiplier ** attempt)
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    # All retries failed
                    logger.error(f"All SMS delivery attempts failed for {phone_number}")
                    return {
                        'status': 'failed',
                        'error': error_message,
                        'attempt': attempt + 1
                    }
        
        return {
            'status': 'failed',
            'error': 'Max retries exceeded',
            'attempt': self.max_retries
        }
    
    def send_price_alert(
        self,
        phone_number: str,
        crop_type: str,
        target_price: float,
        current_price: float,
        location: str,
        language: str = 'en'
    ) -> Dict:
        """
        Send formatted price alert SMS
        
        Args:
            phone_number: Recipient phone number
            crop_type: Type of crop
            target_price: Target price set by user
            current_price: Current market price
            location: Market location
            language: Message language
            
        Returns:
            Dictionary with delivery status
        """
        message = self.format_alert_message(
            crop_type=crop_type,
            target_price=target_price,
            current_price=current_price,
            location=location,
            language=language
        )
        
        return self.send_sms(phone_number, message, language)
    
    def retry_failed_sms(
        self,
        notification_id: str,
        phone_number: str,
        message: str,
        max_retries: int = 3
    ) -> Dict:
        """
        Retry failed SMS delivery
        
        Args:
            notification_id: Notification identifier
            phone_number: Recipient phone number
            message: SMS message
            max_retries: Maximum retry attempts
            
        Returns:
            Dictionary with delivery status
        """
        logger.info(f"Retrying SMS delivery for notification {notification_id}")
        
        # Override max_retries for this specific retry
        original_max_retries = self.max_retries
        self.max_retries = max_retries
        
        result = self.send_sms(phone_number, message)
        
        # Restore original max_retries
        self.max_retries = original_max_retries
        
        return result


# Global client instance
_sns_client: SNSClient = None


def get_sns_client() -> SNSClient:
    """Get the global SNS client instance"""
    global _sns_client
    
    if _sns_client is None:
        _sns_client = SNSClient()
    
    return _sns_client


if __name__ == '__main__':
    # Test SNS client
    client = get_sns_client()
    print("SNS Client initialized successfully")
    print(f"Max retries: {client.max_retries}")
    
    # Test message formatting
    message_en = client.format_alert_message(
        crop_type="Wheat",
        target_price=2500.0,
        current_price=2550.0,
        location="Delhi",
        language="en"
    )
    print(f"\nEnglish message: {message_en}")
    
    message_hi = client.format_alert_message(
        crop_type="गेहूं",
        target_price=2500.0,
        current_price=2550.0,
        location="दिल्ली",
        language="hi"
    )
    print(f"Hindi message: {message_hi}")
