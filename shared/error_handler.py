"""
Error Handling Module for Agri-Nexus V1 Platform
Provides centralized error handling with multilingual support and CloudWatch logging
"""

import logging
import traceback
from typing import Dict, Optional, Any
from enum import Enum
from datetime import datetime, timezone
import json


# Error codes as defined in the design document
class ErrorCode(Enum):
    """Error codes for the application"""
    INVALID_IMAGE_FORMAT = "INVALID_IMAGE_FORMAT"
    IMAGE_TOO_LARGE = "IMAGE_TOO_LARGE"
    IMAGE_QUALITY_LOW = "IMAGE_QUALITY_LOW"
    INVALID_AUDIO_FORMAT = "INVALID_AUDIO_FORMAT"
    AUDIO_TOO_LONG = "AUDIO_TOO_LONG"
    DIAGNOSIS_FAILED = "DIAGNOSIS_FAILED"
    TRANSCRIPTION_FAILED = "TRANSCRIPTION_FAILED"
    TTS_FAILED = "TTS_FAILED"
    STORAGE_FAILED = "STORAGE_FAILED"
    SMS_DELIVERY_FAILED = "SMS_DELIVERY_FAILED"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    SESSION_EXPIRED = "SESSION_EXPIRED"
    NETWORK_TIMEOUT = "NETWORK_TIMEOUT"
    INVALID_CONFIGURATION = "INVALID_CONFIGURATION"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


