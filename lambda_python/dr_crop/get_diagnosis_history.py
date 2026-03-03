import json
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from lib.dynamodb_repository import DynamoDBRepository

db = DynamoDBRepository(os.environ['TABLE_NAME'])

def handler(event, context):
    try:
        params = event.get('queryStringParameters', {})
        farmer_id = params.get('farmerId')
        limit = int(params.get('limit', 50))
        
        if not farmer_id:
            return {'statusCode': 400, 'body': json.dumps({'error': 'farmerId required'})}
        
        diagnoses = db.query(f"USER#{farmer_id}", 'DIAGNOSIS#', limit)
        
        return {'statusCode': 200, 'body': json.dumps({'diagnoses': diagnoses, 'count': len(diagnoses), 'hasMore': len(diagnoses) == limit})}
    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
