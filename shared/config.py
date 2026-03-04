"""
Application Configuration Module for Agri-Nexus V1 Platform
Loads and validates configuration from environment variables
"""

import os
from dataclasses import dataclass, field
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class AppConfig:
    """
    Application configuration with environment variable loading and validation
    """
    # AWS Configuration
    aws_region: str
    table_name: str
    image_bucket: str
    api_gateway_url: str
    
    # Bedrock Configuration
    bedrock_model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    bedrock_temperature: float = 0.3
    bedrock_max_tokens: int = 2048
    
    # Application Limits
    max_image_size_mb: int = 10
    max_audio_duration_sec: int = 60
    session_timeout_minutes: int = 30
    diagnosis_timeout_sec: int = 30
    voice_processing_timeout_sec: int = 15
    sms_delivery_timeout_sec: int = 60
    max_sms_retries: int = 3
    
    # Supported Languages
    supported_languages: List[str] = field(default_factory=lambda: ["en", "bn", "hi"])
    default_language: str = "en"
    
    # Environment
    environment: str = "development"
    
    @classmethod
    def from_env(cls, validate_production: bool = False) -> 'AppConfig':
        """
        Load configuration from environment variables
        
        Args:
            validate_production: If True, raise errors for missing required config in production
            
        Returns:
            AppConfig instance
            
        Raises:
            ValueError: If required configuration is missing in production mode
        """
        environment = os.getenv('ENVIRONMENT', 'development')
        
        # Required configuration
        aws_region = os.getenv('AWS_REGION')
        table_name = os.getenv('TABLE_NAME')
        image_bucket = os.getenv('IMAGE_BUCKET')
        api_gateway_url = os.getenv('API_GATEWAY_URL')
        
        # Validate required configuration
        if validate_production and environment == 'production':
            missing_vars = []
            if not aws_region:
                missing_vars.append('AWS_REGION')
            if not table_name:
                missing_vars.append('TABLE_NAME')
            if not image_bucket:
                missing_vars.append('IMAGE_BUCKET')
            if not api_gateway_url:
                missing_vars.append('API_GATEWAY_URL')
            
            if missing_vars:
                raise ValueError(
                    f"Missing required configuration in production mode: {', '.join(missing_vars)}"
                )
        
        # Provide defaults for development
        aws_region = aws_region or 'us-east-1'
        table_name = table_name or 'agri-nexus-data'
        image_bucket = image_bucket or 'agri-nexus-images'
        api_gateway_url = api_gateway_url or 'http://localhost:8000'
        
        # Optional configuration with defaults
        bedrock_model_id = os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-5-sonnet-20241022-v2:0')
        bedrock_temperature = float(os.getenv('BEDROCK_TEMPERATURE', '0.3'))
        bedrock_max_tokens = int(os.getenv('BEDROCK_MAX_TOKENS', '2048'))
        
        max_image_size_mb = int(os.getenv('MAX_IMAGE_SIZE_MB', '10'))
        max_audio_duration_sec = int(os.getenv('MAX_AUDIO_DURATION_SEC', '60'))
        session_timeout_minutes = int(os.getenv('SESSION_TIMEOUT_MINUTES', '30'))
        
        # Parse supported languages
        supported_languages_str = os.getenv('SUPPORTED_LANGUAGES', 'en,bn,hi')
        supported_languages = [lang.strip() for lang in supported_languages_str.split(',')]
        default_language = os.getenv('DEFAULT_LANGUAGE', 'en')
        
        return cls(
            aws_region=aws_region,
            table_name=table_name,
            image_bucket=image_bucket,
            api_gateway_url=api_gateway_url,
            bedrock_model_id=bedrock_model_id,
            bedrock_temperature=bedrock_temperature,
            bedrock_max_tokens=bedrock_max_tokens,
            max_image_size_mb=max_image_size_mb,
            max_audio_duration_sec=max_audio_duration_sec,
            session_timeout_minutes=session_timeout_minutes,
            supported_languages=supported_languages,
            default_language=default_language,
            environment=environment
        )
    
    def validate(self) -> None:
        """
        Validate configuration values
        
        Raises:
            ValueError: If configuration values are invalid
        """
        if self.bedrock_temperature < 0 or self.bedrock_temperature > 1:
            raise ValueError(f"Invalid bedrock_temperature: {self.bedrock_temperature}. Must be between 0 and 1")
        
        if self.bedrock_max_tokens < 1:
            raise ValueError(f"Invalid bedrock_max_tokens: {self.bedrock_max_tokens}. Must be positive")
        
        if self.max_image_size_mb < 1:
            raise ValueError(f"Invalid max_image_size_mb: {self.max_image_size_mb}. Must be positive")
        
        if self.max_audio_duration_sec < 1:
            raise ValueError(f"Invalid max_audio_duration_sec: {self.max_audio_duration_sec}. Must be positive")
        
        if self.default_language not in self.supported_languages:
            raise ValueError(
                f"Invalid default_language: {self.default_language}. "
                f"Must be one of {self.supported_languages}"
            )
    
    def __str__(self) -> str:
        """String representation of configuration (hides sensitive data)"""
        return (
            f"AppConfig(\n"
            f"  environment={self.environment}\n"
            f"  aws_region={self.aws_region}\n"
            f"  table_name={self.table_name}\n"
            f"  image_bucket={self.image_bucket}\n"
            f"  api_gateway_url={self.api_gateway_url[:30]}...\n"
            f"  bedrock_model_id={self.bedrock_model_id}\n"
            f"  supported_languages={self.supported_languages}\n"
            f")"
        )


# Global configuration instance
_config: AppConfig = None


def get_config(reload: bool = False, validate_production: bool = False) -> AppConfig:
    """
    Get the global configuration instance
    
    Args:
        reload: If True, reload configuration from environment
        validate_production: If True, validate required config in production
        
    Returns:
        AppConfig instance
    """
    global _config
    
    if _config is None or reload:
        _config = AppConfig.from_env(validate_production=validate_production)
        _config.validate()
    
    return _config


if __name__ == '__main__':
    # Test configuration loading
    config = get_config()
    print("Configuration loaded successfully:")
    print(config)
