import json

SCHEMES = {
    'PM-KISAN': {'name': 'Pradhan Mantri Kisan Samman Nidhi', 'benefits': '₹6,000/year', 'eligibility': 'All landholding farmers'},
    'PMFBY': {'name': 'Pradhan Mantri Fasal Bima Yojana', 'benefits': 'Crop insurance', 'eligibility': 'All farmers'}
}

def handler(event, context):
    try:
        body = json.loads(event['body'])
        farmer_id = body['farmerId']
        schemes = list(SCHEMES.values())
        return {'statusCode': 200, 'body': json.dumps({'farmerId': farmer_id, 'schemes': schemes})}
    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
