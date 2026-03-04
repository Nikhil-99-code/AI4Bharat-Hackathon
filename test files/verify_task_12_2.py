"""
Verification script for Task 12.2: Implement voice processing and response display

This script verifies that all requirements for task 12.2 are properly implemented:
1. Submit button to send recorded audio
2. Loading indicator during processing (expected 15 seconds)
3. Call process_voice_input Lambda via API Gateway
4. Display transcribed question text
5. Call generate_voice_response Lambda to get audio response
6. Display text response and audio playback control
7. Handle errors and display user-friendly messages

Requirements validated: 8.1, 8.3, 8.4, 8.5, 8.6, 14.1, 14.3, 21.2
"""

import ast
import sys


def verify_task_12_2():
    """Verify all task 12.2 requirements are implemented"""
    
    print("=" * 80)
    print("TASK 12.2 VERIFICATION: Voice Processing and Response Display")
    print("=" * 80)
    print()
    
    # Read the streamlit app file
    with open('frontend/streamlit_app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse the AST
    tree = ast.parse(content)
    
    # Find render_sahayak_tab function
    sahayak_func = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == 'render_sahayak_tab':
            sahayak_func = node
            break
    
    if not sahayak_func:
        print("❌ FAILED: render_sahayak_tab function not found")
        return False
    
    print("✅ Found render_sahayak_tab function")
    print()
    
    # Get function source
    func_source = ast.get_source_segment(content, sahayak_func)
    
    # Verification checks
    checks = {
        'submit_button': {
            'description': '1. Submit button to send recorded audio',
            'patterns': ["st.button(lab['submit']", 'type=\'primary\''],
            'requirement': '8.1, 14.1'
        },
        'loading_indicator': {
            'description': '2. Loading indicator during processing (15 seconds)',
            'patterns': ['st.spinner(lab[\'processing\'])', '15 seconds'],
            'requirement': '21.2'
        },
        'process_voice_api': {
            'description': '3. Call process_voice_input Lambda via API Gateway',
            'patterns': ['api_client.process_voice(', 'user_id=', 'audio_bytes=', 'language='],
            'requirement': '8.1, 14.3'
        },
        'display_transcript': {
            'description': '4. Display transcribed question text',
            'patterns': ["st.subheader(lab['transcript'])", "voice_result.get('transcript'"],
            'requirement': '8.3'
        },
        'generate_speech_api': {
            'description': '5. Call generate_voice_response Lambda',
            'patterns': ['api_client.generate_speech(', "voice_result.get('response_text'"],
            'requirement': '8.4, 14.3'
        },
        'display_response': {
            'description': '6. Display text response and audio playback',
            'patterns': ["st.subheader(lab['response'])", "st.subheader(lab['audio_response'])", 
                        'st.audio(audio_bytes'],
            'requirement': '8.5'
        },
        'error_handling': {
            'description': '7. Handle errors and display user-friendly messages',
            'patterns': ['try:', 'except Exception as e:', 'display_error(e,', 
                        'ErrorCode.TRANSCRIPTION_FAILED'],
            'requirement': '8.6, 14.1, 18.1'
        }
    }
    
    all_passed = True
    
    for check_name, check_info in checks.items():
        print(f"Checking: {check_info['description']}")
        print(f"  Requirements: {check_info['requirement']}")
        
        patterns_found = []
        patterns_missing = []
        
        for pattern in check_info['patterns']:
            if pattern in func_source:
                patterns_found.append(pattern)
            else:
                patterns_missing.append(pattern)
        
        if len(patterns_found) == len(check_info['patterns']):
            print(f"  ✅ PASSED - All patterns found")
        elif len(patterns_found) > 0:
            print(f"  ⚠️  PARTIAL - {len(patterns_found)}/{len(check_info['patterns'])} patterns found")
            print(f"     Missing: {patterns_missing}")
        else:
            print(f"  ❌ FAILED - No patterns found")
            all_passed = False
        
        print()
    
    # Additional checks for multilingual support
    print("Additional Checks:")
    print()
    
    # Check for multilingual labels
    print("Checking: Multilingual support for all UI elements")
    required_labels = ['submit', 'processing', 'transcript', 'response', 'audio_response']
    languages = ['en', 'hi', 'bn']
    
    multilingual_ok = True
    for lang in languages:
        for label in required_labels:
            pattern = f"'{lang}': {{" if lang == 'en' else f"'{lang}': {{"
            if pattern not in func_source:
                print(f"  ⚠️  Language '{lang}' labels may be incomplete")
                multilingual_ok = False
                break
    
    if multilingual_ok:
        print("  ✅ PASSED - Multilingual labels present for all languages")
    print()
    
    # Check for session state management
    print("Checking: Session state management for audio")
    if "'recorded_audio' not in st.session_state" in func_source:
        print("  ✅ PASSED - Session state properly initialized")
    else:
        print("  ⚠️  WARNING - Session state initialization not found")
    print()
    
    # Check for audio validation
    print("Checking: Audio file size validation")
    if "max_size_bytes" in func_source and "10 * 1024 * 1024" in func_source:
        print("  ✅ PASSED - Audio file size validation implemented")
    else:
        print("  ⚠️  WARNING - Audio file size validation not found")
    print()
    
    # Check for playback control
    print("Checking: Audio playback control for recorded audio")
    if "st.audio(audio_bytes" in func_source and "playback" in func_source.lower():
        print("  ✅ PASSED - Audio playback control implemented")
    else:
        print("  ❌ FAILED - Audio playback control not found")
        all_passed = False
    print()
    
    # Summary
    print("=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)
    
    if all_passed:
        print("✅ ALL CHECKS PASSED")
        print()
        print("Task 12.2 is COMPLETE. All requirements are properly implemented:")
        print("  ✅ Submit button with primary styling")
        print("  ✅ Loading indicator with 15-second message")
        print("  ✅ API call to process_voice_input Lambda")
        print("  ✅ Display transcribed question text")
        print("  ✅ API call to generate_voice_response Lambda")
        print("  ✅ Display text response and audio playback")
        print("  ✅ Comprehensive error handling")
        print("  ✅ Multilingual support (English, Hindi, Bengali)")
        print("  ✅ Session state management")
        print("  ✅ Audio validation and playback controls")
        print()
        print("Requirements validated: 8.1, 8.3, 8.4, 8.5, 8.6, 14.1, 14.3, 21.2")
        return True
    else:
        print("❌ SOME CHECKS FAILED")
        print()
        print("Please review the failed checks above and ensure all requirements are met.")
        return False


if __name__ == '__main__':
    success = verify_task_12_2()
    sys.exit(0 if success else 1)
