import json
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from lib.bedrock_client import BedrockClient
from lib.dynamodb_repository import DynamoDBRepository
from lib.prompt_templates import get_prompt

bedrock = BedrockClient()
db = DynamoDBRepository(os.environ['TABLE_NAME'])

def handler(event, context):
    try:
        body = json.loads(event['body'])
        crop_type = body['cropType']
        location = body['location']
        language = body.get('language', 'en')
        
        market_data = db.query(f"MARKET#{crop_type}#{location}", 'PRICE#', 1)
        prompt = get_prompt('market_intelligence', {'cropType': crop_type, 'location': location}, language)
        insights = bedrock.invoke(prompt['user'], system=prompt['system'])
        
        return {'statusCode': 200, 'body': json.dumps({'cropType': crop_type, 'location': location, 'currentPrice': market_data[0] if market_data else None, 'insights': insights})}
    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
