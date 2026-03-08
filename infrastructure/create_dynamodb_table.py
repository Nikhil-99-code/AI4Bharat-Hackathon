"""
DynamoDB Table Creation Script for Agri-Nexus V1 Platform
Creates a single-table design with three Global Secondary Indexes (GSI1, GSI2, GSI3)
"""

import boto3
import os
from dotenv import load_dotenv

load_dotenv()

def create_dynamodb_table():
    """
    Create DynamoDB table with single-table design pattern
    
    Table Schema:
    - PK (String): Partition key
    - SK (String): Sort key
    - GSI1PK (String): Admin dashboard queries
    - GSI1SK (String): Status or timestamp
    - GSI2PK (String): Market data queries
    - GSI2SK (String): Location and timestamp
    - GSI3PK (String): Alert processing
    - GSI3SK (String): Target price and timestamp
    """
    
    # Use credentials from .env file
    dynamodb = boto3.client(
        'dynamodb',
        region_name=os.getenv('AWS_REGION', 'us-east-1'),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )
    table_name = os.getenv('TABLE_NAME', 'agri-nexus-data')
    
    try:
        # Create table with GSIs
        response = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'PK', 'KeyType': 'HASH'},   # Partition key
                {'AttributeName': 'SK', 'KeyType': 'RANGE'}   # Sort key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'PK', 'AttributeType': 'S'},
                {'AttributeName': 'SK', 'AttributeType': 'S'},
                {'AttributeName': 'GSI1PK', 'AttributeType': 'S'},
                {'AttributeName': 'GSI1SK', 'AttributeType': 'S'},
                {'AttributeName': 'GSI2PK', 'AttributeType': 'S'},
                {'AttributeName': 'GSI2SK', 'AttributeType': 'S'},
                {'AttributeName': 'GSI3PK', 'AttributeType': 'S'},
                {'AttributeName': 'GSI3SK', 'AttributeType': 'S'},
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'GSI1',
                    'KeySchema': [
                        {'AttributeName': 'GSI1PK', 'KeyType': 'HASH'},
                        {'AttributeName': 'GSI1SK', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                },
                {
                    'IndexName': 'GSI2',
                    'KeySchema': [
                        {'AttributeName': 'GSI2PK', 'KeyType': 'HASH'},
                        {'AttributeName': 'GSI2SK', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                },
                {
                    'IndexName': 'GSI3',
                    'KeySchema': [
                        {'AttributeName': 'GSI3PK', 'KeyType': 'HASH'},
                        {'AttributeName': 'GSI3SK', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            BillingMode='PROVISIONED',
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            },
            Tags=[
                {'Key': 'Project', 'Value': 'Agri-Nexus-V1'},
                {'Key': 'Environment', 'Value': os.getenv('ENVIRONMENT', 'development')}
            ]
        )
        
        print(f"✅ Table '{table_name}' creation initiated successfully!")
        print(f"Table ARN: {response['TableDescription']['TableArn']}")
        print(f"Table Status: {response['TableDescription']['TableStatus']}")
        print("\nWaiting for table to become active...")
        
        # Wait for table to be active
        waiter = dynamodb.get_waiter('table_exists')
        waiter.wait(TableName=table_name)
        
        print(f"✅ Table '{table_name}' is now ACTIVE and ready to use!")
        
        return response
        
    except dynamodb.exceptions.ResourceInUseException:
        print(f"⚠️  Table '{table_name}' already exists!")
        return None
    except Exception as e:
        print(f"❌ Error creating table: {str(e)}")
        raise


def delete_dynamodb_table():
    """Delete the DynamoDB table (useful for testing/cleanup)"""
    dynamodb = boto3.client(
        'dynamodb',
        region_name=os.getenv('AWS_REGION', 'us-east-1'),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )
    table_name = os.getenv('TABLE_NAME', 'agri-nexus-data')
    
    try:
        dynamodb.delete_table(TableName=table_name)
        print(f"✅ Table '{table_name}' deletion initiated!")
    except dynamodb.exceptions.ResourceNotFoundException:
        print(f"⚠️  Table '{table_name}' does not exist!")
    except Exception as e:
        print(f"❌ Error deleting table: {str(e)}")
        raise


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'delete':
        delete_dynamodb_table()
    else:
        create_dynamodb_table()
