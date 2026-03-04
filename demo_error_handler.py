"""
Demonstration of Error Handler functionality
Shows how error messages are displayed in different languages
"""

from shared.error_handler import ErrorCode, get_error_handler


def demo_error_messages():
    """Demonstrate error messages in all supported languages"""
    handler = get_error_handler()
    
    print("=" * 80)
    print("AGRI-NEXUS ERROR HANDLER DEMONSTRATION")
    print("=" * 80)
    print()
    
    # Test different error codes
    error_codes = [
        ErrorCode.IMAGE_QUALITY_LOW,
        ErrorCode.NETWORK_TIMEOUT,
        ErrorCode.DIAGNOSIS_FAILED,
        ErrorCode.SMS_DELIVERY_FAILED,
    ]
    
    languages = {
        'en': 'English',
        'hi': 'Hindi (हिंदी)',
        'bn': 'Bengali (বাংলা)'
    }
    
    for error_code in error_codes:
        print(f"\n{error_code.value}")
        print("-" * 80)
        
        for lang_code, lang_name in languages.items():
            message = handler.get_user_message(error_code, lang_code)
            print(f"  [{lang_name}]")
            print(f"  {message}")
            print()


def demo_error_handling():
    """Demonstrate complete error handling flow"""
    handler = get_error_handler()
    
    print("\n" + "=" * 80)
    print("ERROR HANDLING FLOW DEMONSTRATION")
    print("=" * 80)
    print()
    
    # Simulate an error
    print("Simulating a diagnosis failure...")
    try:
        raise ValueError("Bedrock API returned invalid response")
    except Exception as e:
        result = handler.handle_error(
            error=e,
            error_code=ErrorCode.DIAGNOSIS_FAILED,
            language='en',
            context={'operation': 'analyze_crop_image', 'image_size': 2048000},
            user_id='farmer_123',
            request_id='req_abc123'
        )
        
        print("\nUser sees:")
        print(f"  ❌ {result['message']}")
        print(f"\nError Code: {result['error_code']}")
        print(f"Timestamp: {result['timestamp']}")
        print("\nDetailed technical information has been logged to CloudWatch")
        print("(Stack traces and context are NOT shown to the user)")


def demo_network_timeout_guidance():
    """Demonstrate actionable guidance for network errors"""
    handler = get_error_handler()
    
    print("\n" + "=" * 80)
    print("ACTIONABLE GUIDANCE DEMONSTRATION")
    print("=" * 80)
    print()
    
    print("Network timeout error messages include actionable guidance:")
    print()
    
    for lang_code, lang_name in [('en', 'English'), ('hi', 'Hindi'), ('bn', 'Bengali')]:
        message = handler.get_user_message(ErrorCode.NETWORK_TIMEOUT, lang_code)
        print(f"[{lang_name}]")
        print(f"  {message}")
        print()


if __name__ == '__main__':
    demo_error_messages()
    demo_error_handling()
    demo_network_timeout_guidance()
    
    print("\n" + "=" * 80)
    print("DEMONSTRATION COMPLETE")
    print("=" * 80)
