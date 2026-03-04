"""
DynamoDB Repository Layer for Agri-Nexus V1 Platform
Implements single-table design pattern with GSI queries
"""

import boto3
from datetime import datetime
from typing import Dict, List, Optional
from decimal import Decimal
import json

from .config import get_config


class DynamoDBRepository:
    """
    Repository for DynamoDB operations using single-table design
    """
    
    def __init__(self):
        """Initialize DynamoDB client and table"""
        config = get_config()
        self.dynamodb = boto3.resource('dynamodb', region_name=config.aws_region)
        self.table = self.dynamodb.Table(config.table_name)
    
    def _convert_decimals(self, obj):
        """Convert Decimal objects to float for JSON serialization"""
        if isinstance(obj, list):
            return [self._convert_decimals(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: self._convert_decimals(value) for key, value in obj.items()}
        elif isinstance(obj, Decimal):
            return float(obj)
        return obj
    
    # Diagnosis Operations
    
    def store_diagnosis(self, user_id: str, diagnosis: Dict) -> str:
        """
        Store diagnosis result in DynamoDB
        
        Args:
            user_id: User identifier
            diagnosis: Diagnosis data containing disease_name, confidence, treatment, etc.
            
        Returns:
            diagnosis_id: Unique identifier for the diagnosis
        """
        timestamp = datetime.utcnow().isoformat()
        diagnosis_id = f"DIAGNOSIS#{timestamp}"
        
        item = {
            'PK': f'USER#{user_id}',
            'SK': diagnosis_id,
            'GSI1PK': 'DIAGNOSIS',
            'GSI1SK': timestamp,
            'entity_type': 'diagnosis',
            'disease_name': diagnosis.get('disease_name'),
            'confidence': Decimal(str(diagnosis.get('confidence', 0))),
            'treatment': diagnosis.get('treatment'),
            'image_s3_key': diagnosis.get('image_s3_key'),
            'language': diagnosis.get('language', 'en'),
            'created_at': timestamp
        }
        
        self.table.put_item(Item=item)
        return diagnosis_id
    
    def get_diagnosis_history(self, user_id: str, limit: int = 20) -> List[Dict]:
        """
        Retrieve diagnosis history for a user
        
        Args:
            user_id: User identifier
            limit: Maximum number of diagnoses to return (default: 20)
            
        Returns:
            List of diagnosis records in reverse chronological order
        """
        response = self.table.query(
            KeyConditionExpression='PK = :pk AND begins_with(SK, :sk_prefix)',
            ExpressionAttributeValues={
                ':pk': f'USER#{user_id}',
                ':sk_prefix': 'DIAGNOSIS#'
            },
            ScanIndexForward=False,  # Reverse chronological order
            Limit=limit
        )
        
        return self._convert_decimals(response.get('Items', []))
    
    # Voice Interaction Operations
    
    def store_interaction(self, user_id: str, interaction: Dict) -> str:
        """
        Store voice interaction in DynamoDB
        
        Args:
            user_id: User identifier
            interaction: Interaction data containing transcript, response_text, etc.
            
        Returns:
            interaction_id: Unique identifier for the interaction
        """
        timestamp = datetime.utcnow().isoformat()
        interaction_id = f'INTERACTION#{timestamp}'
        
        item = {
            'PK': f'USER#{user_id}',
            'SK': interaction_id,
            'GSI1PK': 'INTERACTION',
            'GSI1SK': timestamp,
            'entity_type': 'interaction',
            'transcript': interaction.get('transcript'),
            'response_text': interaction.get('response_text'),
            'audio_s3_key': interaction.get('audio_s3_key'),
            'language': interaction.get('language', 'en'),
            'created_at': timestamp
        }
        
        self.table.put_item(Item=item)
        return interaction_id
    
    # Price Alert Operations
    
    def store_price_threshold(self, user_id: str, threshold: Dict) -> str:
        """
        Store price alert threshold in DynamoDB
        
        Args:
            user_id: User identifier
            threshold: Threshold data containing crop_type, location, target_price, etc.
            
        Returns:
            alert_id: Unique identifier for the price alert
        """
        timestamp = datetime.utcnow().isoformat()
        crop_type = threshold.get('crop_type')
        location = threshold.get('location')
        target_price = threshold.get('target_price')
        
        alert_id = f'PRICE_TARGET#{crop_type}#{location}'
        
        item = {
            'PK': f'USER#{user_id}',
            'SK': alert_id,
            'GSI3PK': 'ALERT#ACTIVE',
            'GSI3SK': f"{Decimal(str(target_price))}#{timestamp}",
            'entity_type': 'price_threshold',
            'crop_type': crop_type,
            'location': location,
            'target_price': Decimal(str(target_price)),
            'phone_number': threshold.get('phone_number'),
            'language': threshold.get('language', 'en'),
            'status': 'active',
            'created_at': timestamp
        }
        
        self.table.put_item(Item=item)
        return alert_id
    
    def get_user_price_thresholds(self, user_id: str) -> List[Dict]:
        """
        Get all active price thresholds for a user
        
        Args:
            user_id: User identifier
            
        Returns:
            List of active price threshold records
        """
        response = self.table.query(
            KeyConditionExpression='PK = :pk AND begins_with(SK, :sk_prefix)',
            ExpressionAttributeValues={
                ':pk': f'USER#{user_id}',
                ':sk_prefix': 'PRICE_TARGET#'
            }
        )
        
        return self._convert_decimals(response.get('Items', []))
    
    def delete_price_threshold(self, user_id: str, crop_type: str, location: str) -> None:
        """
        Delete a price threshold
        
        Args:
            user_id: User identifier
            crop_type: Crop type
            location: Location
        """
        self.table.delete_item(
            Key={
                'PK': f'USER#{user_id}',
                'SK': f'PRICE_TARGET#{crop_type}#{location}'
            }
        )
    
    def get_active_thresholds(self, crop_type: str = None, location: str = None) -> List[Dict]:
        """
        Query active price thresholds using GSI3
        
        Args:
            crop_type: Optional crop type filter
            location: Optional location filter
            
        Returns:
            List of active price threshold records
        """
        response = self.table.query(
            IndexName='GSI3',
            KeyConditionExpression='GSI3PK = :gsi3pk',
            ExpressionAttributeValues={
                ':gsi3pk': 'ALERT#ACTIVE'
            }
        )
        
        items = self._convert_decimals(response.get('Items', []))
        
        # Apply filters if provided
        if crop_type:
            items = [item for item in items if item.get('crop_type') == crop_type]
        if location:
            items = [item for item in items if item.get('location') == location]
        
        return items
    
    # Market Data Operations
    
    def store_market_data(self, market_data: Dict) -> str:
        """
        Store market price data in DynamoDB
        
        Args:
            market_data: Market data containing crop_type, location, price, etc.
            
        Returns:
            market_data_id: Unique identifier for the market data
        """
        timestamp = market_data.get('timestamp', datetime.utcnow().isoformat())
        crop_type = market_data.get('crop_type')
        location = market_data.get('location')
        
        item = {
            'PK': f'MARKET#{crop_type}',
            'SK': f'LOCATION#{location}#{timestamp}',
            'GSI2PK': crop_type,
            'GSI2SK': f'{location}#{timestamp}',
            'entity_type': 'market_data',
            'crop_type': crop_type,
            'location': location,
            'price': Decimal(str(market_data.get('price'))),
            'source': market_data.get('source', 'manual'),
            'timestamp': timestamp
        }
        
        self.table.put_item(Item=item)
        return f"{crop_type}#{location}#{timestamp}"
    
    def get_latest_price(self, crop_type: str, location: str) -> Optional[Dict]:
        """
        Get latest price for a crop at a location using GSI2
        
        Args:
            crop_type: Crop type
            location: Location
            
        Returns:
            Latest market data record or None
        """
        response = self.table.query(
            IndexName='GSI2',
            KeyConditionExpression='GSI2PK = :crop AND begins_with(GSI2SK, :location)',
            ExpressionAttributeValues={
                ':crop': crop_type,
                ':location': f'{location}#'
            },
            ScanIndexForward=False,  # Most recent first
            Limit=1
        )
        
        items = response.get('Items', [])
        return self._convert_decimals(items[0]) if items else None
    
    # Notification Operations
    
    def store_notification_trigger(self, user_id: str, trigger: Dict) -> str:
        """
        Store notification trigger event in DynamoDB
        
        Args:
            user_id: User identifier
            trigger: Trigger data containing crop_type, target_price, current_price, etc.
            
        Returns:
            notification_id: Unique identifier for the notification
        """
        timestamp = datetime.utcnow().isoformat()
        notification_id = f'NOTIFICATION#{timestamp}'
        
        item = {
            'PK': f'USER#{user_id}',
            'SK': notification_id,
            'GSI3PK': 'ALERT#TRIGGERED',
            'GSI3SK': timestamp,
            'entity_type': 'notification',
            'crop_type': trigger.get('crop_type'),
            'location': trigger.get('location'),
            'target_price': Decimal(str(trigger.get('target_price'))),
            'current_price': Decimal(str(trigger.get('current_price'))),
            'sms_status': trigger.get('sms_status', 'pending'),
            'retry_count': trigger.get('retry_count', 0),
            'created_at': timestamp
        }
        
        self.table.put_item(Item=item)
        return notification_id
    
    def get_user_notifications(self, user_id: str, limit: int = 20) -> List[Dict]:
        """
        Get notification history for a user
        
        Args:
            user_id: User identifier
            limit: Maximum number of notifications to return
            
        Returns:
            List of notification records
        """
        response = self.table.query(
            KeyConditionExpression='PK = :pk AND begins_with(SK, :sk_prefix)',
            ExpressionAttributeValues={
                ':pk': f'USER#{user_id}',
                ':sk_prefix': 'NOTIFICATION#'
            },
            ScanIndexForward=False,
            Limit=limit
        )
        
        return self._convert_decimals(response.get('Items', []))


# Global repository instance
_repository: DynamoDBRepository = None


def get_repository() -> DynamoDBRepository:
    """Get the global repository instance"""
    global _repository
    
    if _repository is None:
        _repository = DynamoDBRepository()
    
    return _repository


if __name__ == '__main__':
    # Test repository operations
    repo = get_repository()
    print("DynamoDB Repository initialized successfully")
    print(f"Table: {repo.table.table_name}")