# Error message localization dictionary
ERROR_MESSAGES = {
    'en': {
        ErrorCode.INVALID_IMAGE_FORMAT: "Invalid image format. Please upload a JPEG or PNG file.",
        ErrorCode.IMAGE_TOO_LARGE: "Image file is too large. Please upload an image smaller than 10 MB.",
        ErrorCode.IMAGE_QUALITY_LOW: "Image quality is too low. Please upload a clearer photo with good lighting.",
        ErrorCode.INVALID_AUDIO_FORMAT: "Invalid audio format. Please record audio in a supported format.",
        ErrorCode.AUDIO_TOO_LONG: "Audio recording is too long. Please keep recordings under 60 seconds.",
        ErrorCode.DIAGNOSIS_FAILED: "Unable to analyze the image. Please try again or upload a different photo.",
        ErrorCode.TRANSCRIPTION_FAILED: "Unable to transcribe audio. Please try recording again with clear speech.",
        ErrorCode.TTS_FAILED: "Unable to generate audio response. Please try again.",
        ErrorCode.STORAGE_FAILED: "Unable to save data. Please check your connection and try again.",
        ErrorCode.SMS_DELIVERY_FAILED: "Unable to send SMS notification. Please verify your phone number.",
        ErrorCode.RATE_LIMIT_EXCEEDED: "Too many requests. Please wait a moment and try again.",
        ErrorCode.AUTHENTICATION_REQUIRED: "Please log in to access this feature.",
        ErrorCode.SESSION_EXPIRED: "Your session has expired. Please log in again.",
        ErrorCode.NETWORK_TIMEOUT: "Request timed out. Please check your internet connection and try again.",
        ErrorCode.INVALID_CONFIGURATION: "Application configuration error. Please contact support.",
        ErrorCode.UNKNOWN_ERROR: "An unexpected error occurred. Please try again.",
    },
    'hi': {
        ErrorCode.INVALID_IMAGE_FORMAT: "अमान्य छवि प्रारूप। कृपया JPEG या PNG फ़ाइल अपलोड करें।",
        ErrorCode.IMAGE_TOO_LARGE: "छवि फ़ाइल बहुत बड़ी है। कृपया 10 MB से छोटी छवि अपलोड करें।",
        ErrorCode.IMAGE_QUALITY_LOW: "छवि की गुणवत्ता बहुत कम है। कृपया अच्छी रोशनी के साथ एक स्पष्ट फोटो अपलोड करें।",
        ErrorCode.INVALID_AUDIO_FORMAT: "अमान्य ऑडियो प्रारूप। कृपया समर्थित प्रारूप में ऑडियो रिकॉर्ड करें।",
        ErrorCode.AUDIO_TOO_LONG: "ऑडियो रिकॉर्डिंग बहुत लंबी है। कृपया 60 सेकंड से कम रिकॉर्डिंग रखें।",
        ErrorCode.DIAGNOSIS_FAILED: "छवि का विश्लेषण करने में असमर्थ। कृपया पुनः प्रयास करें या एक अलग फोटो अपलोड करें।",
        ErrorCode.TRANSCRIPTION_FAILED: "ऑडियो को ट्रांसक्राइब करने में असमर्थ। कृपया स्पष्ट भाषण के साथ फिर से रिकॉर्ड करें।",
        ErrorCode.TTS_FAILED: "ऑडियो प्रतिक्रिया उत्पन्न करने में असमर्थ। कृपया पुनः प्रयास करें।",
        ErrorCode.STORAGE_FAILED: "डेटा सहेजने में असमर्थ। कृपया अपना कनेक्शन जांचें और पुनः प्रयास करें।",
        ErrorCode.SMS_DELIVERY_FAILED: "SMS सूचना भेजने में असमर्थ। कृपया अपना फोन नंबर सत्यापित करें।",
        ErrorCode.RATE_LIMIT_EXCEEDED: "बहुत सारे अनुरोध। कृपया एक क्षण प्रतीक्षा करें और पुनः प्रयास करें।",
        ErrorCode.AUTHENTICATION_REQUIRED: "कृपया इस सुविधा तक पहुंचने के लिए लॉग इन करें।",
        ErrorCode.SESSION_EXPIRED: "आपका सत्र समाप्त हो गया है। कृपया फिर से लॉग इन करें।",
        ErrorCode.NETWORK_TIMEOUT: "अनुरोध समय समाप्त हो गया। कृपया अपना इंटरनेट कनेक्शन जांचें और पुनः प्रयास करें।",
        ErrorCode.INVALID_CONFIGURATION: "एप्लिकेशन कॉन्फ़िगरेशन त्रुटि। कृपया सहायता से संपर्क करें।",
        ErrorCode.UNKNOWN_ERROR: "एक अप्रत्याशित त्रुटि हुई। कृपया पुनः प्रयास करें।",
    },
    'bn': {
        ErrorCode.INVALID_IMAGE_FORMAT: "অবৈধ ছবি ফরম্যাট। অনুগ্রহ করে একটি JPEG বা PNG ফাইল আপলোড করুন।",
        ErrorCode.IMAGE_TOO_LARGE: "ছবি ফাইল খুব বড়। অনুগ্রহ করে 10 MB এর চেয়ে ছোট একটি ছবি আপলোড করুন।",
        ErrorCode.IMAGE_QUALITY_LOW: "ছবির গুণমান খুব কম। ভাল আলো সহ একটি পরিষ্কার ফটো আপলোড করুন।",
        ErrorCode.INVALID_AUDIO_FORMAT: "অবৈধ অডিও ফরম্যাট। অনুগ্রহ করে সমর্থিত ফরম্যাটে অডিও রেকর্ড করুন।",
        ErrorCode.AUDIO_TOO_LONG: "অডিও রেকর্ডিং খুব দীর্ঘ। অনুগ্রহ করে 60 সেকেন্ডের নিচে রেকর্ডিং রাখুন।",
        ErrorCode.DIAGNOSIS_FAILED: "ছবি বিশ্লেষণ করতে অক্ষম। অনুগ্রহ করে আবার চেষ্টা করুন বা একটি ভিন্ন ফটো আপলোড করুন।",
        ErrorCode.TRANSCRIPTION_FAILED: "অডিও ট্রান্সক্রাইব করতে অক্ষম। অনুগ্রহ করে স্পষ্ট বক্তৃতা সহ আবার রেকর্ড করুন।",
        ErrorCode.TTS_FAILED: "অডিও প্রতিক্রিয়া তৈরি করতে অক্ষম। অনুগ্রহ করে আবার চেষ্টা করুন।",
        ErrorCode.STORAGE_FAILED: "ডেটা সংরক্ষণ করতে অক্ষম। অনুগ্রহ করে আপনার সংযোগ পরীক্ষা করুন এবং আবার চেষ্টা করুন।",
        ErrorCode.SMS_DELIVERY_FAILED: "SMS বিজ্ঞপ্তি পাঠাতে অক্ষম। অনুগ্রহ করে আপনার ফোন নম্বর যাচাই করুন।",
        ErrorCode.RATE_LIMIT_EXCEEDED: "অনেক বেশি অনুরোধ। অনুগ্রহ করে একটু অপেক্ষা করুন এবং আবার চেষ্টা করুন।",
        ErrorCode.AUTHENTICATION_REQUIRED: "এই বৈশিষ্ট্য অ্যাক্সেস করতে অনুগ্রহ করে লগ ইন করুন।",
        ErrorCode.SESSION_EXPIRED: "আপনার সেশন মেয়াদ শেষ হয়ে গেছে। অনুগ্রহ করে আবার লগ ইন করুন।",
        ErrorCode.NETWORK_TIMEOUT: "অনুরোধ সময় শেষ হয়ে গেছে। অনুগ্রহ করে আপনার ইন্টারনেট সংযোগ পরীক্ষা করুন এবং আবার চেষ্টা করুন।",
        ErrorCode.INVALID_CONFIGURATION: "অ্যাপ্লিকেশন কনফিগারেশন ত্রুটি। অনুগ্রহ করে সহায়তার সাথে যোগাযোগ করুন।",
        ErrorCode.UNKNOWN_ERROR: "একটি অপ্রত্যাশিত ত্রুটি ঘটেছে। অনুগ্রহ করে আবার চেষ্টা করুন।",
    }
}


