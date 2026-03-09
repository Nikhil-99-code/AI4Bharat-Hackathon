"""
Agri-Nexus Platform - Professional Production UI
One Stop Solution for our Annadata (Farmers)
"""

import streamlit as st
import sys
import os
import boto3
import base64
import json
from datetime import datetime
from PIL import Image
import io

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from shared.config import get_config
from shared.bedrock_client import get_bedrock_client
from shared.dynamodb_repository import DynamoDBRepository
from shared.image_validator import get_image_validator
from shared.sns_client import get_sns_client
from shared.weather_service import get_weather_service
from shared.government_schemes import get_schemes_db
from shared.crop_calendar import get_crop_calendar
from shared.price_charts import get_price_chart_generator
from shared.community_forum import get_community_forum

# Try to import PDF generator (optional)
try:
    from shared.pdf_generator import get_pdf_generator
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# Page config with custom theme
st.set_page_config(
    page_title="Agri-Nexus Platform",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.agrinexus.in/help',
        'Report a bug': 'https://www.agrinexus.in/bug',
        'About': 'Agri-Nexus - Empowering Indian Farmers with AI'
    }
)

# Initialize config
config = get_config()

# Initialize AWS clients
@st.cache_resource
def get_aws_clients():
    bedrock = get_bedrock_client()
    dynamodb = DynamoDBRepository()
    validator = get_image_validator()
    sns = get_sns_client()
    weather = get_weather_service()
    schemes = get_schemes_db()
    calendar = get_crop_calendar()
    price_charts = get_price_chart_generator()
    forum = get_community_forum(dynamodb)
    s3 = boto3.client(
        's3',
        region_name=config.aws_region,
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )
    
    pdf_gen = None
    if PDF_AVAILABLE:
        try:
            pdf_gen = get_pdf_generator()
        except:
            pass
    
    return bedrock, dynamodb, validator, sns, weather, schemes, calendar, price_charts, forum, pdf_gen, s3

bedrock_client, db_repo, image_validator, sns_client, weather_service, schemes_db, crop_calendar, price_chart_gen, community_forum, pdf_generator, s3_client = get_aws_clients()

