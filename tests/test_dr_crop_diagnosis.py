"""
Unit tests for Dr. Crop diagnosis functionality
Tests the integration between Streamlit UI and API client
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from frontend.api_client import AgriNexusAPIClient
from shared.error_handler import ErrorCode


class TestDiagnosisIntegration:
    """Test diagnosis request and display functionality"""
    
    def test_diagnose_crop_success(self):
        """Test successful crop diagnosis"""
        # Create API client
        client = AgriNexusAPIClient('https://test-api.example.com', 'en')
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'diagnosis_id': 'DIAG123',
            'disease_name': 'Late Blight',
            'confidence': 87.5,
            'treatment': 'Apply copper-based fungicide within 24 hours',
            'timestamp': '2024-01-15T10:30:00Z'
        }
        
        with patch('requests.post', return_value=mock_response):
            # Call diagnosis
            result = client.diagnose_crop(
                user_id='test_user',
                image_bytes=b'fake_image_data',
                language='en'
            )
            
            # Verify result structure
            assert 'diagnosis_id' in result
            assert 'disease_name' in result
            assert 'confidence' in result
            assert 'treatment' in result
            assert 'timestamp' in result
            
            # Verify values
            assert result['disease_name'] == 'Late Blight'
            assert result['confidence'] == 87.5
            assert 0 <= result['confidence'] <= 100
            assert len(result['treatment']) > 0
    
    def test_diagnose_crop_timeout(self):
        """Test diagnosis timeout handling"""
        client = AgriNexusAPIClient('https://test-api.example.com', 'en')
        
        # Mock timeout
        with patch('requests.post', side_effect=Exception('Timeout')):
            with pytest.raises(Exception) as exc_info:
                client.diagnose_crop(
                    user_id='test_user',
                    image_bytes=b'fake_image_data',
                    language='en'
                )
            
            # Verify error message is user-friendly
            error_msg = str(exc_info.value)
            assert len(error_msg) > 0
            # Should not contain technical details
            assert 'Traceback' not in error_msg
    
    def test_diagnose_crop_network_error(self):
        """Test network error handling"""
        client = AgriNexusAPIClient('https://test-api.example.com', 'en')
        
        # Mock network error
        with patch('requests.post', side_effect=Exception('Connection refused')):
            with pytest.raises(Exception) as exc_info:
                client.diagnose_crop(
                    user_id='test_user',
                    image_bytes=b'fake_image_data',
                    language='en'
                )
            
            # Verify error is raised
            assert exc_info.value is not None
    
    def test_diagnose_crop_multilingual(self):
        """Test diagnosis in different languages"""
        client = AgriNexusAPIClient('https://test-api.example.com', 'hi')
        
        # Mock successful response in Hindi
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'diagnosis_id': 'DIAG123',
            'disease_name': 'लेट ब्लाइट',
            'confidence': 87.5,
            'treatment': '24 घंटे के भीतर तांबा आधारित कवकनाशी लगाएं',
            'timestamp': '2024-01-15T10:30:00Z'
        }
        
        with patch('requests.post', return_value=mock_response):
            result = client.diagnose_crop(
                user_id='test_user',
                image_bytes=b'fake_image_data',
                language='hi'
            )
            
            # Verify Hindi response
            assert result['disease_name'] == 'लेट ब्लाइट'
            assert 'तांबा' in result['treatment']
    
    def test_diagnosis_result_validation(self):
        """Test that diagnosis results contain required fields"""
        client = AgriNexusAPIClient('https://test-api.example.com', 'en')
        
        # Mock response with all required fields
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'diagnosis_id': 'DIAG123',
            'disease_name': 'Healthy',
            'confidence': 95.0,
            'treatment': 'No treatment needed. Continue regular care.',
            'timestamp': '2024-01-15T10:30:00Z'
        }
        
        with patch('requests.post', return_value=mock_response):
            result = client.diagnose_crop(
                user_id='test_user',
                image_bytes=b'fake_image_data',
                language='en'
            )
            
            # Verify all required fields are present
            required_fields = ['diagnosis_id', 'disease_name', 'confidence', 'treatment', 'timestamp']
            for field in required_fields:
                assert field in result, f"Missing required field: {field}"
            
            # Verify confidence is in valid range
            assert 0 <= result['confidence'] <= 100
    
    def test_loading_indicator_timeout(self):
        """Test that loading indicator is shown for expected 30 seconds"""
        # This is a conceptual test - in practice, we verify the timeout is set correctly
        client = AgriNexusAPIClient('https://test-api.example.com', 'en')
        
        # Verify timeout is set to 30 seconds (as per requirements)
        assert client.timeout == 30
    
    def test_api_client_initialization(self):
        """Test API client initialization with different configurations"""
        # Test with trailing slash
        client1 = AgriNexusAPIClient('https://test-api.example.com/', 'en')
        assert client1.base_url == 'https://test-api.example.com'
        
        # Test without trailing slash
        client2 = AgriNexusAPIClient('https://test-api.example.com', 'en')
        assert client2.base_url == 'https://test-api.example.com'
        
        # Test with different languages
        client3 = AgriNexusAPIClient('https://test-api.example.com', 'hi')
        assert client3.language == 'hi'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
