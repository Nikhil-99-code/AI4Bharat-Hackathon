import json
import boto3

polly = boto3.client('polly')

def handler(event, context):
    try:
        body = json.loads(event['body'])
        text = body['text']
        language = body.get('language', 'en-US')
        
        voice_map = {'en-US': 'Joanna', 'hi-IN': 'Aditi'}
        response = polly.synthesize_speech(Text=text, OutputFormat='mp3', VoiceId=voice_map.get(language, 'Joanna'))
        audio_data = response['AudioStream'].read()
        
        return {'statusCode': 200, 'body': json.dumps({'audioData': audio_data.hex(), 'format': 'mp3'})}
    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