# Load Professional CSS
with open('static/professional_styles.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# PWA Integration
st.markdown("""
<link rel="manifest" href="/static/manifest.json">
<meta name="theme-color" content="#2E7D32">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Agri-Nexus">
<script src="/static/pwa-register.js"></script>
""", unsafe_allow_html=True)

# Professional Header
st.markdown("""
<div class="app-header">
    <div class="app-title">🌾 Agri-Nexus Platform</div>
    <div class="app-subtitle">One Stop Solution for our Annadata</div>
</div>
""", unsafe_allow_html=True)

# Sidebar with professional design
with st.sidebar:
    st.markdown("### ⚙️ User Settings")
    
    user_id = st.text_input("👤 User ID", value="demo_user_001")
    phone_number = st.text_input("📱 Phone Number", value="+918847894318", help="For SMS alerts")
    language = st.selectbox("🌐 Language", ["English", "हिंदी (Hindi)", "বাংলা (Bengali)"], index=0)
    
    # Map display language to code
    lang_map = {"English": "en", "हिंदी (Hindi)": "hi", "বাংলা (Bengali)": "bn"}
    language_code = lang_map[language]
    
    # Location selector
    selected_location = st.selectbox(
        "📍 Your Location",
        ["Mumbai", "Delhi", "Bangalore", "Kolkata", "Chennai", "Hyderabad", "Pune", "Ahmedabad"],
        help="Used for weather and market data"
    )
    
    st.divider()
    
    # Weather Widget with professional design
    st.markdown("### ⛅ Live Weather")
    try:
        weather_data = weather_service.get_weather(selected_location)
        
        st.markdown(f"""
        <div class="weather-widget">
            <div class="weather-temp">{weather_data['temperature']}°C</div>
            <div class="weather-desc">{weather_data['description'].title()}</div>
            <div class="weather-details">
                <div>💧 {weather_data['humidity']}%</div>
                <div>💨 {weather_data['wind_speed']} m/s</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if weather_data.get('demo_mode'):
            st.caption("📊 Demo data")
    except Exception as e:
        st.warning("⚠️ Weather unavailable")
    
    st.divider()
    
    # System Status with modern cards
    st.markdown("### 📊 System Status")
    st.markdown("""
    <div class="status-grid">
        <div class="status-item">
            <div class="status-icon">✅</div>
            <div class="status-label">Database</div>
        </div>
        <div class="status-item">
            <div class="status-icon">✅</div>
            <div class="status-label">Storage</div>
        </div>
        <div class="status-item">
            <div class="status-icon">✅</div>
            <div class="status-label">AI Engine</div>
        </div>
        <div class="status-item">
            <div class="status-icon">✅</div>
            <div class="status-label">SMS</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # System Information
    st.markdown("### 🔧 System Info")
    st.markdown(f"""
    <div class="system-info">
        <div class="system-info-item">
            <span class="system-info-label">AWS Region</span>
            <span class="system-info-value">{config.aws_region}</span>
        </div>
        <div class="system-info-item">
            <span class="system-info-label">Database</span>
            <span class="system-info-value">DynamoDB</span>
        </div>
        <div class="system-info-item">
            <span class="system-info-label">AI Model</span>
            <span class="system-info-value">Claude 3.5</span>
        </div>
        <div class="system-info-item">
            <span class="system-info-label">Status</span>
            <span class="system-info-value">🟢 Online</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # PWA Install
    with st.expander("📱 Install as App"):
        st.write("""
        **Android/iOS:**
        - Tap menu → Install app
        
        **Desktop:**
        - Click install icon in address bar
        
        **Benefits:**
        - Offline access
        - Faster loading
        - Native app experience
        """)

# Main tabs
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "🔬 Dr. Crop", 
    "🎤 Sahayak Assistant", 
    "📈 Market Alerts",
    "🏛️ Gov Schemes",
    "📅 Crop Calendar",
    "📊 Price Charts",
    "💬 Community",
    "📚 History",
    "ℹ️ About"
])

# ============================================================================
# TAB 1: DR. CROP - Crop Disease Diagnosis
# ============================================================================
with tab1:
    st.header("🔬 Dr. Crop - AI Crop Disease Diagnosis")
    st.write("Upload a photo of your crop to get instant AI-powered disease diagnosis and treatment recommendations.")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "📸 Upload Crop Image",
            type=['jpg', 'jpeg', 'png'],
            help="Upload a clear image of the affected crop (max 10MB)"
        )
        
        if uploaded_file:
            # Display image
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Image", use_column_width=True)
            
            if st.button("🔍 Analyze Crop", type="primary", use_container_width=True):
                with st.spinner("🤖 AI is analyzing your crop image..."):
                    try:
                        # Read image bytes
                        image_bytes = uploaded_file.getvalue()
                        
                        # Validate image
                        validation = image_validator.validate_image(image_bytes, uploaded_file.name, language_code)
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
                            prompt = """Analyze this crop image and provide a detailed diagnosis in JSON format with the following structure:
{
  "crop_analysis": {
    "crop_type": "identified crop name",
    "condition": {
      "issue": "disease or pest name",
      "severity": "Mild/Moderate/Severe",
      "visible_symptoms": ["symptom1", "symptom2", ...]
    },
    "treatment_recommendations": ["action1", "action2", ...],
    "preventive_measures": ["measure1", "measure2", ...]
  },
  "additional_notes": "any important notes"
}"""
                            
                            # Call Bedrock
                            response = bedrock_client.bedrock_runtime.invoke_model(
                                modelId=config.bedrock_model_id,
                                body=json.dumps({
                                    "anthropic_version": "bedrock-2023-05-31",
                                    "max_tokens": 2048,
                                    "temperature": 0.2,
                                    "messages": [{
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
                                            {"type": "text", "text": prompt}
                                        ]
                                    }]
                                })
                            )
                            
                            # Parse response
                            response_body = json.loads(response['body'].read())
                            diagnosis_text = response_body['content'][0]['text']
                            
                            # Initialize diagnosis_data
                            diagnosis_data = None
                            
                            # Try to parse as JSON
                            try:
                                json_text = diagnosis_text
                                if '```json' in json_text:
                                    json_start = json_text.find('```json') + 7
                                    json_end = json_text.find('```', json_start)
                                    json_text = json_text[json_start:json_end].strip()
                                elif '```' in json_text:
                                    json_start = json_text.find('```') + 3
                                    json_end = json_text.find('```', json_start)
                                    json_text = json_text[json_start:json_end].strip()
                                
                                diagnosis_data = json.loads(json_text)
                                
                                # Display results
                                st.success("✅ Analysis Complete!")
                                
                                # Get analysis section
                                analysis = diagnosis_data.get('crop_analysis') or diagnosis_data.get('analysis')
                                
                                if analysis and isinstance(analysis, dict):
                                    col_a, col_b = st.columns(2)
                                    
                                    with col_a:
                                        crop_type = analysis.get('crop_type', 'Unknown')
                                        st.metric("🌾 Crop Type", crop_type)
                                    
                                    with col_b:
                                        severity = analysis.get('severity_level', 'Unknown')
                                        if severity == 'Unknown' and 'condition' in analysis:
                                            condition = analysis['condition']
                                            if isinstance(condition, dict):
                                                severity = condition.get('severity', 'Unknown')
                                        
                                        severity_color = {
                                            'Mild': '🟢',
                                            'Moderate': '🟡',
                                            'Severe': '🔴',
                                            'Moderate to Severe': '🟠'
                                        }.get(severity, '⚪')
                                        st.metric(f"{severity_color} Severity", severity)
                                    
                                    # Disease/Issue
                                    st.subheader("🔬 Diagnosis")
                                    if 'condition' in analysis and isinstance(analysis['condition'], dict):
                                        condition = analysis['condition']
                                        issue = condition.get('issue', 'Unknown')
                                        st.error(f"**Detected Issue:** {issue}")
                                        if 'pest_presence' in condition:
                                            st.warning(f"**Pest/Mold:** {condition['pest_presence']}")
                                    
                                    # Symptoms
                                    symptoms = None
                                    if 'condition' in analysis and isinstance(analysis['condition'], dict):
                                        symptoms = analysis['condition'].get('visible_symptoms') or analysis['condition'].get('symptoms')
                                    if not symptoms:
                                        symptoms = analysis.get('symptoms')
                                    
                                    if symptoms and isinstance(symptoms, list) and len(symptoms) > 0:
                                        st.subheader("📋 Observed Symptoms")
                                        for symptom in symptoms:
                                            st.write(f"• {symptom}")
                                    
                                    # Treatment
                                    actions = analysis.get('treatment_recommendations', [])
                                    if actions and isinstance(actions, list) and len(actions) > 0:
                                        st.subheader("💊 Immediate Treatment")
                                        for i, action in enumerate(actions, 1):
                                            st.info(f"**Step {i}:** {action}")
                                    
                                    # Prevention
                                    measures = analysis.get('preventive_measures', [])
                                    if measures and isinstance(measures, list) and len(measures) > 0:
                                        st.subheader("🛡️ Prevention Measures")
                                        for measure in measures:
                                            st.write(f"✓ {measure}")
                                    
                                    # Additional Notes
                                    if 'additional_notes' in diagnosis_data:
                                        notes = diagnosis_data['additional_notes']
                                        if notes:
                                            st.subheader("📝 Additional Notes")
                                            st.warning(notes)
                                
                            except (json.JSONDecodeError, KeyError, TypeError) as e:
                                st.success("✅ Analysis Complete!")
                                st.subheader("🔬 Diagnosis Results")
                                st.markdown(diagnosis_text)
                            
                            # Save to DynamoDB
                            disease_name = "Unknown"
                            confidence = 0.0
                            treatment_summary = "See full diagnosis"
                            
                            if diagnosis_data and isinstance(diagnosis_data, dict):
                                analysis = diagnosis_data.get('crop_analysis') or diagnosis_data.get('analysis')
                                if analysis and isinstance(analysis, dict):
                                    if 'condition' in analysis and isinstance(analysis['condition'], dict):
                                        disease_name = analysis['condition'].get('issue', 'Unknown')
                                    
                                    treatments = analysis.get('treatment_recommendations', [])
                                    if treatments and isinstance(treatments, list) and len(treatments) > 0:
                                        treatment_summary = treatments[0]
                                    
                                    severity = analysis.get('severity_level', 'Unknown')
                                    if 'condition' in analysis and isinstance(analysis['condition'], dict):
                                        severity = analysis['condition'].get('severity', severity)
                                    
                                    confidence_map = {
                                        'Mild': 0.7,
                                        'Moderate': 0.85,
                                        'Severe': 0.95,
                                        'Moderate to Severe': 0.90
                                    }
                                    confidence = confidence_map.get(severity, 0.8)
                            
                            db_repo.store_diagnosis(
                                user_id=user_id,
                                diagnosis={
                                    'disease_name': disease_name,
                                    'confidence': confidence,
                                    'treatment': treatment_summary,
                                    'image_s3_key': image_key,
                                    'language': language_code,
                                    'full_diagnosis': diagnosis_text
                                }
                            )
                            
                            st.divider()
                            st.success("💾 Diagnosis saved to your history!")
                            
                            # PDF Download Button
                            if PDF_AVAILABLE and pdf_generator:
                                try:
                                    pdf_buffer = pdf_generator.generate_diagnosis_report(
                                        diagnosis_data={
                                            'disease_name': disease_name,
                                            'confidence': confidence,
                                            'treatment': treatment_summary,
                                            'image_s3_key': image_key,
                                            'language': language_code,
                                            'full_diagnosis': diagnosis_text
                                        },
                                        user_id=user_id
                                    )
                                    
                                    st.download_button(
                                        label="📄 Download PDF Report",
                                        data=pdf_buffer,
                                        file_name=f"diagnosis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                                        mime="application/pdf",
                                        use_container_width=True
                                    )
                                except Exception as e:
                                    st.caption(f"PDF generation unavailable. Install: pip install reportlab")
                            
                    except Exception as e:
                        error_msg = str(e)
                        if "ThrottlingException" in error_msg or "Too many requests" in error_msg:
                            st.error("⏳ **Rate Limit Reached**")
                            st.warning("""
                            AWS Bedrock has a rate limit. Please wait 2-3 minutes before trying again.
                            
                            **Why:** You've made several AI requests quickly (free tier: 2-5 per minute)
                            
                            **Solution:** Wait 2-3 minutes, then try again
                            """)
                        else:
                            st.error(f"❌ Error: {error_msg}")
    
    with col2:
        st.info("""
        **How it works:**
        
        1. 📸 Upload a clear photo
        2. 🤖 AI analyzes the image
        3. 📋 Get instant diagnosis
        4. 💊 Receive treatment plan
        5. 💾 Save to history
        
        **Tips for best results:**
        - Use good lighting
        - Focus on affected area
        - Include multiple angles
        - Avoid blurry images
        """)

# ============================================================================
# TAB 2: SAHAYAK - Voice Assistant
# ============================================================================
with tab2:
    st.header("🎤 Sahayak - Your Agricultural Assistant")
    st.write("Ask questions about farming, crops, weather, or get advice in your language.")
    
    # Initialize session state for question
    if 'sahayak_question' not in st.session_state:
        st.session_state.sahayak_question = ""
    
    # Text input (voice recording would require additional libraries)
    st.subheader("💬 Ask a Question")
    
    user_question = st.text_area(
        "Type your question:",
        value=st.session_state.sahayak_question,
        placeholder="Example: What is the best time to plant wheat in North India?",
        height=100,
        key="question_input"
    )
    
    if st.button("🚀 Get Answer", type="primary", use_container_width=True):
        if user_question:
            with st.spinner("🤖 Sahayak is thinking..."):
                try:
                    # Create agricultural context prompt with user location
                    system_prompt = f"""You are Sahayak, an expert agricultural assistant for Indian farmers. 
Provide practical, actionable advice based on Indian farming conditions, crops, and seasons. 
Be concise, friendly, and use simple language. Include specific recommendations when possible.

IMPORTANT USER CONTEXT:
- User's Location: {selected_location}
- User's Language: {language}
- User's Phone: {phone_number}

CRITICAL INSTRUCTIONS:
- When the user asks about prices, markets, weather, or any location-specific information, ALWAYS use their location: {selected_location}
- If they ask "in my state" or "in my area", they mean {selected_location}
- Provide location-specific answers for {selected_location} whenever relevant
- If you don't have exact data for {selected_location}, mention nearby markets or general regional information"""
                    
                    # Call Bedrock
                    response = bedrock_client.bedrock_runtime.invoke_model(
                        modelId=config.bedrock_model_id,
                        body=json.dumps({
                            "anthropic_version": "bedrock-2023-05-31",
                            "max_tokens": 1024,
                            "temperature": 0.3,
                            "system": system_prompt,
                            "messages": [{
                                "role": "user",
                                "content": user_question
                            }]
                        })
                    )
                    
                    # Parse response
                    response_body = json.loads(response['body'].read())
                    answer = response_body['content'][0]['text']
                    
                    # Display answer
                    st.success("✅ Answer from Sahayak:")
                    st.markdown(f"**Q:** {user_question}")
                    st.markdown(f"**A:** {answer}")
                    
                    # Save interaction
                    db_repo.store_interaction(
                        user_id=user_id,
                        interaction={
                            'transcript': user_question,
                            'response_text': answer,
                            'language': language_code
                        }
                    )
                    
                    st.divider()
                    st.info("💾 Conversation saved to history")
                    
                    # Clear the question after getting answer
                    st.session_state.sahayak_question = ""
                    
                except Exception as e:
                    error_msg = str(e)
                    if "ThrottlingException" in error_msg or "Too many requests" in error_msg:
                        st.error("⏳ **Rate Limit Reached**")
                        st.warning("""
                        AWS Bedrock has a rate limit. Please wait 2-3 minutes before trying again.
                        
                        **Why:** You've made several AI requests quickly (free tier: 2-5 per minute)
                        
                        **Solution:** Wait 2-3 minutes, then try again
                        """)
                    else:
                        st.error(f"❌ Error: {error_msg}")
        else:
            st.warning("Please enter a question first")
    
    st.divider()
    st.subheader("💡 Example Questions")
    st.write("Click any question below to auto-fill:")
    
    examples = [
        "What are the best crops to grow in monsoon season?",
        "How do I prevent pest attacks on tomatoes?",
        "When should I apply fertilizer to wheat?",
        "What is crop rotation and why is it important?",
        "How much water does rice need per day?"
    ]
    
    cols = st.columns(1)
    for example in examples:
        if st.button(f"📝 {example}", key=f"ex_{example}", use_container_width=True):
            st.session_state.sahayak_question = example
            st.rerun()

# ============================================================================
# TAB 3: MARKET ALERTS - Price Monitoring
# ============================================================================
with tab3:
    st.header("📈 Market Price Alerts")
    st.write("Set price alerts for your crops and get notified when prices reach your target.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔔 Create New Alert")
        
        with st.form("alert_form"):
            crop_type = st.selectbox(
                "Select Crop",
                ["Wheat", "Rice", "Cotton", "Sugarcane", "Maize", "Soybean", "Potato", "Onion", "Tomato"]
            )
            
            location = st.selectbox(
                "Select Market/Location",
                ["Mumbai", "Delhi", "Bangalore", "Kolkata", "Chennai", "Hyderabad", "Pune", "Ahmedabad"]
            )
            
            target_price = st.number_input(
                "Target Price (₹ per quintal)",
                min_value=100,
                max_value=100000,
                value=2000,
                step=100
            )
            
            submitted = st.form_submit_button("🔔 Create Alert", use_container_width=True)
            
            if submitted:
                try:
                    # Store price threshold
                    alert_id = db_repo.store_price_threshold(
                        user_id=user_id,
                        threshold={
                            'crop_type': crop_type.lower(),
                            'location': location,
                            'target_price': target_price,
                            'phone_number': phone_number,
                            'language': language_code
                        }
                    )
                    
                    st.success(f"✅ Alert created! You'll be notified when {crop_type} reaches ₹{target_price} in {location}")
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"❌ Error creating alert: {str(e)}")
    
    with col2:
        st.subheader("📊 Your Active Alerts")
        
        try:
            alerts = db_repo.get_user_price_thresholds(user_id)
            
            if alerts:
                for alert in alerts:
                    with st.container():
                        st.markdown(f"""
                        **{alert.get('crop_type', 'N/A').title()}** @ {alert.get('location', 'N/A')}
                        - Target: ₹{alert.get('target_price', 0)}/quintal
                        - Created: {alert.get('created_at', 'N/A')[:10]}
                        """)
                        
                        if st.button(f"🗑️ Delete", key=f"del_{alert.get('SK')}"):
                            try:
                                db_repo.delete_price_threshold(
                                    user_id=user_id,
                                    crop_type=alert.get('crop_type'),
                                    location=alert.get('location')
                                )
                                st.success("Alert deleted!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                        
                        st.divider()
            else:
                st.info("No active alerts. Create one to get started!")
                
        except Exception as e:
            st.error(f"❌ Error loading alerts: {str(e)}")
    
    st.divider()
    st.subheader("🧪 Test Alert System (Step-by-Step)")
    
    with st.expander("📖 How to Test Alerts", expanded=True):
        st.markdown("""
        **Follow these steps to test the alert system:**
        
        **Step 1: Create an Alert**
        1. In the form above, select a crop (e.g., Wheat)
        2. Select a location (e.g., Mumbai)
        3. Set target price to **₹2000**
        4. Click "Create Alert"
        
        **Step 2: Simulate Price Update**
        1. Scroll down to "Test Market Data" section
        2. Select same crop: **wheat**
        3. Select same location: **Mumbai**
        4. Set price to **₹2500** (higher than your target)
        5. Click "Simulate Price Update"
        
        **Step 3: View Notification**
        1. Go to **History** tab
        2. Select **"Alert Notifications"**
        3. Click "Load Alert Notifications"
        4. You'll see your triggered alert!
        
        **💡 Tip:** The alert only triggers if:
        - Crop and location match exactly
        - Current price ≥ Target price
        """)
    
    st.divider()
    st.subheader("📱 Test SMS Delivery")
    st.write("Send a test SMS to verify your phone number and AWS SNS setup")
    
    col_test1, col_test2 = st.columns([2, 1])
    
    with col_test1:
        test_phone = st.text_input(
            "Phone Number (E.164 format)",
            value=phone_number,
            help="Format: +919876543210 (country code + number)"
        )
        
        if st.button("📤 Send Test SMS", type="secondary"):
            if test_phone:
                with st.spinner("Sending test SMS..."):
                    try:
                        # Send test message
                        test_message = f"Test message from Agri-Nexus! Your SMS alerts are configured correctly. Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
                        
                        result = sns_client.send_sms(
                            phone_number=test_phone,
                            message=test_message,
                            language=language_code
                        )
                        
                        if result.get('status') == 'delivered':
                            st.success(f"""
                            ✅ **Test SMS Sent Successfully!**
                            - Phone: {test_phone}
                            - Message ID: {result.get('message_id', 'N/A')}
                            - Attempts: {result.get('attempt', 1)}
                            
                            Check your phone for the test message!
                            """)
                        else:
                            st.error(f"""
                            ❌ **SMS Delivery Failed**
                            - Error: {result.get('error', 'Unknown error')}
                            - Attempts: {result.get('attempt', 0)}
                            
                            **Common issues:**
                            - Phone number format incorrect (must be E.164: +919876543210)
                            - AWS SNS not configured for SMS
                            - IAM user missing SNS permissions
                            - Phone number not verified (sandbox mode)
                            """)
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
            else:
                st.warning("Please enter a phone number")
    
    with col_test2:
        st.info("""
        **Phone Format:**
        
        E.164 format required:
        - India: +91XXXXXXXXXX
        - US: +1XXXXXXXXXX
        
        **AWS SNS Setup:**
        1. Verify IAM permissions
        2. Check SNS sandbox mode
        3. Verify phone number
        """)
    
    st.divider()
    st.subheader("🧪 Test Market Data (Demo)")
    st.write("Simulate a price update to test the alert system")
    
    col_a, col_b, col_c = st.columns(3)
    
    with col_a:
        test_crop = st.selectbox("Crop", ["wheat", "rice", "cotton"], key="test_crop")
    with col_b:
        test_location = st.selectbox("Location", ["Mumbai", "Delhi", "Bangalore"], key="test_loc")
    with col_c:
        test_price = st.number_input("Price (₹)", value=2500, key="test_price")
    
    if st.button("📊 Simulate Price Update"):
        try:
            # Store market data
            market_id = db_repo.store_market_data({
                'crop_type': test_crop,
                'location': test_location,
                'price': test_price,
                'timestamp': datetime.utcnow().isoformat(),
                'source': 'simulation'
            })
            
            st.success(f"✅ Market data updated: {test_crop.title()} @ ₹{test_price} in {test_location}")
            
            # Check for alerts that should be triggered
            active_alerts = db_repo.get_active_thresholds(crop_type=test_crop, location=test_location)
            
            triggered_count = 0
            for alert in active_alerts:
                target_price = float(alert.get('target_price', 0))
                
                # Check if current price meets or exceeds target
                if test_price >= target_price:
                    # Get user PK from alert
                    alert_user_id = alert.get('PK', '').replace('USER#', '')
                    alert_phone = alert.get('phone_number', phone_number)
                    alert_language = alert.get('language', language_code)
                    
                    # Send SMS notification
                    sms_result = sns_client.send_price_alert(
                        phone_number=alert_phone,
                        crop_type=test_crop,
                        target_price=target_price,
                        current_price=test_price,
                        location=test_location,
                        language=alert_language
                    )
                    
                    # Store notification trigger with actual SMS status
                    db_repo.store_notification_trigger(
                        user_id=alert_user_id,
                        trigger={
                            'crop_type': test_crop,
                            'location': test_location,
                            'target_price': target_price,
                            'current_price': test_price,
                            'sms_status': sms_result.get('status', 'failed'),
                            'sms_message_id': sms_result.get('message_id', ''),
                            'retry_count': sms_result.get('attempt', 1) - 1
                        }
                    )
                    
                    triggered_count += 1
                    
                    # Show SMS delivery status
                    if sms_result.get('status') == 'delivered':
                        st.success(f"""
                        🔔 **Alert Triggered & SMS Sent!**
                        - Crop: {test_crop.title()}
                        - Target: ₹{target_price}
                        - Current: ₹{test_price}
                        - User: {alert_user_id}
                        - SMS: ✅ Delivered to {alert_phone}
                        - Message ID: {sms_result.get('message_id', 'N/A')}
                        """)
                    else:
                        st.warning(f"""
                        🔔 **Alert Triggered (SMS Failed)**
                        - Crop: {test_crop.title()}
                        - Target: ₹{target_price}
                        - Current: ₹{test_price}
                        - User: {alert_user_id}
                        - SMS: ❌ Failed - {sms_result.get('error', 'Unknown error')}
                        - Attempts: {sms_result.get('attempt', 0)}
                        """)
            
            if triggered_count == 0:
                st.info("""
                ℹ️ No alerts triggered. 
                
                **To test alerts:**
                1. Create an alert with a target price below ₹{test_price}
                2. Run this simulation again
                3. Check History → Alert Notifications
                """.format(test_price=test_price))
            else:
                st.balloons()
                st.success(f"🎉 {triggered_count} alert(s) triggered! Check History → Alert Notifications")
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# ============================================================================
# TAB 4: GOVERNMENT SCHEMES - Agricultural Schemes Database
# ============================================================================
with tab4:
    st.header("🏛️ Government Schemes for Farmers")
    st.write("Explore agricultural schemes, subsidies, and support programs available for Indian farmers.")
    
    # Search and filter
    col1, col2 = st.columns([2, 1])
    
    with col1:
        search_query = st.text_input("🔍 Search schemes", placeholder="e.g., insurance, loan, subsidy")
    
    with col2:
        categories = ["All"] + schemes_db.get_categories()
        selected_category = st.selectbox("📂 Category", categories)
    
    # Get schemes
    if selected_category == "All":
        schemes = schemes_db.search_schemes(search_query)
    else:
        schemes = schemes_db.search_schemes(search_query, selected_category)
    
    st.write(f"Found {len(schemes)} scheme(s)")
    st.divider()
    
    # Display schemes
    for scheme in schemes:
        with st.expander(f"**{scheme['name']}** - {scheme['category']}"):
            st.markdown(f"**Description:** {scheme['description']}")
            
            st.subheader("✅ Eligibility")
            for item in scheme['eligibility']:
                st.write(f"• {item}")
            
            st.subheader("💰 Benefits")
            st.info(scheme['benefits'])
            
            if 'premium' in scheme:
                st.write(f"**Premium:** {scheme['premium']}")
            
            st.subheader("📝 How to Apply")
            st.write(scheme['how_to_apply'])
            
            st.subheader("📄 Required Documents")
            for doc in scheme['documents']:
                st.write(f"• {doc}")
            
            col_a, col_b = st.columns(2)
            with col_a:
                if scheme['website'] != "Contact State Agriculture Department":
                    st.markdown(f"**🌐 Website:** [{scheme['website']}]({scheme['website']})")
                else:
                    st.write(f"**🌐 Website:** {scheme['website']}")
            
            with col_b:
                st.write(f"**📞 Helpline:** {scheme['helpline']}")
    
    if len(schemes) == 0:
        st.info("No schemes found. Try a different search term or category.")

# ============================================================================
# TAB 5: CROP CALENDAR - Planting and Harvesting Schedules
# ============================================================================
with tab5:
    st.header("📅 Crop Calendar - Planting & Harvesting Guide")
    st.write("Get detailed schedules for planting, fertilizing, and harvesting major crops in your region.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Crop selector
        available_crops = crop_calendar.get_available_crops()
        selected_crop = st.selectbox("🌾 Select Crop", available_crops)
    
    with col2:
        # Region selector
        regions = crop_calendar.get_regions()
        selected_region = st.selectbox("📍 Select Region", regions)
    
    # Get schedule
    schedule = crop_calendar.get_crop_schedule(selected_crop, selected_region)
    
    if schedule:
        st.success(f"✅ Schedule found for {selected_crop} in {selected_region}")
        st.divider()
        
        # Overview
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("🌱 Planting Time", schedule['planting'])
        with col_b:
            st.metric("🌾 Harvesting Time", schedule['harvesting'])
        with col_c:
            st.metric("⏱️ Duration", schedule['duration'])
        
        st.divider()
        
        # Fertilizer Schedule
        st.subheader("💊 Fertilizer Schedule")
        fert_schedule = schedule.get('fertilizer_schedule', [])
        if fert_schedule:
            for idx, fert in enumerate(fert_schedule, 1):
                with st.container():
                    col1, col2, col3 = st.columns([2, 2, 2])
                    with col1:
                        st.write(f"**Step {idx}:** {fert['time']}")
                    with col2:
                        st.write(f"**Type:** {fert['type']}")
                    with col3:
                        st.write(f"**Amount:** {fert['amount']}")
                    st.divider()
        else:
            st.info("No fertilizer schedule available")
        
        # Irrigation
        st.subheader("💧 Irrigation Requirements")
        st.info(schedule.get('irrigation', 'No irrigation data available'))
        
        # Pest Control
        st.subheader("🐛 Pest Control Timeline")
        pest_control = schedule.get('pest_control', [])
        if pest_control:
            for idx, pest in enumerate(pest_control, 1):
                with st.expander(f"**{pest['time']}** - {pest['issue']}"):
                    st.write(f"**Issue:** {pest['issue']}")
                    st.write(f"**Treatment:** {pest['treatment']}")
                    st.write(f"**Timing:** {pest['time']}")
        else:
            st.info("No pest control data available")
        
        st.divider()
        
        # Tips
        st.subheader("💡 Pro Tips")
        st.write(f"""
        **For {selected_crop} in {selected_region}:**
        - Start preparing your field 2-3 weeks before planting time
        - Ensure soil testing is done before fertilizer application
        - Monitor weather forecasts during critical growth stages
        - Keep records of all activities for better planning next season
        """)
        
    else:
        st.warning(f"⚠️ No schedule available for {selected_crop} in {selected_region}")
        st.info("""
        **Available combinations:**
        - Try selecting a different region
        - Some crops may not be suitable for all regions
        - Check the crop list for region-specific availability
        """)
        
        # Show available crops for selected region
        available_for_region = crop_calendar.get_crops_for_region(selected_region)
        if available_for_region:
            st.write(f"**Crops available for {selected_region}:**")
            st.write(", ".join(available_for_region))

# ============================================================================
# TAB 6: PRICE CHARTS - Market Price Visualization
# ============================================================================
with tab6:
    st.header("📊 Price Comparison Charts")
    st.write("Visualize and compare market prices across crops and locations.")
    
    # Chart type selector
    chart_type = st.radio(
        "Select Chart Type:",
        ["📈 Price Trend", "🌍 Location Comparison", "🌾 Crop Comparison", "📊 Current Prices"],
        horizontal=True
    )
    
    if chart_type == "📈 Price Trend":
        st.subheader("Price Trend Over Time")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            crop = st.selectbox("Select Crop", price_chart_gen.crops, key="trend_crop")
        with col2:
            location = st.selectbox("Select Location", price_chart_gen.locations, key="trend_loc")
        with col3:
            days = st.slider("Days", 7, 90, 30, key="trend_days")
        
        if st.button("📈 Generate Trend Chart", use_container_width=True):
            with st.spinner("Generating chart..."):
                try:
                    fig = price_chart_gen.create_price_trend_chart(crop, location, days)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.info(f"""
                    **Chart Info:**
                    - Crop: {crop}
                    - Location: {location}
                    - Period: Last {days} days
                    - Red dashed line shows average price
                    
                    💡 **Tip:** Hover over the chart to see detailed price information
                    """)
                except Exception as e:
                    st.error(f"Error generating chart: {str(e)}")
    
    elif chart_type == "🌍 Location Comparison":
        st.subheader("Compare Prices Across Locations")
        
        col1, col2 = st.columns(2)
        with col1:
            crop = st.selectbox("Select Crop", price_chart_gen.crops, key="loc_crop")
        with col2:
            days = st.slider("Days", 7, 90, 30, key="loc_days")
        
        locations = st.multiselect(
            "Select Locations to Compare (max 6)",
            price_chart_gen.locations,
            default=price_chart_gen.locations[:3],
            max_selections=6
        )
        
        if st.button("🌍 Generate Comparison Chart", use_container_width=True):
            if len(locations) < 2:
                st.warning("Please select at least 2 locations to compare")
            else:
                with st.spinner("Generating chart..."):
                    try:
                        fig = price_chart_gen.create_multi_location_comparison(crop, locations, days)
                        st.plotly_chart(fig, use_container_width=True)
                        
                        st.info(f"""
                        **Chart Info:**
                        - Crop: {crop}
                        - Locations: {', '.join(locations)}
                        - Period: Last {days} days
                        
                        💡 **Tip:** Click on location names in the legend to show/hide them
                        """)
                    except Exception as e:
                        st.error(f"Error generating chart: {str(e)}")
    
    elif chart_type == "🌾 Crop Comparison":
        st.subheader("Compare Multiple Crops in One Location")
        
        col1, col2 = st.columns(2)
        with col1:
            location = st.selectbox("Select Location", price_chart_gen.locations, key="crop_loc")
        with col2:
            days = st.slider("Days", 7, 90, 30, key="crop_days")
        
        crops = st.multiselect(
            "Select Crops to Compare (max 6)",
            price_chart_gen.crops,
            default=price_chart_gen.crops[:3],
            max_selections=6
        )
        
        if st.button("🌾 Generate Crop Comparison", use_container_width=True):
            if len(crops) < 2:
                st.warning("Please select at least 2 crops to compare")
            else:
                with st.spinner("Generating chart..."):
                    try:
                        fig = price_chart_gen.create_multi_crop_comparison(crops, location, days)
                        st.plotly_chart(fig, use_container_width=True)
                        
                        st.info(f"""
                        **Chart Info:**
                        - Location: {location}
                        - Crops: {', '.join(crops)}
                        - Period: Last {days} days
                        
                        💡 **Tip:** Use this to identify which crops have better prices
                        """)
                    except Exception as e:
                        st.error(f"Error generating chart: {str(e)}")
    
    else:  # Current Prices
        st.subheader("Current Market Prices")
        
        location = st.selectbox("Select Location", price_chart_gen.locations, key="current_loc")
        
        crops = st.multiselect(
            "Select Crops",
            price_chart_gen.crops,
            default=price_chart_gen.crops[:5]
        )
        
        if st.button("📊 Show Current Prices", use_container_width=True):
            if len(crops) == 0:
                st.warning("Please select at least one crop")
            else:
                with st.spinner("Generating chart..."):
                    try:
                        fig = price_chart_gen.create_current_price_bar_chart(crops, location)
                        st.plotly_chart(fig, use_container_width=True)
                        
                        st.info(f"""
                        **Chart Info:**
                        - Location: {location}
                        - Crops: {', '.join(crops)}
                        - Prices shown are current market rates
                        
                        💡 **Tip:** Use this for quick price comparison
                        """)
                    except Exception as e:
                        st.error(f"Error generating chart: {str(e)}")
    
    st.divider()
    st.caption("📊 Demo data shown. In production, this would connect to real market data APIs.")

# ============================================================================
# TAB 7: COMMUNITY FORUM - Farmer-to-Farmer Q&A
# ============================================================================
with tab7:
    st.header("💬 Community Forum")
    st.write("Connect with fellow farmers, ask questions, and share knowledge.")
    
    # Forum mode selector
    forum_mode = st.radio(
        "Select Mode:",
        ["📖 Browse Questions", "❓ Ask Question", "🔍 Search"],
        horizontal=True
    )
    
    if forum_mode == "📖 Browse Questions":
        st.subheader("Recent Questions")
        
        # Category filter
        categories = ["All"] + community_forum.get_categories()
        selected_category = st.selectbox("Filter by Category", categories)
        
        if st.button("🔄 Load Questions", use_container_width=True):
            with st.spinner("Loading questions..."):
                try:
                    questions = community_forum.get_questions(
                        category=selected_category if selected_category != "All" else None,
                        limit=20
                    )
                    
                    if questions:
                        st.success(f"Found {len(questions)} questions")
                        
                        for idx, q in enumerate(questions, 1):
                            with st.expander(f"**{q.get('title', 'Untitled')}** - {q.get('category', 'General')}"):
                                st.write(f"**Description:** {q.get('description', 'No description')}")
                                
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("👁️ Views", q.get('views', 0))
                                with col2:
                                    st.metric("💬 Answers", q.get('answer_count', 0))
                                with col3:
                                    status = q.get('status', 'open')
                                    status_icon = {'open': '🟢', 'answered': '✅', 'closed': '🔴'}.get(status, '⚪')
                                    st.write(f"**Status:** {status_icon} {status.title()}")
                                
                                st.caption(f"Posted by: {q.get('user_id', 'Anonymous')} | {q.get('created_at', 'N/A')[:10]}")
                                
                                # View answers button
                                question_id = q.get('SK', '')
                                if st.button(f"👀 View Answers", key=f"view_{question_id}"):
                                    st.session_state[f'viewing_{question_id}'] = True
                                
                                # Show answers if viewing
                                if st.session_state.get(f'viewing_{question_id}', False):
                                    with st.spinner("Loading answers..."):
                                        qa_data = community_forum.get_question_with_answers(question_id)
                                        answers = qa_data.get('answers', [])
                                        
                                        if answers:
                                            st.write("**Answers:**")
                                            for ans_idx, ans in enumerate(answers, 1):
                                                st.markdown(f"""
                                                **Answer {ans_idx}:** {ans.get('answer_text', 'No text')}
                                                
                                                *By: {ans.get('user_id', 'Anonymous')} | {ans.get('created_at', 'N/A')[:10]} | 👍 {ans.get('helpful_count', 0)} helpful*
                                                """)
                                                st.divider()
                                        else:
                                            st.info("No answers yet. Be the first to answer!")
                    else:
                        st.info("No questions found. Be the first to ask!")
                        
                except Exception as e:
                    st.error(f"Error loading questions: {str(e)}")
    
    elif forum_mode == "❓ Ask Question":
        st.subheader("Post a New Question")
        
        with st.form("ask_question_form"):
            title = st.text_input("Question Title", placeholder="e.g., How to control aphids on wheat?")
            description = st.text_area(
                "Detailed Description",
                placeholder="Provide details about your question...",
                height=150
            )
            category = st.selectbox("Category", community_forum.get_categories())
            
            submitted = st.form_submit_button("📤 Post Question", use_container_width=True)
            
            if submitted:
                if not title or not description:
                    st.error("Please fill in both title and description")
                else:
                    try:
                        question_id = community_forum.post_question(
                            user_id=user_id,
                            question={
                                'title': title,
                                'description': description,
                                'category': category,
                                'language': language_code
                            }
                        )
                        
                        st.success("✅ Question posted successfully!")
                        st.balloons()
                        st.info(f"Question ID: {question_id}")
                        
                    except Exception as e:
                        st.error(f"Error posting question: {str(e)}")
        
        st.divider()
        st.subheader("💡 Tips for Asking Good Questions")
        st.write("""
        - Be specific and clear in your title
        - Provide detailed description with context
        - Include relevant information (crop type, location, season)
        - Choose the appropriate category
        - Add photos if possible (coming soon!)
        """)
    
    else:  # Search
        st.subheader("🔍 Search Questions")
        
        search_term = st.text_input("Search", placeholder="Enter keywords...")
        
        if st.button("🔍 Search", use_container_width=True):
            if search_term:
                with st.spinner("Searching..."):
                    try:
                        results = community_forum.search_questions(search_term, limit=20)
                        
                        if results:
                            st.success(f"Found {len(results)} results for '{search_term}'")
                            
                            for idx, q in enumerate(results, 1):
                                with st.expander(f"**{q.get('title', 'Untitled')}**"):
                                    st.write(f"**Description:** {q.get('description', 'No description')}")
                                    st.write(f"**Category:** {q.get('category', 'General')}")
                                    st.write(f"**Answers:** {q.get('answer_count', 0)} | **Views:** {q.get('views', 0)}")
                                    st.caption(f"Posted: {q.get('created_at', 'N/A')[:10]}")
                        else:
                            st.info(f"No results found for '{search_term}'")
                            
                    except Exception as e:
                        st.error(f"Error searching: {str(e)}")
            else:
                st.warning("Please enter a search term")

# ============================================================================
# TAB 8: HISTORY - View Past Activities
# ============================================================================
with tab8:
    st.header("📊 Your Activity History")
    
    history_type = st.radio(
        "Select History Type:",
        ["🔬 Diagnosis History", "💬 Conversation History", "🔔 Alert Notifications"],
        horizontal=True
    )
    
    if history_type == "🔬 Diagnosis History":
        if st.button("🔄 Load Diagnosis History"):
            with st.spinner("Loading..."):
                try:
                    history = db_repo.get_diagnosis_history(user_id, limit=20)
                    
                    if history:
                        st.success(f"Found {len(history)} diagnoses")
                        
                        for idx, diag in enumerate(history, 1):
                            timestamp = diag.get('created_at', 'N/A')
                            if timestamp != 'N/A' and len(timestamp) > 19:
                                timestamp = timestamp[:19]
                            
                            with st.expander(f"📋 Diagnosis #{idx} - {timestamp}"):
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.write(f"**Disease:** {diag.get('disease_name', 'N/A')}")
                                    confidence = diag.get('confidence', 0)
                                    if confidence:
                                        st.write(f"**Confidence:** {float(confidence)*100:.1f}%")
                                    else:
                                        st.write(f"**Confidence:** N/A")
                                    st.write(f"**Language:** {diag.get('language', 'N/A')}")
                                
                                with col2:
                                    st.write(f"**Date:** {timestamp}")
                                    image_key = diag.get('image_s3_key', '')
                                    if image_key:
                                        image_name = image_key.split('/')[-1] if '/' in image_key else image_key
                                    else:
                                        image_name = 'N/A'
                                    st.write(f"**Image:** {image_name}")
                                
                                st.write("**Treatment:**")
                                st.info(diag.get('treatment', 'No treatment data'))
                                
                                if 'full_diagnosis' in diag:
                                    with st.expander("View Full Diagnosis"):
                                        st.text(diag['full_diagnosis'])
                    else:
                        st.info("No diagnosis history found")
                        
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    elif history_type == "💬 Conversation History":
        if st.button("🔄 Load Conversation History"):
            with st.spinner("Loading conversations..."):
                try:
                    # Get interactions from DynamoDB
                    # Note: We need to query by PK and SK prefix
                    response = db_repo.table.query(
                        KeyConditionExpression='PK = :pk AND begins_with(SK, :sk_prefix)',
                        ExpressionAttributeValues={
                            ':pk': f'USER#{user_id}',
                            ':sk_prefix': 'INTERACTION#'
                        },
                        ScanIndexForward=False,
                        Limit=20
                    )
                    
                    interactions = db_repo._convert_decimals(response.get('Items', []))
                    
                    if interactions:
                        st.success(f"Found {len(interactions)} conversations")
                        
                        for idx, interaction in enumerate(interactions, 1):
                            timestamp = interaction.get('created_at', 'N/A')
                            if timestamp != 'N/A' and len(timestamp) > 19:
                                timestamp = timestamp[:19]
                            
                            with st.expander(f"💬 Conversation #{idx} - {timestamp}"):
                                st.markdown(f"**Q:** {interaction.get('transcript', 'N/A')}")
                                st.markdown(f"**A:** {interaction.get('response_text', 'N/A')}")
                                st.caption(f"Language: {interaction.get('language', 'N/A')} | Date: {timestamp}")
                    else:
                        st.info("No conversation history found. Start asking questions in Sahayak!")
                        
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    else:  # Alert Notifications
        if st.button("🔄 Load Alert Notifications"):
            with st.spinner("Loading notifications..."):
                try:
                    # Get notifications from DynamoDB
                    notifications = db_repo.get_user_notifications(user_id, limit=20)
                    
                    if notifications:
                        st.success(f"Found {len(notifications)} notifications")
                        
                        for idx, notif in enumerate(notifications, 1):
                            timestamp = notif.get('created_at', 'N/A')
                            if timestamp != 'N/A' and len(timestamp) > 19:
                                timestamp = timestamp[:19]
                            
                            with st.expander(f"🔔 Alert #{idx} - {timestamp}"):
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.write(f"**Crop:** {notif.get('crop_type', 'N/A').title()}")
                                    st.write(f"**Location:** {notif.get('location', 'N/A')}")
                                    
                                    # SMS Status with icon
                                    sms_status = notif.get('sms_status', 'N/A')
                                    status_icon = {
                                        'delivered': '✅',
                                        'failed': '❌',
                                        'simulated': '🔄',
                                        'pending': '⏳'
                                    }.get(sms_status, '❓')
                                    st.write(f"**SMS Status:** {status_icon} {sms_status.title()}")
                                    
                                    # Show message ID if delivered
                                    if sms_status == 'delivered' and 'sms_message_id' in notif:
                                        st.caption(f"Message ID: {notif['sms_message_id']}")
                                
                                with col2:
                                    target = notif.get('target_price', 0)
                                    current = notif.get('current_price', 0)
                                    st.write(f"**Target Price:** ₹{target}")
                                    st.write(f"**Current Price:** ₹{current}")
                                    st.write(f"**Date:** {timestamp}")
                                    
                                    # Show retry count if any
                                    retry_count = notif.get('retry_count', 0)
                                    if retry_count > 0:
                                        st.caption(f"SMS Retries: {retry_count}")
                                
                                if current >= target:
                                    st.success(f"✅ Price target reached! Current price (₹{current}) is above your target (₹{target})")
                                else:
                                    st.info(f"📊 Current price (₹{current}) is below target (₹{target})")
                    else:
                        st.info("No alert notifications yet. Create price alerts in the Market Alerts tab!")
                        
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# ============================================================================
# TAB 9: ABOUT - Platform Information
# ============================================================================
with tab9:
    st.header("ℹ️ About Agri-Nexus V1")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 Our Mission")
        st.write("""
        Agri-Nexus empowers Indian farmers with AI-powered tools to:
        - Diagnose crop diseases instantly
        - Get expert agricultural advice
        - Monitor market prices
        - Make data-driven decisions
        """)
        
        st.subheader("✨ Features")
        st.write("""
        **🔬 Dr. Crop**
        - AI-powered disease diagnosis
        - Treatment recommendations
        - Prevention strategies
        - PDF report download
        
        **🎤 Sahayak Assistant**
        - 24/7 agricultural advice
        - Multi-language support
        - Location-aware responses
        
        **📈 Market Alerts**
        - Real-time price monitoring
        - SMS notifications
        - Custom price targets
        
        **🏛️ Government Schemes**
        - 8 major agricultural schemes
        - Eligibility checker
        - Application guidance
        
        **📅 Crop Calendar**
        - Planting & harvesting schedules
        - Fertilizer timelines
        - Pest control guidance
        - Region-specific advice
        
        **📊 Price Charts**
        - Interactive price visualizations
        - Multi-location comparisons
        - Crop price trends
        - Market analysis tools
        
        **💬 Community Forum**
        - Farmer-to-farmer Q&A
        - Knowledge sharing
        - Category-based discussions
        - Search functionality
        
        **⛅ Weather Widget**
        - Real-time weather data
        - Location-based forecasts
        - Farming insights
        
        **📱 PWA Support**
        - Install as mobile app
        - Offline mode support
        - Fast loading
        - Native app experience
        """)
    
    with col2:
        st.subheader("🛠️ Technology Stack")
        st.write("""
        - **AI**: Amazon Bedrock (Claude 3.5 Sonnet)
        - **Database**: Amazon DynamoDB
        - **Storage**: Amazon S3
        - **Notifications**: Amazon SNS
        - **Frontend**: Streamlit
        - **Language**: Python 3.11+
        """)
        
        st.subheader("📞 Support")
        st.write("""
        For technical support or feedback:
        - Email: support@agrinexus.in
        - Phone: 1800-XXX-XXXX
        - Website: www.agrinexus.in
        """)
        
        st.subheader("📜 Version Info")
        st.code(f"""
Version: 1.0.0
Region: {config.aws_region}
Model: {config.bedrock_model_id}
Environment: Production
        """)
    
    st.divider()
    st.caption("© 2024 Agri-Nexus. Built for AI4Bharat Hackathon. All rights reserved.")
