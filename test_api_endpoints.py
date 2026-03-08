"""
Quick API endpoint testing script
"""

import requests
import base64
import json
import os
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv('API_GATEWAY_URL')

def test_diagnose_endpoint():
    """Test the /diagnose endpoint"""
    print("\n" + "="*80)
    print("Testing POST /diagnose endpoint")
    print("="*80)
    
    # Create a small test image (1x1 pixel)
    import io
    from PIL import Image
    
    img = Image.new('RGB', (100, 100), color='green')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_base64 = base64.b64encode(img_bytes.getvalue()).decode('utf-8')
    
    payload = {
        'user_id': 'test_user_001',
        'image_data': img_base64,
        'language': 'en'
    }
    
    try:
        response = requests.post(
            f"{API_URL}/diagnose",
            json=payload,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Diagnose endpoint working!")
        else:
            print("❌ Diagnose endpoint failed!")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")


def test_voice_process_endpoint():
    """Test the /voice/process endpoint"""
    print("\n" + "="*80)
    print("Testing POST /voice/process endpoint")
    print("="*80)
    
    # Create dummy audio data
    audio_base64 = base64.b64encode(b"dummy audio data").decode('utf-8')
    
    payload = {
        'user_id': 'test_user_001',
        'audio_data': audio_base64,
        'language': 'en'
    }
    
    try:
        response = requests.post(
            f"{API_URL}/voice/process",
            json=payload,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            print("✅ Voice process endpoint working!")
        else:
            print("⚠️  Voice process endpoint returned error (expected if not fully implemented)")
            
    except Exception as e:
        print(f"⚠️  Error: {str(e)} (expected if not fully implemented)")


def test_market_ingest_endpoint():
    """Test the /market/ingest endpoint"""
    print("\n" + "="*80)
    print("Testing POST /market/ingest endpoint")
    print("="*80)
    
    payload = {
        'crop_type': 'wheat',
        'location': 'Delhi',
        'price': 2500.0,
        'simulation': True
    }
    
    try:
        response = requests.post(
            f"{API_URL}/market/ingest",
            json=payload,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            print("✅ Market ingest endpoint working!")
        else:
            print("⚠️  Market ingest endpoint returned error")
            
    except Exception as e:
        print(f"⚠️  Error: {str(e)}")


if __name__ == '__main__':
    print("\n🧪 Testing Agri-Nexus API Endpoints")
    print(f"API URL: {API_URL}")
    
    if not API_URL or API_URL == 'http://localhost:8000':
        print("\n⚠️  Warning: API Gateway URL not configured in .env file")
        print("Skipping API tests. Run 'streamlit run run_demo_direct.py' instead.")
    else:
        test_diagnose_endpoint()
        test_voice_process_endpoint()
        test_market_ingest_endpoint()
        
        print("\n" + "="*80)
        print("API Testing Complete!")
        print("="*80)
