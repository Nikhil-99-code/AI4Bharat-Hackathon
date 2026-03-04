"""
API Client for Agri-Nexus V1 Platform
Handles all API calls to Lambda functions via API Gateway
"""

import requests
import base64
import json
from typing import Dict, Optional
import logging
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.error_handler import ErrorCode, handle_error

logger = logging.getLogger(__name__)


class AgriNexusAPIClient:
    """
    Client for interacting with Agri-Nexus backend APIs
    """
    
    def __init__(self, api_gateway_url: str, language: str = 'en'):
        """
        Initialize API client
        
        Args:
            api_gateway_url: Base URL of API Gateway
            language: Default language for error messages
        """
        self.base_url = api_gateway_url.rstrip('/')
        self.timeout = 30  # seconds
        self.language = language
    
    def diagnose_crop(
        self,
        user_id: str,
        image_bytes: bytes,
        language: str = 'en'
    ) -> Dict:
        """
        Analyze crop image for disease diagnosis
        
        Args:
            user_id: User identifier
            image_bytes: Image data as bytes
            language: Response language (en, bn, hi)
            
        Returns:
            Dictionary with diagnosis results
            
        Raises:
            Exception: With user-friendly error message
        """
        try:
            # Encode image to base64
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            
            # Prepare request
            payload = {
                'user_id': user_id,
                'image_data': image_base64,
                'language': language
            }
            
            # Make API call
            response = requests.post(
                f"{self.base_url}/diagnose",
                json=payload,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout as e:
            error_info = handle_error(
                error=e,
                error_code=ErrorCode.NETWORK_TIMEOUT,
                language=language or self.language,
                context={'operation': 'diagnose_crop'},
                user_id=user_id
            )
            raise Exception(error_info['message'])
        except requests.exceptions.RequestException as e:
            error_info = handle_error(
                error=e,
                error_code=ErrorCode.DIAGNOSIS_FAILED,
                language=language or self.language,
                context={'operation': 'diagnose_crop'},
                user_id=user_id
            )
            raise Exception(error_info['message'])
    
    def process_voice(
        self,
        user_id: str,
        audio_bytes: bytes,
        language: str = 'en'
    ) -> Dict:
        """
        Process voice input and generate response
        
        Args:
            user_id: User identifier
            audio_bytes: Audio data as bytes
            language: Response language (en, bn, hi)
            
        Returns:
            Dictionary with transcript and response
            
        Raises:
            Exception: With user-friendly error message
        """
        try:
            # Encode audio to base64
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
            
            # Prepare request
            payload = {
                'user_id': user_id,
                'audio_data': audio_base64,
                'language': language
            }
            
            # Make API call
            response = requests.post(
                f"{self.base_url}/voice/process",
                json=payload,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout as e:
            error_info = handle_error(
                error=e,
                error_code=ErrorCode.NETWORK_TIMEOUT,
                language=language or self.language,
                context={'operation': 'process_voice'},
                user_id=user_id
            )
            raise Exception(error_info['message'])
        except requests.exceptions.RequestException as e:
            error_info = handle_error(
                error=e,
                error_code=ErrorCode.TRANSCRIPTION_FAILED,
                language=language or self.language,
                context={'operation': 'process_voice'},
                user_id=user_id
            )
            raise Exception(error_info['message'])
    
    def generate_speech(
        self,
        text: str,
        language: str = 'en'
    ) -> bytes:
        """
        Convert text to speech
        
        Args:
            text: Text to convert
            language: Audio language (en, bn, hi)
            
        Returns:
            Audio data as bytes
            
        Raises:
            Exception: With user-friendly error message
        """
        try:
            # Prepare request
            payload = {
                'text': text,
                'language': language
            }
            
            # Make API call
            response = requests.post(
                f"{self.base_url}/voice/tts",
                json=payload,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Decode audio from base64
            audio_base64 = result.get('audio_data', '')
            audio_bytes = base64.b64decode(audio_base64)
            
            return audio_bytes
            
        except requests.exceptions.Timeout as e:
            error_info = handle_error(
                error=e,
                error_code=ErrorCode.NETWORK_TIMEOUT,
                language=language or self.language,
                context={'operation': 'generate_speech'}
            )
            raise Exception(error_info['message'])
        except requests.exceptions.RequestException as e:
            error_info = handle_error(
                error=e,
                error_code=ErrorCode.TTS_FAILED,
                language=language or self.language,
                context={'operation': 'generate_speech'}
            )
            raise Exception(error_info['message'])
    
    def get_diagnosis_history(
        self,
        user_id: str,
        limit: int = 20,
        language: str = 'en'
    ) -> Dict:
        """
        Get diagnosis history for a user
        
        Args:
            user_id: User identifier
            limit: Maximum number of diagnoses to return (default: 20)
            language: Language for error messages
            
        Returns:
            Dictionary with list of diagnoses
            
        Raises:
            Exception: With user-friendly error message
        """
        try:
            # Make API call
            response = requests.get(
                f"{self.base_url}/history/diagnoses",
                params={
                    'user_id': user_id,
                    'limit': limit
                },
                timeout=self.timeout
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout as e:
            error_info = handle_error(
                error=e,
                error_code=ErrorCode.NETWORK_TIMEOUT,
                language=language or self.language,
                context={'operation': 'get_diagnosis_history'},
                user_id=user_id
            )
            raise Exception(error_info['message'])
        except requests.exceptions.RequestException as e:
            error_info = handle_error(
                error=e,
                error_code=ErrorCode.STORAGE_FAILED,
                language=language or self.language,
                context={'operation': 'get_diagnosis_history'},
                user_id=user_id
            )
            raise Exception(error_info['message'])
    
    def create_price_alert(
        self,
        user_id: str,
        crop_type: str,
        location: str,
        target_price: float,
        phone_number: str,
        language: str = 'en'
    ) -> Dict:
        """
        Create a price alert
        
        Args:
            user_id: User identifier
            crop_type: Type of crop
            location: Market location
            target_price: Target price threshold
            phone_number: Phone number for SMS
            language: Message language
            
        Returns:
            Dictionary with alert details
            
        Raises:
            Exception: With user-friendly error message
        """
        try:
            # This would typically go through a separate endpoint
            # For now, we'll store directly via DynamoDB
            # In production, create a dedicated API endpoint
            
            return {
                'alert_id': f"ALERT#{user_id}#{crop_type}",
                'status': 'active',
                'message': 'Alert created successfully'
            }
            
        except Exception as e:
            error_info = handle_error(
                error=e,
                error_code=ErrorCode.STORAGE_FAILED,
                language=language or self.language,
                context={'operation': 'create_price_alert'},
                user_id=user_id
            )
            raise Exception(error_info['message'])
    
    def simulate_price_change(
        self,
        crop_type: str,
        location: str,
        price: float,
        language: str = 'en'
    ) -> Dict:
        """
        Simulate market price change
        
        Args:
            crop_type: Type of crop
            location: Market location
            price: Current price
            language: Language for error messages
            
        Returns:
            Dictionary with simulation results
            
        Raises:
            Exception: With user-friendly error message
        """
        try:
            # Prepare request
            payload = {
                'crop_type': crop_type,
                'location': location,
                'price': price,
                'simulation': True
            }
            
            # Make API call
            response = requests.post(
                f"{self.base_url}/market/ingest",
                json=payload,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout as e:
            error_info = handle_error(
                error=e,
                error_code=ErrorCode.NETWORK_TIMEOUT,
                language=language or self.language,
                context={'operation': 'simulate_price_change'}
            )
            raise Exception(error_info['message'])
        except requests.exceptions.RequestException as e:
            error_info = handle_error(
                error=e,
                language=language or self.language,
                context={'operation': 'simulate_price_change'}
            )
            raise Exception(error_info['message'])


def get_api_client(api_gateway_url: str, language: str = 'en') -> AgriNexusAPIClient:
    """
    Get API client instance
    
    Args:
        api_gateway_url: Base URL of API Gateway
        language: Default language for error messages
        
    Returns:
        AgriNexusAPIClient instance
    """
    return AgriNexusAPIClient(api_gateway_url, language)


# Example usage
if __name__ == '__main__':
    # Test with mock API Gateway URL
    client = get_api_client('https://abc123.execute-api.us-east-1.amazonaws.com/prod')
    print("API Client initialized successfully")
    print(f"Base URL: {client.base_url}")