class ErrorHandler:
    """
    Centralized error handler with multilingual support and CloudWatch logging
    """
    
    def __init__(self, logger_name: str = 'agri-nexus'):
        """
        Initialize error handler
        
        Args:
            logger_name: Name for the CloudWatch logger
        """
        self.logger = logging.getLogger(logger_name)
        self._setup_logging()
    
    def _setup_logging(self):
        """Configure CloudWatch logging"""
        # Set logging level
        self.logger.setLevel(logging.INFO)
        
        # Create console handler for development
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            # Create formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(formatter)
            
            self.logger.addHandler(console_handler)
    
    def get_user_message(
        self,
        error_code: ErrorCode,
        language: str = 'en'
    ) -> str:
        """
        Get user-friendly error message in specified language
        
        Args:
            error_code: Error code enum
            language: Language code (en, bn, hi)
            
        Returns:
            Localized error message
        """
        # Default to English if language not supported
        if language not in ERROR_MESSAGES:
            language = 'en'
        
        # Get message for error code
        messages = ERROR_MESSAGES[language]
        return messages.get(error_code, messages[ErrorCode.UNKNOWN_ERROR])
    
    def log_error(
        self,
        error_code: ErrorCode,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None
    ):
        """
        Log detailed error information to CloudWatch
        
        Args:
            error_code: Error code enum
            error: The exception that occurred
            context: Additional context information
            user_id: User identifier
            request_id: Request identifier
        """
        # Build structured log entry
        log_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'error_code': error_code.value,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'stack_trace': traceback.format_exc(),
        }
        
        if user_id:
            log_entry['user_id'] = user_id
        
        if request_id:
            log_entry['request_id'] = request_id
        
        if context:
            log_entry['context'] = context
        
        # Log as JSON for structured logging
        self.logger.error(json.dumps(log_entry))
    
    def handle_error(
        self,
        error: Exception,
        error_code: Optional[ErrorCode] = None,
        language: str = 'en',
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle an error by logging details and returning user-friendly message
        
        Args:
            error: The exception that occurred
            error_code: Error code enum (auto-detected if not provided)
            language: Language for user message
            context: Additional context information
            user_id: User identifier
            request_id: Request identifier
            
        Returns:
            Dictionary with user message and error details
        """
        # Auto-detect error code if not provided
        if error_code is None:
            error_code = self._detect_error_code(error)
        
        # Log detailed error information
        self.log_error(
            error_code=error_code,
            error=error,
            context=context,
            user_id=user_id,
            request_id=request_id
        )
        
        # Get user-friendly message
        user_message = self.get_user_message(error_code, language)
        
        return {
            'error_code': error_code.value,
            'message': user_message,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def _detect_error_code(self, error: Exception) -> ErrorCode:
        """
        Auto-detect error code from exception
        
        Args:
            error: The exception
            
        Returns:
            Detected error code
        """
        error_str = str(error).lower()
        error_type = type(error).__name__
        
        # Check for timeout errors
        if 'timeout' in error_str or error_type == 'TimeoutError':
            return ErrorCode.NETWORK_TIMEOUT
        
        # Check for rate limit errors
        if 'rate limit' in error_str or 'throttl' in error_str:
            return ErrorCode.RATE_LIMIT_EXCEEDED
        
        # Check for authentication errors
        if 'auth' in error_str or 'unauthorized' in error_str:
            return ErrorCode.AUTHENTICATION_REQUIRED
        
        # Check for storage errors
        if 'dynamodb' in error_str or 'storage' in error_str or 's3' in error_str:
            return ErrorCode.STORAGE_FAILED
        
        # Default to unknown error
        return ErrorCode.UNKNOWN_ERROR


# Global error handler instance
_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """
    Get the global error handler instance
    
    Returns:
        ErrorHandler instance
    """
    global _error_handler
    
    if _error_handler is None:
        _error_handler = ErrorHandler()
    
    return _error_handler


def handle_error(
    error: Exception,
    error_code: Optional[ErrorCode] = None,
    language: str = 'en',
    context: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to handle errors using the global error handler
    
    Args:
        error: The exception that occurred
        error_code: Error code enum (auto-detected if not provided)
        language: Language for user message
        context: Additional context information
        user_id: User identifier
        request_id: Request identifier
        
    Returns:
        Dictionary with user message and error details
    """
    handler = get_error_handler()
    return handler.handle_error(
        error=error,
        error_code=error_code,
        language=language,
        context=context,
        user_id=user_id,
        request_id=request_id
    )


if __name__ == '__main__':
    # Test error handler
    handler = ErrorHandler()
    
    # Test English message
    print("English:", handler.get_user_message(ErrorCode.IMAGE_QUALITY_LOW, 'en'))
    
    # Test Hindi message
    print("Hindi:", handler.get_user_message(ErrorCode.IMAGE_QUALITY_LOW, 'hi'))
    
    # Test Bengali message
    print("Bengali:", handler.get_user_message(ErrorCode.IMAGE_QUALITY_LOW, 'bn'))
    
    # Test error handling
    try:
        raise ValueError("Test error")
    except Exception as e:
        result = handler.handle_error(
            error=e,
            error_code=ErrorCode.DIAGNOSIS_FAILED,
            language='en',
            context={'test': 'value'},
            user_id='test_user'
        )
        print("\nError handling result:", result)
