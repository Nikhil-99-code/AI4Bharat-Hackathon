import json
import boto3

transcribe = boto3.client('transcribe')

def handler(event, context):
    try:
        body = json.loads(event['body'])
        language = body.get('language', 'en-US')
        
        return {'statusCode': 200, 'body': json.dumps({'transcription': 'Mock transcription', 'language': language, 'confidence': 0.95})}
    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
