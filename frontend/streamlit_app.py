"""
Agri-Nexus V1 Platform - Streamlit Frontend Application
Main application with three tabs: Dr. Crop, Sahayak, and Alerts
"""

import streamlit as st
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.config import get_config
from shared.error_handler import ErrorCode, get_error_handler

# Page configuration
st.set_page_config(
    page_title="Agri-Nexus V1",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Multilingual labels
LABELS = {
    'en': {
        'title': '🌾 Agri-Nexus V1 Platform',
        'subtitle': 'AI-Powered Agricultural Assistant',
        'dr_crop': '🔬 Dr. Crop',
        'sahayak': '🎤 Sahayak',
        'alerts': '📊 Alerts',
        'language': 'Language',
        'welcome': 'Welcome to Agri-Nexus! Select a feature from the tabs above.',
        'about': 'About',
        'about_text': 'Agri-Nexus empowers farmers with AI-powered crop diagnosis, voice assistance, and market price alerts.',
    },
    'hi': {
        'title': '🌾 एग्री-नेक्सस V1 प्लेटफॉर्म',
        'subtitle': 'AI-संचालित कृषि सहायक',
        'dr_crop': '🔬 डॉ. क्रॉप',
        'sahayak': '🎤 सहायक',
        'alerts': '📊 अलर्ट',
        'language': 'भाषा',
        'welcome': 'एग्री-नेक्सस में आपका स्वागत है! ऊपर दिए गए टैब से एक सुविधा चुनें।',
        'about': 'के बारे में',
        'about_text': 'एग्री-नेक्सस किसानों को AI-संचालित फसल निदान, आवाज सहायता और बाजार मूल्य अलर्ट के साथ सशक्त बनाता है।',
    },
    'bn': {
        'title': '🌾 এগ্রি-নেক্সাস V1 প্ল্যাটফর্ম',
        'subtitle': 'AI-চালিত কৃষি সহায়ক',
        'dr_crop': '🔬 ডাঃ ক্রপ',
        'sahayak': '🎤 সহায়ক',
        'alerts': '📊 সতর্কতা',
        'language': 'ভাষা',
        'welcome': 'এগ্রি-নেক্সাসে স্বাগতম! উপরের ট্যাব থেকে একটি বৈশিষ্ট্য নির্বাচন করুন।',
        'about': 'সম্পর্কে',
        'about_text': 'এগ্রি-নেক্সাস কৃষকদের AI-চালিত ফসল নির্ণয়, ভয়েস সহায়তা এবং বাজার মূল্য সতর্কতা দিয়ে ক্ষমতায়ন করে।',
    }
}


def initialize_session_state():
    """Initialize session state variables"""
    if 'language' not in st.session_state:
        st.session_state.language = 'en'
    if 'user_id' not in st.session_state:
        st.session_state.user_id = 'demo_user'  # For demo purposes
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = True  # Simplified for hackathon
    if 'error_handler' not in st.session_state:
        st.session_state.error_handler = get_error_handler()


def get_label(key: str) -> str:
    """Get label in current language"""
    lang = st.session_state.language
    return LABELS.get(lang, LABELS['en']).get(key, key)


def display_error(error: Exception, error_code: ErrorCode = None):
    """
    Display user-friendly error message without stack traces
    
    Args:
        error: The exception that occurred
        error_code: Optional error code for specific error types
    """
    handler = st.session_state.error_handler
    language = st.session_state.language
    user_id = st.session_state.get('user_id')
    
    # Handle the error and get user-friendly message
    error_info = handler.handle_error(
        error=error,
        error_code=error_code,
        language=language,
        user_id=user_id
    )
    
    # Display error message to user
    st.error(f"❌ {error_info['message']}")
    
    # Log that error was displayed (detailed logging already done in handler)
    handler.logger.info(f"Error displayed to user: {error_info['error_code']}")


def render_header():
    """Render application header with language selector"""
    col1, col2 = st.columns([4, 1])
    
    with col1:
        st.title(get_label('title'))
        st.caption(get_label('subtitle'))
    
    with col2:
        # Language selector
        language_options = {
            'English': 'en',
            'हिंदी': 'hi',
            'বাংলা': 'bn'
        }
        
        selected_lang = st.selectbox(
            get_label('language'),
            options=list(language_options.keys()),
            index=list(language_options.values()).index(st.session_state.language)
        )
        
        # Update language if changed
        new_lang = language_options[selected_lang]
        if new_lang != st.session_state.language:
            st.session_state.language = new_lang
            st.rerun()


def render_dr_crop_tab():
    """Render Dr. Crop disease diagnosis interface"""
    from shared.image_validator import get_image_validator
    from frontend.api_client import get_api_client
    
    st.header(get_label('dr_crop'))
    
    labels = {
        'en': {
            'upload': 'Upload Crop Image',
            'help': 'Upload a clear photo of your crop showing any disease symptoms (JPEG, PNG, JPG - max 10MB)',
            'analyze': 'Analyze Image',
            'analyzing': 'Analyzing image... This may take up to 30 seconds.',
            'validating': 'Validating image...',
            'result': 'Diagnosis Result',
            'disease': 'Disease',
            'confidence': 'Confidence',
            'treatment': 'Treatment Recommendation',
            'history': 'Diagnosis History',
            'no_history': 'No diagnosis history yet',
            'preview': 'Image Preview',
            'validation_success': '✓ Image validated successfully',
            'diagnosis_success': '✓ Diagnosis completed successfully',
            'diagnosis_error': 'Failed to analyze image. Please try again.',
        },
        'hi': {
            'upload': 'फसल की तस्वीर अपलोड करें',
            'help': 'अपनी फसल की एक स्पष्ट तस्वीर अपलोड करें जिसमें रोग के लक्षण दिखाई दें (JPEG, PNG, JPG - अधिकतम 10MB)',
            'analyze': 'तस्वीर का विश्लेषण करें',
            'analyzing': 'तस्वीर का विश्लेषण हो रहा है... इसमें 30 सेकंड तक का समय लग सकता है।',
            'validating': 'तस्वीर की जांच हो रही है...',
            'result': 'निदान परिणाम',
            'disease': 'रोग',
            'confidence': 'विश्वास',
            'treatment': 'उपचार की सिफारिश',
            'history': 'निदान इतिहास',
            'no_history': 'अभी तक कोई निदान इतिहास नहीं',
            'preview': 'तस्वीर पूर्वावलोकन',
            'validation_success': '✓ तस्वीर सफलतापूर्वक सत्यापित',
            'diagnosis_success': '✓ निदान सफलतापूर्वक पूर्ण हुआ',
            'diagnosis_error': 'तस्वीर का विश्लेषण विफल रहा। कृपया पुनः प्रयास करें।',
        },
        'bn': {
            'upload': 'ফসলের ছবি আপলোড করুন',
            'help': 'আপনার ফসলের একটি স্পষ্ট ছবি আপলোড করুন যেখানে রোগের লক্ষণ দেখা যায় (JPEG, PNG, JPG - সর্বোচ্চ 10MB)',
            'analyze': 'ছবি বিশ্লেষণ করুন',
            'analyzing': 'ছবি বিশ্লেষণ করা হচ্ছে... এটি 30 সেকেন্ড পর্যন্ত সময় নিতে পারে।',
            'validating': 'ছবি যাচাই করা হচ্ছে...',
            'result': 'নির্ণয় ফলাফল',
            'disease': 'রোগ',
            'confidence': 'আত্মবিশ্বাস',
            'treatment': 'চিকিৎসার সুপারিশ',
            'history': 'নির্ণয় ইতিহাস',
            'no_history': 'এখনও কোনো নির্ণয় ইতিহাস নেই',
            'preview': 'ছবি পূর্বরূপ',
            'validation_success': '✓ ছবি সফলভাবে যাচাই করা হয়েছে',
            'diagnosis_success': '✓ নির্ণয় সফলভাবে সম্পন্ন হয়েছে',
            'diagnosis_error': 'ছবি বিশ্লেষণ ব্যর্থ হয়েছে। অনুগ্রহ করে আবার চেষ্টা করুন।',
        }
    }
    
    lang = st.session_state.language
    lab = labels.get(lang, labels['en'])
    
    # Image upload
    uploaded_file = st.file_uploader(
        lab['upload'],
        type=['jpg', 'jpeg', 'png'],
        help=lab['help']
    )
    
    if uploaded_file is not None:
        # Read image bytes
        image_bytes = uploaded_file.read()
        
        # Validate image
        validator = get_image_validator()
        
        with st.spinner(lab['validating']):
            try:
                validation_result = validator.validate_image(
                    image_bytes=image_bytes,
                    filename=uploaded_file.name,
                    language=lang
                )
            except Exception as e:
                display_error(e)
                return
        
        # Display validation result
        if not validation_result.is_valid:
            # Display validation error
            st.error(f"❌ {validation_result.error_message}")
            
            # Display warnings if any
            if validation_result.warnings:
                for warning in validation_result.warnings:
                    st.warning(warning)
            return
        
        # Validation successful
        st.success(lab['validation_success'])
        
        # Display warnings if any
        if validation_result.warnings:
            for warning in validation_result.warnings:
                st.info(warning)
        
        # Display image preview and analysis button
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.image(image_bytes, caption=lab['preview'], use_column_width=True)
        
        with col2:
            if st.button(lab['analyze'], type='primary', use_container_width=True):
                # Get configuration
                try:
                    config = get_config()
                    api_client = get_api_client(config.api_gateway_url, lang)
                except Exception as e:
                    display_error(e, ErrorCode.INVALID_CONFIGURATION)
                    return
                
                # Call diagnosis API with loading indicator
                with st.spinner(lab['analyzing']):
                    try:
                        # Call analyze_crop_image Lambda via API Gateway
                        diagnosis_result = api_client.diagnose_crop(
                            user_id=st.session_state.user_id,
                            image_bytes=image_bytes,
                            language=lang
                        )
                        
                        # Display success message
                        st.success(lab['diagnosis_success'])
                        
                        # Display diagnosis results
                        st.subheader(lab['result'])
                        
                        # Create columns for disease and confidence
                        result_col1, result_col2 = st.columns(2)
                        
                        with result_col1:
                            st.metric(
                                label=lab['disease'],
                                value=diagnosis_result.get('disease_name', 'Unknown')
                            )
                        
                        with result_col2:
                            confidence = diagnosis_result.get('confidence', 0)
                            st.metric(
                                label=lab['confidence'],
                                value=f"{confidence:.1f}%"
                            )
                        
                        # Display treatment recommendation
                        st.markdown(f"**{lab['treatment']}:**")
                        st.write(diagnosis_result.get('treatment', 'No treatment recommendation available'))
                        
                    except Exception as e:
                        # Display error with user-friendly message
                        display_error(e, ErrorCode.DIAGNOSIS_FAILED)
    
    # Diagnosis history
    st.divider()
    st.subheader(lab['history'])
    
    # Fetch diagnosis history
    try:
        config = get_config()
        api_client = get_api_client(config.api_gateway_url, lang)
        
        # Get diagnosis history
        history_response = api_client.get_diagnosis_history(
            user_id=st.session_state.user_id,
            limit=20,
            language=lang
        )
        
        diagnoses = history_response.get('diagnoses', [])
        
        if diagnoses:
            # Display each diagnosis in a card-like format
            for idx, diagnosis in enumerate(diagnoses):
                with st.container():
                    # Create columns for diagnosis info
                    hist_col1, hist_col2, hist_col3 = st.columns([2, 1, 1])
                    
                    with hist_col1:
                        st.markdown(f"**{lab['disease']}:** {diagnosis.get('disease_name', 'Unknown')}")
                    
                    with hist_col2:
                        confidence = diagnosis.get('confidence', 0)
                        st.markdown(f"**{lab['confidence']}:** {confidence:.1f}%")
                    
                    with hist_col3:
                        # Format timestamp
                        timestamp = diagnosis.get('timestamp', diagnosis.get('created_at', ''))
                        if timestamp:
                            # Extract date from ISO timestamp
                            date_str = timestamp.split('T')[0] if 'T' in timestamp else timestamp
                            st.markdown(f"**📅** {date_str}")
                    
                    # Display treatment in expandable section
                    with st.expander(f"{lab['treatment']}"):
                        st.write(diagnosis.get('treatment', 'No treatment recommendation available'))
                    
                    # Add separator between diagnoses (except for last one)
                    if idx < len(diagnoses) - 1:
                        st.markdown("---")
        else:
            st.info(lab['no_history'])
            
    except Exception as e:
        # Display error if history fetch fails
        st.warning(f"⚠️ Could not load diagnosis history. {str(e)}")


def render_sahayak_tab():
    """Render Sahayak voice assistant interface"""
    st.header(get_label('sahayak'))
    
    labels = {
        'en': {
            'record': 'Record Voice Question',
            'help': 'Record your agricultural question using the audio recorder below (max 60 seconds)',
            'upload': 'Or upload an audio file',
            'upload_help': 'Upload a recorded audio file (WAV, MP3, M4A - max 60 seconds)',
            'submit': 'Submit Question',
            'processing': 'Processing your question... This may take up to 15 seconds.',
            'transcript': 'Your Question',
            'response': 'Response',
            'audio_response': 'Audio Response',
            'playback': 'Recorded Audio Playback',
            'recording_status': 'Recording Status',
            'ready': 'Ready to record',
            'recording': 'Recording in progress...',
            'recorded': 'Recording complete',
            'duration_limit': 'Maximum duration: 60 seconds',
            'no_audio': 'Please record or upload audio before submitting',
        },
        'hi': {
            'record': 'आवाज़ प्रश्न रिकॉर्ड करें',
            'help': 'नीचे दिए गए ऑडियो रिकॉर्डर का उपयोग करके अपना कृषि प्रश्न रिकॉर्ड करें (अधिकतम 60 सेकंड)',
            'upload': 'या एक ऑडियो फ़ाइल अपलोड करें',
            'upload_help': 'एक रिकॉर्ड की गई ऑडियो फ़ाइल अपलोड करें (WAV, MP3, M4A - अधिकतम 60 सेकंड)',
            'submit': 'प्रश्न जमा करें',
            'processing': 'आपके प्रश्न को संसाधित किया जा रहा है... इसमें 15 सेकंड तक का समय लग सकता है।',
            'transcript': 'आपका प्रश्न',
            'response': 'उत्तर',
            'audio_response': 'ऑडियो उत्तर',
            'playback': 'रिकॉर्ड किए गए ऑडियो का प्लेबैक',
            'recording_status': 'रिकॉर्डिंग स्थिति',
            'ready': 'रिकॉर्ड करने के लिए तैयार',
            'recording': 'रिकॉर्डिंग प्रगति में...',
            'recorded': 'रिकॉर्डिंग पूर्ण',
            'duration_limit': 'अधिकतम अवधि: 60 सेकंड',
            'no_audio': 'कृपया जमा करने से पहले ऑडियो रिकॉर्ड या अपलोड करें',
        },
        'bn': {
            'record': 'ভয়েস প্রশ্ন রেকর্ড করুন',
            'help': 'নীচের অডিও রেকর্ডার ব্যবহার করে আপনার কৃষি প্রশ্ন রেকর্ড করুন (সর্বোচ্চ 60 সেকেন্ড)',
            'upload': 'অথবা একটি অডিও ফাইল আপলোড করুন',
            'upload_help': 'একটি রেকর্ড করা অডিও ফাইল আপলোড করুন (WAV, MP3, M4A - সর্বোচ্চ 60 সেকেন্ড)',
            'submit': 'প্রশ্ন জমা দিন',
            'processing': 'আপনার প্রশ্ন প্রক্রিয়া করা হচ্ছে... এটি 15 সেকেন্ড পর্যন্ত সময় নিতে পারে।',
            'transcript': 'আপনার প্রশ্ন',
            'response': 'উত্তর',
            'audio_response': 'অডিও উত্তর',
            'playback': 'রেকর্ড করা অডিও প্লেব্যাক',
            'recording_status': 'রেকর্ডিং স্থিতি',
            'ready': 'রেকর্ড করার জন্য প্রস্তুত',
            'recording': 'রেকর্ডিং চলছে...',
            'recorded': 'রেকর্ডিং সম্পূর্ণ',
            'duration_limit': 'সর্বোচ্চ সময়কাল: 60 সেকেন্ড',
            'no_audio': 'অনুগ্রহ করে জমা দেওয়ার আগে অডিও রেকর্ড বা আপলোড করুন',
        }
    }
    
    lang = st.session_state.language
    lab = labels.get(lang, labels['en'])
    
    # Initialize session state for audio
    if 'recorded_audio' not in st.session_state:
        st.session_state.recorded_audio = None
    if 'audio_duration' not in st.session_state:
        st.session_state.audio_duration = 0
    
    st.info(lab['help'])
    
    # Audio recording section
    st.subheader(lab['record'])
    
    # Display duration limit
    st.caption(f"⏱️ {lab['duration_limit']}")
    
    # Audio file uploader (as primary method for MVP)
    uploaded_audio = st.file_uploader(
        lab['upload'],
        type=['wav', 'mp3', 'm4a', 'ogg', 'flac'],
        help=lab['upload_help'],
        key='audio_uploader'
    )
    
    # Handle uploaded audio
    if uploaded_audio is not None:
        # Read audio bytes
        audio_bytes = uploaded_audio.read()
        
        # Validate audio duration (basic check on file size)
        # Rough estimate: 1 minute of audio ≈ 1-2 MB for compressed formats
        max_size_bytes = 10 * 1024 * 1024  # 10 MB to allow for various formats
        
        if len(audio_bytes) > max_size_bytes:
            st.error(f"❌ Audio file is too large. Please ensure your recording is under 60 seconds.")
        else:
            # Store audio in session state
            st.session_state.recorded_audio = audio_bytes
            
            # Display success message
            st.success(f"✅ {lab['recorded']}")
            
            # Display playback control
            st.subheader(lab['playback'])
            st.audio(audio_bytes, format=f'audio/{uploaded_audio.type.split("/")[-1]}')
            
            # Submit button
            if st.button(lab['submit'], type='primary', use_container_width=True):
                if st.session_state.recorded_audio is None:
                    st.warning(lab['no_audio'])
                else:
                    # Get configuration
                    try:
                        from frontend.api_client import get_api_client
                        config = get_config()
                        api_client = get_api_client(config.api_gateway_url, lang)
                    except Exception as e:
                        display_error(e, ErrorCode.INVALID_CONFIGURATION)
                        return
                    
                    # Process voice input with loading indicator
                    with st.spinner(lab['processing']):
                        try:
                            # Call process_voice_input Lambda via API Gateway
                            voice_result = api_client.process_voice(
                                user_id=st.session_state.user_id,
                                audio_bytes=st.session_state.recorded_audio,
                                language=lang
                            )
                            
                            # Display transcript
                            st.subheader(lab['transcript'])
                            st.info(voice_result.get('transcript', 'Unable to transcribe'))
                            
                            # Display text response
                            st.subheader(lab['response'])
                            st.write(voice_result.get('response_text', 'No response available'))
                            
                            # Generate and display audio response
                            try:
                                audio_bytes = api_client.generate_speech(
                                    text=voice_result.get('response_text', ''),
                                    language=lang
                                )
                                
                                if audio_bytes:
                                    st.subheader(lab['audio_response'])
                                    st.audio(audio_bytes, format='audio/mp3')
                            except Exception as e:
                                # Audio response is optional, just log the error
                                st.warning("⚠️ Text-to-speech response unavailable")
                            
                        except Exception as e:
                            # Display error with user-friendly message
                            display_error(e, ErrorCode.TRANSCRIPTION_FAILED)
    else:
        # Show placeholder when no audio is uploaded
        st.info("📤 Please upload an audio file to get started")
        
        # Note about browser recording
        st.caption("💡 Tip: You can record audio using your device's voice recorder app and upload the file here.")


def render_alerts_tab():
    """Render price alerts configuration interface"""
    from frontend.api_client import get_api_client
    from shared.dynamodb_repository import get_repository
    import re
    
    st.header(get_label('alerts'))
    
    labels = {
        'en': {
            'configure': 'Configure Price Alert',
            'crop': 'Crop Type',
            'location': 'Location/Market',
            'target_price': 'Target Price (₹/quintal)',
            'phone': 'Phone Number',
            'create': 'Create Alert',
            'active': 'Active Alerts',
            'no_alerts': 'No active alerts',
            'simulate': 'Simulate Price Change',
            'simulation': 'Price Simulation',
            'help_text': 'Set up alerts to receive SMS notifications when crop prices reach your target.',
            'validation_error': 'Please correct the following errors:',
            'invalid_price': 'Target price must be greater than 0',
            'invalid_location': 'Location cannot be empty',
            'invalid_phone': 'Please enter a valid phone number (e.g., +919876543210)',
            'alert_created': 'Alert created successfully!',
            'alert_deleted': 'Alert deleted successfully',
            'delete': 'Delete',
            'created_on': 'Created',
            'sim_crop': 'Crop for Simulation',
            'sim_location': 'Location for Simulation',
            'sim_price': 'Simulated Price (₹/quintal)',
            'sim_help': 'Test the alert system by simulating a price change',
            'sim_success': 'Price simulation triggered! Alerts will be sent if thresholds are met.',
            'sim_error': 'Failed to simulate price change',
            'creating': 'Creating alert...',
            'deleting': 'Deleting alert...',
            'loading': 'Loading alerts...',
        },
        'hi': {
            'configure': 'मूल्य अलर्ट कॉन्फ़िगर करें',
            'crop': 'फसल का प्रकार',
            'location': 'स्थान/बाजार',
            'target_price': 'लक्ष्य मूल्य (₹/क्विंटल)',
            'phone': 'फ़ोन नंबर',
            'create': 'अलर्ट बनाएं',
            'active': 'सक्रिय अलर्ट',
            'no_alerts': 'कोई सक्रिय अलर्ट नहीं',
            'simulate': 'मूल्य परिवर्तन का अनुकरण करें',
            'simulation': 'मूल्य अनुकरण',
            'help_text': 'जब फसल की कीमतें आपके लक्ष्य तक पहुंचें तो SMS सूचनाएं प्राप्त करने के लिए अलर्ट सेट करें।',
            'validation_error': 'कृपया निम्नलिखित त्रुटियों को ठीक करें:',
            'invalid_price': 'लक्ष्य मूल्य 0 से अधिक होना चाहिए',
            'invalid_location': 'स्थान खाली नहीं हो सकता',
            'invalid_phone': 'कृपया एक वैध फ़ोन नंबर दर्ज करें (उदा. +919876543210)',
            'alert_created': 'अलर्ट सफलतापूर्वक बनाया गया!',
            'alert_deleted': 'अलर्ट सफलतापूर्वक हटाया गया',
            'delete': 'हटाएं',
            'created_on': 'बनाया गया',
            'sim_crop': 'अनुकरण के लिए फसल',
            'sim_location': 'अनुकरण के लिए स्थान',
            'sim_price': 'अनुकरणित मूल्य (₹/क्विंटल)',
            'sim_help': 'मूल्य परिवर्तन का अनुकरण करके अलर्ट सिस्टम का परीक्षण करें',
            'sim_success': 'मूल्य अनुकरण शुरू किया गया! यदि सीमाएं पूरी होती हैं तो अलर्ट भेजे जाएंगे।',
            'sim_error': 'मूल्य परिवर्तन का अनुकरण विफल रहा',
            'creating': 'अलर्ट बनाया जा रहा है...',
            'deleting': 'अलर्ट हटाया जा रहा है...',
            'loading': 'अलर्ट लोड हो रहे हैं...',
        },
        'bn': {
            'configure': 'মূল্য সতর্কতা কনফিগার করুন',
            'crop': 'ফসলের ধরন',
            'location': 'অবস্থান/বাজার',
            'target_price': 'লক্ষ্য মূল্য (₹/কুইন্টাল)',
            'phone': 'ফোন নম্বর',
            'create': 'সতর্কতা তৈরি করুন',
            'active': 'সক্রিয় সতর্কতা',
            'no_alerts': 'কোনো সক্রিয় সতর্কতা নেই',
            'simulate': 'মূল্য পরিবর্তন অনুকরণ করুন',
            'simulation': 'মূল্য অনুকরণ',
            'help_text': 'ফসলের দাম আপনার লক্ষ্যে পৌঁছালে SMS বিজ্ঞপ্তি পেতে সতর্কতা সেট করুন।',
            'validation_error': 'অনুগ্রহ করে নিম্নলিখিত ত্রুটিগুলি সংশোধন করুন:',
            'invalid_price': 'লক্ষ্য মূল্য 0 এর বেশি হতে হবে',
            'invalid_location': 'অবস্থান খালি থাকতে পারে না',
            'invalid_phone': 'অনুগ্রহ করে একটি বৈধ ফোন নম্বর লিখুন (যেমন +919876543210)',
            'alert_created': 'সতর্কতা সফলভাবে তৈরি হয়েছে!',
            'alert_deleted': 'সতর্কতা সফলভাবে মুছে ফেলা হয়েছে',
            'delete': 'মুছুন',
            'created_on': 'তৈরি হয়েছে',
            'sim_crop': 'অনুকরণের জন্য ফসল',
            'sim_location': 'অনুকরণের জন্য অবস্থান',
            'sim_price': 'অনুকরণ মূল্য (₹/কুইন্টাল)',
            'sim_help': 'মূল্য পরিবর্তন অনুকরণ করে সতর্কতা সিস্টেম পরীক্ষা করুন',
            'sim_success': 'মূল্য অনুকরণ শুরু হয়েছে! থ্রেশহোল্ড পূরণ হলে সতর্কতা পাঠানো হবে।',
            'sim_error': 'মূল্য পরিবর্তন অনুকরণ ব্যর্থ হয়েছে',
            'creating': 'সতর্কতা তৈরি করা হচ্ছে...',
            'deleting': 'সতর্কতা মুছে ফেলা হচ্ছে...',
            'loading': 'সতর্কতা লোড হচ্ছে...',
        }
    }
    
    lang = st.session_state.language
    lab = labels.get(lang, labels['en'])
    
    # Help text
    st.info(lab['help_text'])
    
    # Alert configuration form
    st.subheader(lab['configure'])
    
    # Crop types (common Indian crops)
    crop_options = ['Wheat', 'Rice', 'Cotton', 'Sugarcane', 'Maize', 'Soybean', 'Pulses', 'Groundnut']
    
    with st.form('alert_form'):
        col1, col2 = st.columns(2)
        
        with col1:
            crop_type = st.selectbox(
                lab['crop'],
                crop_options
            )
            target_price = st.number_input(
                lab['target_price'],
                min_value=0.0,
                value=2500.0,
                step=50.0,
                format="%.2f"
            )
        
        with col2:
            location = st.text_input(
                lab['location'],
                value='',
                placeholder='e.g., Delhi, Mumbai, Bangalore'
            )
            phone = st.text_input(
                lab['phone'],
                value='',
                placeholder='+919876543210'
            )
        
        submit_button = st.form_submit_button(lab['create'], type='primary', use_container_width=True)
        
        if submit_button:
            # Validate inputs
            errors = []
            
            if target_price <= 0:
                errors.append(lab['invalid_price'])
            
            if not location or location.strip() == '':
                errors.append(lab['invalid_location'])
            
            # Validate phone number format (basic validation)
            phone_pattern = r'^\+?[1-9]\d{1,14}$'  # E.164 format
            if not phone or not re.match(phone_pattern, phone.strip()):
                errors.append(lab['invalid_phone'])
            
            # Display validation errors
            if errors:
                st.error(f"❌ {lab['validation_error']}")
                for error in errors:
                    st.error(f"• {error}")
            else:
                # Create alert
                try:
                    config = get_config()
                    repo = get_repository()
                    
                    with st.spinner(lab['creating']):
                        # Store price threshold in DynamoDB
                        alert_data = {
                            'crop_type': crop_type.lower(),
                            'location': location.strip().lower(),
                            'target_price': target_price,
                            'phone_number': phone.strip(),
                            'language': lang,
                            'status': 'active'
                        }
                        
                        alert_id = repo.store_price_threshold(
                            user_id=st.session_state.user_id,
                            threshold=alert_data
                        )
                        
                        st.success(f"✅ {lab['alert_created']}")
                        st.info(f"📱 You will receive SMS alerts at {phone.strip()} when {crop_type} prices in {location.strip()} reach ₹{target_price:.2f}/quintal")
                        
                        # Rerun to refresh the alerts list
                        st.rerun()
                        
                except Exception as e:
                    display_error(e, ErrorCode.STORAGE_FAILED)
    
    # Active alerts
    st.divider()
    st.subheader(lab['active'])
    
    try:
        config = get_config()
        repo = get_repository()
        
        with st.spinner(lab['loading']):
            # Get active price thresholds for the user
            alerts = repo.get_user_price_thresholds(st.session_state.user_id)
        
        if alerts:
            # Display each alert in a card-like format
            for idx, alert in enumerate(alerts):
                with st.container():
                    # Create columns for alert info and delete button
                    alert_col1, alert_col2, alert_col3, alert_col4 = st.columns([2, 2, 2, 1])
                    
                    with alert_col1:
                        st.markdown(f"**{lab['crop']}:** {alert.get('crop_type', 'Unknown').title()}")
                    
                    with alert_col2:
                        st.markdown(f"**{lab['location']}:** {alert.get('location', 'Unknown').title()}")
                    
                    with alert_col3:
                        target = alert.get('target_price', 0)
                        st.markdown(f"**{lab['target_price']}:** ₹{target:.2f}")
                    
                    with alert_col4:
                        # Delete button with unique key
                        delete_key = f"delete_{alert.get('crop_type')}_{alert.get('location')}_{idx}"
                        if st.button(lab['delete'], key=delete_key, type='secondary'):
                            try:
                                with st.spinner(lab['deleting']):
                                    # Delete the alert
                                    repo.delete_price_threshold(
                                        user_id=st.session_state.user_id,
                                        crop_type=alert.get('crop_type'),
                                        location=alert.get('location')
                                    )
                                    
                                    st.success(f"✅ {lab['alert_deleted']}")
                                    st.rerun()
                                    
                            except Exception as e:
                                display_error(e, ErrorCode.STORAGE_FAILED)
                    
                    # Display additional info
                    info_col1, info_col2 = st.columns([2, 2])
                    
                    with info_col1:
                        phone_display = alert.get('phone_number', 'N/A')
                        st.caption(f"📱 {phone_display}")
                    
                    with info_col2:
                        created_at = alert.get('created_at', '')
                        if created_at:
                            date_str = created_at.split('T')[0] if 'T' in created_at else created_at
                            st.caption(f"{lab['created_on']}: {date_str}")
                    
                    # Add separator between alerts (except for last one)
                    if idx < len(alerts) - 1:
                        st.markdown("---")
        else:
            st.info(lab['no_alerts'])
            
    except Exception as e:
        st.warning(f"⚠️ Could not load active alerts. {str(e)}")
    
    # Simulation
    st.divider()
    st.subheader(lab['simulation'])
    st.caption(lab['sim_help'])
    
    with st.form('simulation_form'):
        sim_col1, sim_col2, sim_col3 = st.columns(3)
        
        with sim_col1:
            sim_crop = st.selectbox(
                lab['sim_crop'],
                crop_options,
                key='sim_crop_select'
            )
        
        with sim_col2:
            sim_location = st.text_input(
                lab['sim_location'],
                value='',
                placeholder='e.g., Delhi',
                key='sim_location_input'
            )
        
        with sim_col3:
            sim_price = st.number_input(
                lab['sim_price'],
                min_value=0.0,
                value=3000.0,
                step=50.0,
                format="%.2f",
                key='sim_price_input'
            )
        
        simulate_button = st.form_submit_button(lab['simulate'], type='primary', use_container_width=True)
        
        if simulate_button:
            if not sim_location or sim_location.strip() == '':
                st.error(lab['invalid_location'])
            elif sim_price <= 0:
                st.error(lab['invalid_price'])
            else:
                try:
                    config = get_config()
                    api_client = get_api_client(config.api_gateway_url, lang)
                    
                    with st.spinner(lab['simulate']):
                        # Call ingest_market_data Lambda with simulation flag
                        result = api_client.simulate_price_change(
                            crop_type=sim_crop.lower(),
                            location=sim_location.strip().lower(),
                            price=sim_price,
                            language=lang
                        )
                        
                        alerts_triggered = result.get('alerts_triggered', 0)
                        
                        if alerts_triggered > 0:
                            st.success(f"🔔 {lab['sim_success']}")
                            st.info(f"📊 {alerts_triggered} alert(s) triggered for {sim_crop} at ₹{sim_price:.2f}/quintal in {sim_location.strip()}")
                        else:
                            st.info(f"📊 Price simulation completed. No alerts triggered (current price ₹{sim_price:.2f} did not meet any thresholds)")
                        
                except Exception as e:
                    st.error(f"❌ {lab['sim_error']}")
                    display_error(e)


def main():
    """Main application entry point"""
    # Initialize session state
    initialize_session_state()
    
    # Load configuration with error handling
    try:
        config = get_config()
    except Exception as e:
        # Display configuration error
        display_error(e, ErrorCode.INVALID_CONFIGURATION)
        st.stop()
    
    # Render header
    render_header()
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs([
        get_label('dr_crop'),
        get_label('sahayak'),
        get_label('alerts')
    ])
    
    with tab1:
        render_dr_crop_tab()
    
    with tab2:
        render_sahayak_tab()
    
    with tab3:
        render_alerts_tab()
    
    # Footer
    st.divider()
    with st.expander(get_label('about')):
        st.write(get_label('about_text'))
        st.caption(f"Environment: {config.environment} | Region: {config.aws_region}")


if __name__ == '__main__':
    main()
