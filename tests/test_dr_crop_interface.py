"""
Unit tests for Dr. Crop image upload interface
Tests the render_dr_crop_tab function implementation
"""

import pytest
import sys
import os
from io import BytesIO
from PIL import Image

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.image_validator import get_image_validator, ValidationResult
from shared.error_handler import ErrorCode


def create_test_image(width: int, height: int, format: str = 'JPEG') -> bytes:
    """Create a test image with specified dimensions and realistic content"""
    import numpy as np
    
    # Create an image with good variation and contrast (not solid color)
    # This simulates a more realistic crop image with texture
    # Use wider range for better contrast
    img_array = np.random.randint(30, 220, (height, width, 3), dtype=np.uint8)
    img = Image.fromarray(img_array, 'RGB')
    
    buffer = BytesIO()
    # Use higher quality for PNG to preserve contrast
    if format == 'PNG':
        img.save(buffer, format=format, compress_level=1)
    else:
        img.save(buffer, format=format, quality=95)
    return buffer.getvalue()


def test_valid_jpeg_image():
    """Test that valid JPEG images are accepted"""
    validator = get_image_validator()
    image_bytes = create_test_image(300, 300, 'JPEG')
    
    result = validator.validate_image(image_bytes, 'test.jpg', 'en')
    
    assert result.is_valid is True
    assert result.error_message is None


def test_valid_png_image():
    """Test that valid PNG images are accepted"""
    validator = get_image_validator()
    image_bytes = create_test_image(300, 300, 'PNG')
    
    result = validator.validate_image(image_bytes, 'test.png', 'en')
    
    assert result.is_valid is True
    assert result.error_message is None


def test_image_too_small():
    """Test that images below minimum resolution are rejected"""
    validator = get_image_validator()
    image_bytes = create_test_image(100, 100, 'JPEG')
    
    result = validator.validate_image(image_bytes, 'test.jpg', 'en')
    
    assert result.is_valid is False
    assert result.error_code == ErrorCode.IMAGE_QUALITY_LOW


def test_image_too_large():
    """Test that images exceeding size limit are rejected"""
    validator = get_image_validator()
    # Create a large image (simulate > 10MB)
    large_bytes = b'x' * (11 * 1024 * 1024)  # 11 MB
    
    result = validator.validate_image(large_bytes, 'test.jpg', 'en')
    
    assert result.is_valid is False
    assert result.error_code == ErrorCode.IMAGE_TOO_LARGE


def test_invalid_image_format():
    """Test that invalid image data is rejected"""
    validator = get_image_validator()
    invalid_bytes = b'This is not an image'
    
    result = validator.validate_image(invalid_bytes, 'test.txt', 'en')
    
    assert result.is_valid is False
    assert result.error_code == ErrorCode.INVALID_IMAGE_FORMAT


def test_error_messages_in_english():
    """Test that error messages are returned in English"""
    validator = get_image_validator()
    image_bytes = create_test_image(100, 100, 'JPEG')
    
    result = validator.validate_image(image_bytes, 'test.jpg', 'en')
    
    assert result.is_valid is False
    assert 'quality' in result.error_message.lower() or 'low' in result.error_message.lower()


def test_error_messages_in_hindi():
    """Test that error messages are returned in Hindi"""
    validator = get_image_validator()
    image_bytes = create_test_image(100, 100, 'JPEG')
    
    result = validator.validate_image(image_bytes, 'test.jpg', 'hi')
    
    assert result.is_valid is False
    assert result.error_message is not None
    # Hindi error message should contain Hindi characters
    assert any(ord(c) > 127 for c in result.error_message)


def test_error_messages_in_bengali():
    """Test that error messages are returned in Bengali"""
    validator = get_image_validator()
    image_bytes = create_test_image(100, 100, 'JPEG')
    
    result = validator.validate_image(image_bytes, 'test.jpg', 'bn')
    
    assert result.is_valid is False
    assert result.error_message is not None
    # Bengali error message should contain Bengali characters
    assert any(ord(c) > 127 for c in result.error_message)


def test_image_at_minimum_resolution():
    """Test that images at exactly minimum resolution are accepted"""
    validator = get_image_validator()
    image_bytes = create_test_image(224, 224, 'JPEG')
    
    result = validator.validate_image(image_bytes, 'test.jpg', 'en')
    
    assert result.is_valid is True


def test_supported_formats():
    """Test that all supported formats are accepted"""
    validator = get_image_validator()
    
    formats = [
        ('JPEG', 'test.jpg'),
        ('JPEG', 'test.jpeg'),
        ('PNG', 'test.png'),
    ]
    
    for format_type, filename in formats:
        image_bytes = create_test_image(300, 300, format_type)
        result = validator.validate_image(image_bytes, filename, 'en')
        assert result.is_valid is True, f"Format {format_type} should be accepted"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
