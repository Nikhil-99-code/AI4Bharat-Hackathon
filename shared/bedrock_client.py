"""
AWS Bedrock Client Wrapper for Agri-Nexus V1 Platform
Handles image analysis, transcription, text generation, and text-to-speech
"""

import boto3
import json
import time
import base64
from typing import Dict, Optional
import logging

from .config import get_config

logger = logging.getLogger(__name__)


class BedrockClient:
    """
    Wrapper for AWS Bedrock API operations with retry logic
    """
    
    def __init__(self):
        """Initialize Bedrock client"""
        config = get_config()
        self.bedrock_runtime = boto3.client(
            'bedrock-runtime',
            region_name=config.aws_region
        )
        self.model_id = config.bedrock_model_id
        self.temperature = config.bedrock_temperature
        self.max_tokens = config.bedrock_max_tokens
        self.max_retries = 3
        self.backoff_multiplier = 2
    
    def _retry_with_backoff(self, func, *args, **kwargs):
        """
        Execute function with exponential backoff retry logic
        
        Args:
            func: Function to execute
            *args, **kwargs: Arguments to pass to function
            
        Returns:
            Function result
            
        Raises:
            Exception: If all retries fail
        """
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_message = str(e)
                
                # Check if it's a rate limiting error
                if 'ThrottlingException' in error_message or 'TooManyRequestsException' in error_message:
                    if attempt < self.max_retries - 1:
                        wait_time = (self.backoff_multiplier ** attempt)
                        logger.warning(f"Rate limited. Retrying in {wait_time} seconds... (Attempt {attempt + 1}/{self.max_retries})")
                        time.sleep(wait_time)
                        continue
                
                # If not rate limiting or last attempt, raise the error
                if attempt == self.max_retries - 1:
                    logger.error(f"All retry attempts failed: {error_message}")
                    raise
                
                # For other errors, retry with backoff
                wait_time = (self.backoff_multiplier ** attempt)
                logger.warning(f"Error occurred. Retrying in {wait_time} seconds... (Attempt {attempt + 1}/{self.max_retries})")
                time.sleep(wait_time)
    
    def analyze_image(self, image_bytes: bytes, prompt: str, language: str = 'en') -> Dict:
        """
        Analyze crop image and return diagnosis
        
        Args:
            image_bytes: Image data as bytes
            prompt: Analysis prompt
            language: Response language (en, bn, hi)
            
        Returns:
            Dictionary containing disease_name, confidence, and treatment
        """
        
        def _invoke():
            # Encode image to base64
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            
            # Construct the request body
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": image_base64
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            }
            
            # Invoke Bedrock
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            content = response_body.get('content', [])
            
            if content and len(content) > 0:
                text_content = content[0].get('text', '')
                
                # Try to parse as JSON
                try:
                    # Extract JSON from markdown code blocks if present
                    if '```json' in text_content:
                        json_start = text_content.find('```json') + 7
                        json_end = text_content.find('```', json_start)
                        text_content = text_content[json_start:json_end].strip()
                    elif '```' in text_content:
                        json_start = text_content.find('```') + 3
                        json_end = text_content.find('```', json_start)
                        text_content = text_content[json_start:json_end].strip()
                    
                    result = json.loads(text_content)
                    return result
                except json.JSONDecodeError:
                    # If not valid JSON, try to extract structured data
                    logger.warning("Response is not valid JSON, attempting to parse")
                    return self._parse_unstructured_response(text_content)
            
            raise ValueError("No content in Bedrock response")
        
        return self._retry_with_backoff(_invoke)
    
    def _parse_unstructured_response(self, text: str) -> Dict:
        """
        Attempt to parse unstructured text response into structured format
        
        Args:
            text: Unstructured text response
            
        Returns:
            Dictionary with disease_name, confidence, and treatment
        """
        # Simple parsing logic - can be enhanced
        result = {
            "disease_name": "Unknown",
            "confidence": 50.0,
            "treatment": text
        }
        
        # Try to extract disease name
        if "disease" in text.lower():
            lines = text.split('\n')
            for line in lines:
                if "disease" in line.lower():
                    result["disease_name"] = line.split(':')[-1].strip()
                    break
        
        return result
    
    def transcribe_audio(self, audio_bytes: bytes, language: str = 'en') -> str:
        """
        Convert speech to text (Note: Bedrock doesn't directly support audio transcription,
        this is a placeholder for integration with Amazon Transcribe or similar service)
        
        Args:
            audio_bytes: Audio data as bytes
            language: Audio language
            
        Returns:
            Transcribed text
        """
        # TODO: Integrate with Amazon Transcribe
        # For now, return a placeholder
        logger.warning("Audio transcription not yet implemented - using placeholder")
        return "Sample transcribed text from audio"
    
    def generate_response(self, prompt: str, context: str = "", language: str = 'en') -> str:
        """
        Generate contextual text response
        
        Args:
            prompt: User prompt/question
            context: Additional context for the response
            language: Response language
            
        Returns:
            Generated text response
        """
        
        def _invoke():
            # Construct system prompt with agricultural domain expertise
            system_prompt = (
                "You are an expert agricultural advisor with deep knowledge of farming practices, "
                "crop management, pest control, and agricultural economics. Provide practical, "
                "actionable advice to farmers in simple language."
            )
            
            if language == 'bn':
                system_prompt += " Respond in Bengali."
            elif language == 'hi':
                system_prompt += " Respond in Hindi."
            else:
                system_prompt += " Respond in English."
            
            # Construct full prompt
            full_prompt = prompt
            if context:
                full_prompt = f"Context: {context}\n\nQuestion: {prompt}"
            
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "system": system_prompt,
                "messages": [
                    {
                        "role": "user",
                        "content": full_prompt
                    }
                ]
            }
            
            # Invoke Bedrock
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            content = response_body.get('content', [])
            
            if content and len(content) > 0:
                return content[0].get('text', '')
            
            raise ValueError("No content in Bedrock response")
        
        return self._retry_with_backoff(_invoke)
    
    def text_to_speech(self, text: str, language: str = 'en') -> bytes:
        """
        Convert text to speech audio (Note: Bedrock doesn't directly support TTS,
        this is a placeholder for integration with Amazon Polly or similar service)
        
        Args:
            text: Text to convert
            language: Audio language
            
        Returns:
            Audio data as bytes
        """
        # TODO: Integrate with Amazon Polly
        # For now, return empty bytes
        logger.warning("Text-to-speech not yet implemented - using placeholder")
        return b""


# Global client instance
_client: BedrockClient = None


def get_bedrock_client() -> BedrockClient:
    """Get the global Bedrock client instance"""
    global _client
    
    if _client is None:
        _client = BedrockClient()
    
    return _client


if __name__ == '__main__':
    # Test Bedrock client
    client = get_bedrock_client()
    print("Bedrock Client initialized successfully")
    print(f"Model ID: {client.model_id}")
    print(f"Temperature: {client.temperature}")
    print(f"Max Tokens: {client.max_tokens}")
