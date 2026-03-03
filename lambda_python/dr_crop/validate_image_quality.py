import json
import base64
from io import BytesIO
from PIL import Image

def handler(event, context):
    try:
        body = json.loads(event['body'])
        image_data = base64.b64decode(body['imageData'])
        img = Image.open(BytesIO(image_data))
        width, height = img.size
        size = len(image_data)
        
        issues = []
        if width < 800 or height < 600:
            issues.append({'type': 'resolution', 'severity': 'warning', 'message': 'Low resolution'})
        if size > 10*1024*1024:
            issues.append({'type': 'size', 'severity': 'error', 'message': 'File too large'})
        if size < 10*1024:
            issues.append({'type': 'size', 'severity': 'error', 'message': 'File too small'})
        
        valid = not any(i['severity'] == 'error' for i in issues)
        
        return {'statusCode': 200, 'body': json.dumps({'valid': valid, 'issues': issues, 'metadata': {'width': width, 'height': height, 'format': img.format.lower(), 'size': size}})}
    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
