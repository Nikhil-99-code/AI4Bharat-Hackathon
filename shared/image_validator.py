"""
Image Validator for Agri-Nexus V1 Platform
Validates crop images for quality, format, and size
"""

from PIL import Image
import io
import numpy as np
from typing import Tuple, Optional
from dataclasses import dataclass
import logging

from .config import get_config
from .error_handler import ErrorCode, get_error_handler

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of image validation"""
    is_valid: bool
    error_message: Optional[str] = None
    error_code: Optional[ErrorCode] = None
    warnings: list = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class ImageValidator:
    """
    Validator for crop images with quality checks
    """
    
    def __init__(self):
        """Initialize validator with configuration"""
        config = get_config()
        self.max_size_mb = config.max_image_size_mb
        self.max_size_bytes = self.max_size_mb * 1024 * 1024
        self.min_resolution = (224, 224)
        self.supported_formats = ['JPEG', 'PNG', 'JPG']
        self.brightness_range = (20, 235)  # On 0-255 scale
        self.min_contrast = 30
        self.error_handler = get_error_handler()
    
    def validate_image(self, image_bytes: bytes, filename: str = "", language: str = 'en') -> ValidationResult:
        """
        Validate image quality and format
        
        Args:
            image_bytes: Image data as bytes
            filename: Original filename (optional)
            language: Language for error messages
            
        Returns:
            ValidationResult with validation status and messages
        """
        warnings = []
        
        # Check file size
        if len(image_bytes) > self.max_size_bytes:
            return ValidationResult(
                is_valid=False,
                error_message=self.error_handler.get_user_message(ErrorCode.IMAGE_TOO_LARGE, language),
                error_code=ErrorCode.IMAGE_TOO_LARGE
            )
        
        # Try to open image
        try:
            image = Image.open(io.BytesIO(image_bytes))
        except Exception as e:
            self.error_handler.log_error(
                error_code=ErrorCode.INVALID_IMAGE_FORMAT,
                error=e,
                context={'filename': filename, 'size': len(image_bytes)}
            )
            return ValidationResult(
                is_valid=False,
                error_message=self.error_handler.get_user_message(ErrorCode.INVALID_IMAGE_FORMAT, language),
                error_code=ErrorCode.INVALID_IMAGE_FORMAT
            )
        
        # Check format
        if image.format and image.format.upper() not in self.supported_formats:
            return ValidationResult(
                is_valid=False,
                error_message=self.error_handler.get_user_message(ErrorCode.INVALID_IMAGE_FORMAT, language),
                error_code=ErrorCode.INVALID_IMAGE_FORMAT
            )
        
        # Check resolution
        if not self.check_resolution(image):
            return ValidationResult(
                is_valid=False,
                error_message=self.error_handler.get_user_message(ErrorCode.IMAGE_QUALITY_LOW, language),
                error_code=ErrorCode.IMAGE_QUALITY_LOW
            )
        
        # Check brightness and contrast
        brightness_ok, brightness_msg = self.check_brightness_contrast(image)
        if not brightness_ok:
            return ValidationResult(
                is_valid=False,
                error_message=self.error_handler.get_user_message(ErrorCode.IMAGE_QUALITY_LOW, language),
                error_code=ErrorCode.IMAGE_QUALITY_LOW,
                warnings=[brightness_msg]
            )
        
        # All checks passed
        return ValidationResult(
            is_valid=True,
            warnings=warnings
        )
    
    def check_resolution(self, image: Image.Image) -> bool:
        """
        Verify minimum resolution requirements
        
        Args:
            image: PIL Image object
            
        Returns:
            True if resolution meets minimum requirements
        """
        width, height = image.size
        return width >= self.min_resolution[0] and height >= self.min_resolution[1]
    
    def check_brightness_contrast(self, image: Image.Image) -> Tuple[bool, str]:
        """
        Assess image quality metrics (brightness and contrast)
        
        Args:
            image: PIL Image object
            
        Returns:
            Tuple of (is_acceptable, message)
        """
        try:
            # Convert to grayscale for analysis
            if image.mode != 'L':
                gray_image = image.convert('L')
            else:
                gray_image = image
            
            # Convert to numpy array
            img_array = np.array(gray_image)
            
            # Calculate brightness (mean pixel value)
            brightness = np.mean(img_array)
            
            # Calculate contrast (standard deviation)
            contrast = np.std(img_array)
            
            # Check brightness range
            if brightness < self.brightness_range[0]:
                return False, f"Image is too dark (brightness: {brightness:.1f}). Please use better lighting."
            elif brightness > self.brightness_range[1]:
                return False, f"Image is too bright (brightness: {brightness:.1f}). Please reduce exposure."
            
            # Check contrast
            if contrast < self.min_contrast:
                return False, f"Image has low contrast ({contrast:.1f}). Please ensure clear focus and good lighting."
            
            return True, "Image quality is acceptable"
            
        except Exception as e:
            logger.warning(f"Could not assess image quality: {str(e)}")
            return True, "Quality check skipped"
    
    def compress_image(
        self,
        image: Image.Image,
        max_size_mb: Optional[int] = None,
        quality: int = 85
    ) -> bytes:
        """
        Compress image while maintaining quality
        
        Args:
            image: PIL Image object
            max_size_mb: Maximum size in MB (uses config default if not specified)
            quality: JPEG quality (1-100, default: 85)
            
        Returns:
            Compressed image as bytes
        """
        if max_size_mb is None:
            max_size_mb = self.max_size_mb
        
        max_size_bytes = max_size_mb * 1024 * 1024
        
        # Convert RGBA to RGB if necessary
        if image.mode == 'RGBA':
            # Create white background
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])  # Use alpha channel as mask
            image = background
        elif image.mode not in ('RGB', 'L'):
            image = image.convert('RGB')
        
        # Try different quality levels to meet size requirement
        for q in range(quality, 20, -5):
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=q, optimize=True)
            compressed_bytes = output.getvalue()
            
            if len(compressed_bytes) <= max_size_bytes:
                logger.info(f"Image compressed to {len(compressed_bytes) / 1024:.2f} KB at quality {q}")
                return compressed_bytes
        
        # If still too large, resize image
        logger.warning("Image still too large after compression, resizing...")
        scale_factor = 0.8
        new_size = (int(image.size[0] * scale_factor), int(image.size[1] * scale_factor))
        image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=quality, optimize=True)
        return output.getvalue()
    
    def compress_image_bytes(
        self,
        image_bytes: bytes,
        max_size_mb: Optional[int] = None,
        quality: int = 85
    ) -> bytes:
        """
        Compress image from bytes
        
        Args:
            image_bytes: Image data as bytes
            max_size_mb: Maximum size in MB
            quality: JPEG quality (1-100)
            
        Returns:
            Compressed image as bytes
        """
        image = Image.open(io.BytesIO(image_bytes))
        return self.compress_image(image, max_size_mb, quality)


# Global validator instance
_validator: ImageValidator = None


def get_image_validator() -> ImageValidator:
    """Get the global image validator instance"""
    global _validator
    
    if _validator is None:
        _validator = ImageValidator()
    
    return _validator


if __name__ == '__main__':
    # Test image validator
    validator = get_image_validator()
    print("Image Validator initialized successfully")
    print(f"Max size: {validator.max_size_mb} MB")
    print(f"Min resolution: {validator.min_resolution}")
    print(f"Supported formats: {validator.supported_formats}")
