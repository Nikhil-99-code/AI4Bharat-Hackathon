import json
import os
from datetime import datetime
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from lib.dynamodb_repository import DynamoDBRepository

db = DynamoDBRepository(os.environ['TABLE_NAME'])

def handler(event, context):
    try:
        body = json.loads(event['body'])
        crop_type = body['cropType']
        location = body['location']
        price = body['price']
        
        timestamp = int(datetime.now().timestamp())
        db.put_item({'PK': f"MARKET#{crop_type}#{location}", 'SK': f"PRICE#{timestamp}", 'cropType': crop_type, 'location': location, 'price': price, 'timestamp': datetime.now().isoformat()})
        
        return {'statusCode': 200, 'body': json.dumps({'message': 'Market data ingested'})}
    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
