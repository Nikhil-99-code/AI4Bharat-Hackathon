"""
Unit tests for error handler module
"""

import pytest
from shared.error_handler import ErrorCode, ErrorHandler, get_error_handler


def test_error_handler_initialization():
    """Test that error handler initializes correctly"""
    handler = ErrorHandler()
    assert handler is not None
    assert handler.logger is not None


def test_get_user_message_english():
    """Test getting error message in English"""
    handler = ErrorHandler()
    message = handler.get_user_message(ErrorCode.IMAGE_QUALITY_LOW, 'en')
    
    assert message is not None
    assert len(message) > 0
    assert 'quality' in message.lower() or 'clear' in message.lower()
    # Should not contain technical details
    assert 'Exception' not in message
    assert 'Traceback' not in message


def test_get_user_message_hindi():
    """Test getting error message in Hindi"""
    handler = ErrorHandler()
    message = handler.get_user_message(ErrorCode.IMAGE_QUALITY_LOW, 'hi')
    
    assert message is not None
    assert len(message) > 0
    # Should not contain technical details
    assert 'Exception' not in message
    assert 'Traceback' not in message


def test_get_user_message_bengali():
    """Test getting error message in Bengali"""
    handler = ErrorHandler()
    message = handler.get_user_message(ErrorCode.IMAGE_QUALITY_LOW, 'bn')
    
    assert message is not None
    assert len(message) > 0
    # Should not contain technical details
    assert 'Exception' not in message
    assert 'Traceback' not in message


def test_get_user_message_unsupported_language():
    """Test that unsupported language falls back to English"""
    handler = ErrorHandler()
    message = handler.get_user_message(ErrorCode.IMAGE_QUALITY_LOW, 'fr')
    
    # Should fall back to English
    english_message = handler.get_user_message(ErrorCode.IMAGE_QUALITY_LOW, 'en')
    assert message == english_message


def test_handle_error_returns_user_friendly_message():
    """Test that handle_error returns user-friendly message without stack traces"""
    handler = ErrorHandler()
    
    try:
        raise ValueError("Test error with technical details")
    except Exception as e:
        result = handler.handle_error(
            error=e,
            error_code=ErrorCode.DIAGNOSIS_FAILED,
            language='en'
        )
    
    assert 'error_code' in result
    assert 'message' in result
    assert 'timestamp' in result
    
    # Message should be user-friendly
    assert 'ValueError' not in result['message']
    assert 'technical details' not in result['message']
    assert len(result['message']) > 0


def test_handle_error_with_context():
    """Test that handle_error logs context information"""
    handler = ErrorHandler()
    
    context = {
        'operation': 'test_operation',
        'image_size': 1024000
    }
    
    try:
        raise RuntimeError("Test error")
    except Exception as e:
        result = handler.handle_error(
            error=e,
            error_code=ErrorCode.STORAGE_FAILED,
            language='en',
            context=context,
            user_id='test_user',
            request_id='test_request_123'
        )
    
    assert result is not None
    assert result['error_code'] == ErrorCode.STORAGE_FAILED.value


def test_error_code_auto_detection_timeout():
    """Test that timeout errors are auto-detected"""
    handler = ErrorHandler()
    
    timeout_error = TimeoutError("Request timed out")
    error_code = handler._detect_error_code(timeout_error)
    
    assert error_code == ErrorCode.NETWORK_TIMEOUT


def test_error_code_auto_detection_rate_limit():
    """Test that rate limit errors are auto-detected"""
    handler = ErrorHandler()
    
    rate_limit_error = Exception("Rate limit exceeded")
    error_code = handler._detect_error_code(rate_limit_error)
    
    assert error_code == ErrorCode.RATE_LIMIT_EXCEEDED


def test_error_code_auto_detection_auth():
    """Test that authentication errors are auto-detected"""
    handler = ErrorHandler()
    
    auth_error = Exception("Unauthorized access")
    error_code = handler._detect_error_code(auth_error)
    
    assert error_code == ErrorCode.AUTHENTICATION_REQUIRED


def test_error_code_auto_detection_storage():
    """Test that storage errors are auto-detected"""
    handler = ErrorHandler()
    
    storage_error = Exception("DynamoDB operation failed")
    error_code = handler._detect_error_code(storage_error)
    
    assert error_code == ErrorCode.STORAGE_FAILED


def test_error_code_auto_detection_unknown():
    """Test that unknown errors default to UNKNOWN_ERROR"""
    handler = ErrorHandler()
    
    unknown_error = Exception("Some random error")
    error_code = handler._detect_error_code(unknown_error)
    
    assert error_code == ErrorCode.UNKNOWN_ERROR


def test_global_error_handler():
    """Test that global error handler instance works"""
    handler1 = get_error_handler()
    handler2 = get_error_handler()
    
    # Should return same instance
    assert handler1 is handler2


def test_all_error_codes_have_messages():
    """Test that all error codes have messages in all languages"""
    handler = ErrorHandler()
    languages = ['en', 'hi', 'bn']
    
    for error_code in ErrorCode:
        for lang in languages:
            message = handler.get_user_message(error_code, lang)
            assert message is not None
            assert len(message) > 0
            # Should not contain technical details
            assert 'Exception' not in message
            assert 'Traceback' not in message


def test_network_timeout_message_has_guidance():
    """Test that network timeout messages provide actionable guidance"""
    handler = ErrorHandler()
    
    message_en = handler.get_user_message(ErrorCode.NETWORK_TIMEOUT, 'en')
    
    # Should mention internet or connection
    assert any(keyword in message_en.lower() for keyword in ['internet', 'connection', 'network'])


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
