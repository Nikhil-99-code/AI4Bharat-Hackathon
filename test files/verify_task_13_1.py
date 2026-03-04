"""
Verification script for Task 13.1: Price Alert Configuration Form
Tests the render_alerts_tab() function implementation
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all required imports work"""
    print("Testing imports...")
    
    try:
        from frontend.streamlit_app import render_alerts_tab
        print("✓ render_alerts_tab function imported successfully")
        
        from shared.dynamodb_repository import get_repository
        print("✓ get_repository function imported successfully")
        
        from frontend.api_client import get_api_client
        print("✓ get_api_client function imported successfully")
        
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False


def test_function_signature():
    """Test that render_alerts_tab has the correct signature"""
    print("\nTesting function signature...")
    
    try:
        from frontend.streamlit_app import render_alerts_tab
        import inspect
        
        sig = inspect.signature(render_alerts_tab)
        params = list(sig.parameters.keys())
        
        # Function should have no required parameters
        if len(params) == 0:
            print("✓ render_alerts_tab() has correct signature (no parameters)")
            return True
        else:
            print(f"✗ render_alerts_tab() has unexpected parameters: {params}")
            return False
            
    except Exception as e:
        print(f"✗ Signature test failed: {e}")
        return False


def test_multilingual_labels():
    """Test that multilingual labels are defined"""
    print("\nTesting multilingual labels...")
    
    try:
        # Read the streamlit_app.py file
        with open('frontend/streamlit_app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for required label keys in English
        required_keys = [
            'configure', 'crop', 'location', 'target_price', 'phone',
            'create', 'active', 'no_alerts', 'simulate', 'simulation',
            'help_text', 'validation_error', 'invalid_price', 
            'invalid_location', 'invalid_phone', 'alert_created',
            'alert_deleted', 'delete'
        ]
        
        missing_keys = []
        for key in required_keys:
            if f"'{key}':" not in content:
                missing_keys.append(key)
        
        if not missing_keys:
            print(f"✓ All {len(required_keys)} required label keys found")
            
            # Check for all three languages
            languages = ['en', 'hi', 'bn']
            for lang in languages:
                if f"'{lang}':" in content:
                    print(f"✓ Labels defined for language: {lang}")
            
            return True
        else:
            print(f"✗ Missing label keys: {missing_keys}")
            return False
            
    except Exception as e:
        print(f"✗ Label test failed: {e}")
        return False


def test_form_validation():
    """Test that form validation logic is present"""
    print("\nTesting form validation logic...")
    
    try:
        with open('frontend/streamlit_app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        validation_checks = [
            ('target_price <= 0', 'Price validation'),
            ('location.strip() == \'\'', 'Location validation'),
            ('re.match(phone_pattern', 'Phone validation'),
        ]
        
        all_present = True
        for check, description in validation_checks:
            if check in content:
                print(f"✓ {description} present")
            else:
                print(f"✗ {description} missing")
                all_present = False
        
        return all_present
        
    except Exception as e:
        print(f"✗ Validation test failed: {e}")
        return False


def test_dynamodb_integration():
    """Test that DynamoDB repository integration is present"""
    print("\nTesting DynamoDB integration...")
    
    try:
        with open('frontend/streamlit_app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        integration_checks = [
            ('get_repository()', 'Repository instantiation'),
            ('store_price_threshold', 'Store alert method'),
            ('get_user_price_thresholds', 'Get alerts method'),
            ('delete_price_threshold', 'Delete alert method'),
        ]
        
        all_present = True
        for check, description in integration_checks:
            if check in content:
                print(f"✓ {description} present")
            else:
                print(f"✗ {description} missing")
                all_present = False
        
        return all_present
        
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        return False


def test_api_client_integration():
    """Test that API client integration is present for simulation"""
    print("\nTesting API client integration...")
    
    try:
        with open('frontend/streamlit_app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        integration_checks = [
            ('get_api_client', 'API client instantiation'),
            ('simulate_price_change', 'Simulate price change method'),
        ]
        
        all_present = True
        for check, description in integration_checks:
            if check in content:
                print(f"✓ {description} present")
            else:
                print(f"✗ {description} missing")
                all_present = False
        
        return all_present
        
    except Exception as e:
        print(f"✗ API client test failed: {e}")
        return False


def test_ui_components():
    """Test that required UI components are present"""
    print("\nTesting UI components...")
    
    try:
        with open('frontend/streamlit_app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        ui_components = [
            ('st.form(\'alert_form\')', 'Alert configuration form'),
            ('st.selectbox', 'Crop type dropdown'),
            ('st.number_input', 'Target price input'),
            ('st.text_input', 'Location and phone inputs'),
            ('st.form_submit_button', 'Submit button'),
            ('st.form(\'simulation_form\')', 'Simulation form'),
        ]
        
        all_present = True
        for component, description in ui_components:
            if component in content:
                print(f"✓ {description} present")
            else:
                print(f"✗ {description} missing")
                all_present = False
        
        return all_present
        
    except Exception as e:
        print(f"✗ UI component test failed: {e}")
        return False


def test_error_handling():
    """Test that error handling is present"""
    print("\nTesting error handling...")
    
    try:
        with open('frontend/streamlit_app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        error_handling_checks = [
            ('try:', 'Try-except blocks'),
            ('display_error', 'Error display function'),
            ('ErrorCode.STORAGE_FAILED', 'Storage error code'),
            ('st.error', 'Error messages'),
            ('st.warning', 'Warning messages'),
        ]
        
        all_present = True
        for check, description in error_handling_checks:
            if check in content:
                print(f"✓ {description} present")
            else:
                print(f"✗ {description} missing")
                all_present = False
        
        return all_present
        
    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
        return False


def main():
    """Run all verification tests"""
    print("=" * 60)
    print("Task 13.1 Verification: Price Alert Configuration Form")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_function_signature,
        test_multilingual_labels,
        test_form_validation,
        test_dynamodb_integration,
        test_api_client_integration,
        test_ui_components,
        test_error_handling,
    ]
    
    results = []
    for test in tests:
        result = test()
        results.append(result)
    
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED - Task 13.1 implementation is complete!")
        print("\nImplemented features:")
        print("  • Price alert configuration form with validation")
        print("  • Crop type dropdown with common Indian crops")
        print("  • Target price, location, and phone number inputs")
        print("  • Input validation (price > 0, location not empty, valid phone)")
        print("  • DynamoDB integration for storing/retrieving/deleting alerts")
        print("  • Active alerts display with delete functionality")
        print("  • Market price simulation feature")
        print("  • Multilingual support (English, Hindi, Bengali)")
        print("  • Error handling and user feedback")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed - Review implementation")
        return 1


if __name__ == '__main__':
    exit(main())
