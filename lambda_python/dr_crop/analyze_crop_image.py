import json
import base64
import os
from datetime import datetime
from uuid import uuid4
import boto3
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from lib.bedrock_client import BedrockClient
from lib.dynamodb_repository import DynamoDBRepository
from lib.prompt_templates import get_prompt

s3 = boto3.client('s3')
bedrock = BedrockClient()
db = DynamoDBRepository(os.environ['TABLE_NAME'])

def handler(event, context):
    try:
        body = json.loads(event['body'])
        farmer_id = body['farmerId']
        image_data = base64.b64decode(body['imageData'])
        image_format = body['imageFormat']
        language = body.get('language', 'en')
        
        if len(image_data) > 10*1024*1024 or len(image_data) < 10*1024:
            return {'statusCode': 400, 'body': json.dumps({'error': 'Invalid image size'})}
        
        key = f"crop-images/{farmer_id}/{int(datetime.now().timestamp())}.{image_format}"
        s3.put_object(Bucket=os.environ['IMAGE_BUCKET'], Key=key, Body=image_data)
        image_url = f"s3://{os.environ['IMAGE_BUCKET']}/{key}"
        
        prompt = get_prompt('crop_diagnosis', {'cropType': body.get('cropType', 'unknown'), 'location': body.get('location', 'unknown')}, language)
        response = bedrock.invoke(prompt['user'], [{'format': image_format, 'bytes': image_data}], prompt['system'])
        
        diagnosis = json.loads(response[response.find('{'):response.rfind('}')+1]) if '{' in response else {'diseaseIdentified': False, 'confidence': 0.5}
        diagnosis_id = str(uuid4())
        
        db.put_item({'PK': f"USER#{farmer_id}", 'SK': f"DIAGNOSIS#{int(datetime.now().timestamp())}", 'diagnosisId': diagnosis_id, 'imageUrl': image_url, **diagnosis})
        
        return {'statusCode': 200, 'body': json.dumps({'diagnosisId': diagnosis_id, 'imageUrl': image_url, **diagnosis})}
    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
