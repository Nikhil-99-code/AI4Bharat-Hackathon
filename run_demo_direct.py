"""
Quick Demo Runner - Direct AWS Access (No Lambda/API Gateway needed)
This bypasses Lambda and API Gateway for quick testing
"""

import streamlit as st
import sys
import os
import boto3
import base64
from datetime import datetime
from PIL import Image
import io

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from shared.config import get_config
from shared.bedrock_client import get_bedrock_client
from shared.dynamodb_repository import DynamoDBRepository
from shared.image_validator import get_image_validator

# Page config
st.set_page_config(
    page_title="Agri-Nexus V1 - Quick Demo",
    page_icon="🌾",
    layout="wide"
)

# Initialize config
config = get_config()

# Initialize AWS clients
@st.cache_resource
def get_aws_clients():
    bedrock = get_bedrock_client()
    dynamodb = DynamoDBRepository(config.table_name)
    validator = get_image_validator()
    s3 = boto3.client(
        's3',
        region_name=config.aws_region,
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )
    return bedrock, dynamodb, validator, s3

bedrock_client, db_repo, image_validator, s3_client = get_aws_clients()

# Title
st.title("🌾 Agri-Nexus V1 - Quick Demo")
st.caption("Direct AWS access mode (no Lambda/API Gateway)")

# Sidebar
with st.sidebar:
    st.header("Settings")
    user_id = st.text_input("User ID", value="demo_user_001")
    language = st.selectbox("Language", ["en", "hi", "bn"], index=0)
    
    st.divider()
    st.info("✅ DynamoDB Connected\n✅ S3 Connected\n✅ Bedrock Connected")

# Tabs
tab1, tab2, tab3 = st.tabs(["🔬 Dr. Crop", "📊 History", "ℹ️ About"])

# Tab 1: Dr. Crop
with tab1:
    st.header("Crop Disease Diagnosis")
    
    uploaded_file = st.file_uploader(
        "Upload crop image",
        type=['jpg', 'jpeg', 'png'],
        help="Upload a clear image of the affected crop"
    )
    
    if uploaded_file:
        # Display image
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_container_width=True)
        
        if st.button("🔍 Analyze Crop", type="primary"):
            with st.spinner("Analyzing image..."):
                try:
                    # Read image bytes
                    image_bytes = uploaded_file.getvalue()
                    
                    # Validate image
                    validation = image_validator.validate_image(image_bytes, uploaded_file.name, language)
                    if not validation.is_valid:
                        st.error(f"❌ {validation.error_message}")
                    else:
                        # Upload to S3
                        image_key = f"images/{user_id}/{datetime.utcnow().isoformat()}.jpg"
                        s3_client.put_object(
                            Bucket=config.image_bucket,
                            Key=image_key,
                            Body=image_bytes,
                            ContentType='image/jpeg'
                        )
                        
                        # Encode for Bedrock
                        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                        
                        # Create prompt
                        prompt = """Analyze this crop image and provide:
1. Crop type identification
2. Disease/pest diagnosis (if any)
3. Severity level (Healthy/Mild/Moderate/Severe)
4. Treatment recommendations
5. Preventive measures

Provide response in JSON format."""
                        
                        # Call Bedrock
                        response = bedrock_client.invoke_model(
                            modelId=config.bedrock_model_id,
                            body={
                                "anthropic_version": "bedrock-2023-05-31",
                                "max_tokens": 2048,
                                "temperature": 0.2,
                                "messages": [
                                    {
                                        "role": "user",
                                        "content": [
                                            {
                                                "type": "image",
                                                "source": {
                                                    "type": "base64",
                                                    "media_type": "image/jpeg",
                                                    "data": image_base64
                                                }
                                            },
                                            {
                                                "type": "text",
                                                "text": prompt
                                            }
                                        ]
                                    }
                                ]
                            }
                        )
                        
                        diagnosis_text = response['content'][0]['text']
                        
                        # Save to DynamoDB
                        diagnosis_id = f"DIAG#{user_id}#{datetime.utcnow().isoformat()}"
                        db_repo.save_diagnosis(
                            user_id=user_id,
                            diagnosis_id=diagnosis_id,
                            image_url=f"s3://{config.image_bucket}/{image_key}",
                            diagnosis=diagnosis_text,
                            language=language
                        )
                        
                        # Display results
                        st.success("✅ Analysis Complete!")
                        st.subheader("Diagnosis Results")
                        st.write(diagnosis_text)
                        
                        st.info(f"💾 Saved to database with ID: {diagnosis_id}")
                        
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# Tab 2: History
with tab2:
    st.header("Diagnosis History")
    
    if st.button("🔄 Load History"):
        with st.spinner("Loading history..."):
            try:
                history = db_repo.get_diagnosis_history(user_id, limit=10)
                
                if history:
                    st.success(f"Found {len(history)} diagnoses")
                    
                    for idx, diag in enumerate(history, 1):
                        with st.expander(f"Diagnosis #{idx} - {diag.get('timestamp', 'N/A')}"):
                            st.write(f"**ID:** {diag.get('diagnosis_id', 'N/A')}")
                            st.write(f"**Timestamp:** {diag.get('timestamp', 'N/A')}")
                            st.write(f"**Language:** {diag.get('language', 'N/A')}")
                            st.write("**Diagnosis:**")
                            st.write(diag.get('diagnosis', 'No diagnosis data'))
                else:
                    st.info("No diagnosis history found")
                    
            except Exception as e:
                st.error(f"❌ Error loading history: {str(e)}")

# Tab 3: About
with tab3:
    st.header("About Agri-Nexus V1")
    st.write("""
    **Agri-Nexus V1** is an AI-powered agricultural platform that helps farmers with:
    
    - 🔬 **Dr. Crop**: AI-based crop disease diagnosis using image analysis
    - 🎤 **Sahayak**: Voice-based agricultural assistant (coming soon)
    - 📊 **Alerts**: Market price alerts and notifications (coming soon)
    
    ### Current Demo Mode
    This is a **direct access demo** that connects directly to AWS services:
    - ✅ Amazon Bedrock (Claude 3.5 Sonnet) for AI analysis
    - ✅ DynamoDB for data storage
    - ✅ S3 for image storage
    
    ### Full Deployment
    For production use, deploy Lambda functions and API Gateway using:
    ```bash
    python infrastructure/deploy_lambdas.py
    python deploy_api_gateway.py
    ```
    
    ### Technology Stack
    - Frontend: Streamlit
    - AI: Amazon Bedrock (Claude 3.5 Sonnet)
    - Storage: DynamoDB + S3
    - Backend: AWS Lambda + API Gateway (optional)
    """)
    
    st.divider()
    st.caption("Built for AI4Bharat Hackathon 2024")

# Footer
st.divider()
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("AWS Region", config.aws_region)
with col2:
    st.metric("DynamoDB Table", config.table_name)
with col3:
    st.metric("S3 Bucket", config.image_bucket)
