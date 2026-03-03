import json
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from lib.bedrock_client import BedrockClient
from lib.dynamodb_repository import DynamoDBRepository

bedrock = BedrockClient()
db = DynamoDBRepository(os.environ['TABLE_NAME'])

def handler(event, context):
    try:
        body = json.loads(event['body'])
        farmer_id = body['farmerId']
        
        profile = db.get_item(f"USER#{farmer_id}", "PROFILE")
        if not profile:
            return {'statusCode': 404, 'body': json.dumps({'error': 'Farmer not found'})}
        
        crop_types = profile.get('cropTypes', [])
        prompt = f"Analyze portfolio for crops: {', '.join(crop_types)}. Provide optimization suggestions."
        analysis = bedrock.invoke(prompt)
        
        return {'statusCode': 200, 'body': json.dumps({'farmerId': farmer_id, 'cropTypes': crop_types, 'analysis': analysis})}
    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
