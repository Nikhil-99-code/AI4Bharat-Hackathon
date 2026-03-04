"""
Unit tests for diagnosis history functionality
"""

import pytest
import json
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.dynamodb_repository import get_repository
from backend.get_diagnosis_history.handler import lambda_handler


class TestDiagnosisHistory:
    """Test diagnosis history retrieval"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.repository = get_repository()
        self.test_user_id = 'test_user_history'
        
        # Clean up any existing test data
        self._cleanup_test_data()
    
    def teardown_method(self):
        """Cleanup after tests"""
        self._cleanup_test_data()
    
    def _cleanup_test_data(self):
        """Remove test data from DynamoDB"""
        try:
            # Get all diagnoses for test user
            diagnoses = self.repository.get_diagnosis_history(self.test_user_id, limit=100)
            
            # Delete each diagnosis
            for diagnosis in diagnoses:
                pk = diagnosis.get('PK')
                sk = diagnosis.get('SK')
                if pk and sk:
                    self.repository.table.delete_item(Key={'PK': pk, 'SK': sk})
        except Exception:
            pass  # Ignore cleanup errors
    
    def test_get_empty_history(self):
        """Test retrieving history when no diagnoses exist"""
        # Get history for user with no diagnoses
        history = self.repository.get_diagnosis_history(self.test_user_id, limit=20)
        
        assert isinstance(history, list)
        assert len(history) == 0
    
    def test_store_and_retrieve_single_diagnosis(self):
        """Test storing and retrieving a single diagnosis"""
        # Store a diagnosis
        diagnosis = {
            'disease_name': 'Late Blight',
            'confidence': 87.5,
            'treatment': 'Apply copper-based fungicide',
            'image_s3_key': 'images/test/image1.jpg',
            'language': 'en'
        }
        
        diagnosis_id = self.repository.store_diagnosis(self.test_user_id, diagnosis)
        assert diagnosis_id is not None
        
        # Retrieve history
        history = self.repository.get_diagnosis_history(self.test_user_id, limit=20)
        
        assert len(history) == 1
        assert history[0]['disease_name'] == 'Late Blight'
        assert history[0]['confidence'] == 87.5
        assert history[0]['treatment'] == 'Apply copper-based fungicide'
    
    def test_retrieve_multiple_diagnoses_in_reverse_chronological_order(self):
        """Test that multiple diagnoses are returned in reverse chronological order"""
        # Store multiple diagnoses with different timestamps
        diagnoses = [
            {
                'disease_name': 'Early Blight',
                'confidence': 75.0,
                'treatment': 'Treatment 1',
                'image_s3_key': 'images/test/image1.jpg',
                'language': 'en'
            },
            {
                'disease_name': 'Late Blight',
                'confidence': 85.0,
                'treatment': 'Treatment 2',
                'image_s3_key': 'images/test/image2.jpg',
                'language': 'en'
            },
            {
                'disease_name': 'Powdery Mildew',
                'confidence': 90.0,
                'treatment': 'Treatment 3',
                'image_s3_key': 'images/test/image3.jpg',
                'language': 'en'
            }
        ]
        
        # Store diagnoses (they will have increasing timestamps)
        for diagnosis in diagnoses:
            self.repository.store_diagnosis(self.test_user_id, diagnosis)
        
        # Retrieve history
        history = self.repository.get_diagnosis_history(self.test_user_id, limit=20)
        
        # Verify we got all diagnoses
        assert len(history) == 3
        
        # Verify reverse chronological order (most recent first)
        # The last stored diagnosis should be first in the history
        assert history[0]['disease_name'] == 'Powdery Mildew'
        assert history[1]['disease_name'] == 'Late Blight'
        assert history[2]['disease_name'] == 'Early Blight'
        
        # Verify timestamps are in descending order
        timestamps = [d.get('created_at', '') for d in history]
        assert timestamps == sorted(timestamps, reverse=True)
    
    def test_limit_parameter(self):
        """Test that limit parameter restricts number of results"""
        # Store 5 diagnoses
        for i in range(5):
            diagnosis = {
                'disease_name': f'Disease {i}',
                'confidence': 80.0 + i,
                'treatment': f'Treatment {i}',
                'image_s3_key': f'images/test/image{i}.jpg',
                'language': 'en'
            }
            self.repository.store_diagnosis(self.test_user_id, diagnosis)
        
        # Retrieve with limit of 3
        history = self.repository.get_diagnosis_history(self.test_user_id, limit=3)
        
        # Should only get 3 most recent
        assert len(history) == 3
        
        # Should be the last 3 stored (most recent)
        assert history[0]['disease_name'] == 'Disease 4'
        assert history[1]['disease_name'] == 'Disease 3'
        assert history[2]['disease_name'] == 'Disease 2'
    
    def test_lambda_handler_success(self):
        """Test Lambda handler returns diagnosis history successfully"""
        # Store a diagnosis
        diagnosis = {
            'disease_name': 'Test Disease',
            'confidence': 88.0,
            'treatment': 'Test Treatment',
            'image_s3_key': 'images/test/image.jpg',
            'language': 'en'
        }
        self.repository.store_diagnosis(self.test_user_id, diagnosis)
        
        # Call Lambda handler
        event = {
            'queryStringParameters': {
                'user_id': self.test_user_id,
                'limit': '20'
            }
        }
        
        response = lambda_handler(event, None)
        
        # Verify response
        assert response['statusCode'] == 200
        
        body = json.loads(response['body'])
        assert 'diagnoses' in body
        assert len(body['diagnoses']) == 1
        assert body['diagnoses'][0]['disease_name'] == 'Test Disease'
        assert body['diagnoses'][0]['confidence'] == 88.0
    
    def test_lambda_handler_missing_user_id(self):
        """Test Lambda handler returns error when user_id is missing"""
        event = {
            'queryStringParameters': {}
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'user_id is required' in body['error']['message']
    
    def test_lambda_handler_empty_history(self):
        """Test Lambda handler returns empty list when no history exists"""
        event = {
            'queryStringParameters': {
                'user_id': 'nonexistent_user',
                'limit': '20'
            }
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['diagnoses'] == []
        assert body['count'] == 0
    
    def test_diagnosis_contains_required_fields(self):
        """Test that retrieved diagnoses contain all required fields"""
        # Store a diagnosis
        diagnosis = {
            'disease_name': 'Test Disease',
            'confidence': 85.5,
            'treatment': 'Test Treatment',
            'image_s3_key': 'images/test/image.jpg',
            'language': 'en'
        }
        self.repository.store_diagnosis(self.test_user_id, diagnosis)
        
        # Retrieve history
        history = self.repository.get_diagnosis_history(self.test_user_id, limit=20)
        
        assert len(history) == 1
        diagnosis_record = history[0]
        
        # Verify required fields
        assert 'disease_name' in diagnosis_record
        assert 'confidence' in diagnosis_record
        assert 'treatment' in diagnosis_record
        assert 'created_at' in diagnosis_record
        assert 'PK' in diagnosis_record
        assert 'SK' in diagnosis_record
        
        # Verify field values
        assert diagnosis_record['disease_name'] == 'Test Disease'
        assert diagnosis_record['confidence'] == 85.5
        assert diagnosis_record['treatment'] == 'Test Treatment'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
