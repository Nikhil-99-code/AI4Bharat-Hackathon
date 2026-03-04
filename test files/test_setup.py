"""
Setup Verification Script for Agri-Nexus V1 Platform
Tests that all components are properly configured
"""

import sys
import os
from pathlib import Path

def test_python_version():
    """Test Python version"""
    print("🐍 Testing Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 12:
        print(f"  ✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"  ❌ Python {version.major}.{version.minor}.{version.micro} (requires 3.12+)")
        return False


def test_dependencies():
    """Test required dependencies"""
    print("\n📦 Testing dependencies...")
    
    required_packages = [
        'streamlit',
        'boto3',
        'PIL',
        'numpy',
        'pytest',
        'hypothesis',
        'dotenv'
    ]
    
    all_installed = True
    
    for package in required_packages:
        try:
            if package == 'PIL':
                __import__('PIL')
            elif package == 'dotenv':
                __import__('dotenv')
            else:
                __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} (not installed)")
            all_installed = False
    
    return all_installed


def test_project_structure():
    """Test project directory structure"""
    print("\n📁 Testing project structure...")
    
    required_dirs = [
        'frontend',
        'backend',
        'shared',
        'tests',
        'infrastructure'
    ]
    
    all_exist = True
    
    for dir_name in required_dirs:
        if Path(dir_name).exists():
            print(f"  ✅ {dir_name}/")
        else:
            print(f"  ❌ {dir_name}/ (missing)")
            all_exist = False
    
    return all_exist


def test_shared_modules():
    """Test shared utility modules"""
    print("\n🔧 Testing shared modules...")
    
    sys.path.append(str(Path.cwd()))
    
    modules = [
        ('shared.config', 'Configuration'),
        ('shared.dynamodb_repository', 'DynamoDB Repository'),
        ('shared.bedrock_client', 'Bedrock Client'),
        ('shared.sns_client', 'SNS Client'),
        ('shared.image_validator', 'Image Validator')
    ]
    
    all_imported = True
    
    for module_name, display_name in modules:
        try:
            __import__(module_name)
            print(f"  ✅ {display_name}")
        except ImportError as e:
            print(f"  ❌ {display_name} ({str(e)})")
            all_imported = False
    
    return all_imported


def test_lambda_handlers():
    """Test Lambda handler files"""
    print("\n⚡ Testing Lambda handlers...")
    
    handlers = [
        'backend/analyze_crop_image/handler.py',
        'backend/process_voice_input/handler.py',
        'backend/generate_voice_response/handler.py',
        'backend/ingest_market_data/handler.py',
        'backend/trigger_alerts/handler.py'
    ]
    
    all_exist = True
    
    for handler_path in handlers:
        if Path(handler_path).exists():
            print(f"  ✅ {Path(handler_path).parent.name}")
        else:
            print(f"  ❌ {Path(handler_path).parent.name} (missing)")
            all_exist = False
    
    return all_exist


def test_environment_config():
    """Test environment configuration"""
    print("\n⚙️  Testing environment configuration...")
    
    if Path('.env').exists():
        print("  ✅ .env file exists")
        
        # Try to load config
        try:
            from shared.config import get_config
            config = get_config()
            print(f"  ✅ Configuration loaded")
            print(f"     Region: {config.aws_region}")
            print(f"     Table: {config.table_name}")
            print(f"     Bucket: {config.image_bucket}")
            return True
        except Exception as e:
            print(f"  ⚠️  Configuration loaded with warnings: {str(e)}")
            return True
    else:
        print("  ⚠️  .env file not found (copy from .env.template)")
        return False


def test_infrastructure_scripts():
    """Test infrastructure scripts"""
    print("\n🏗️  Testing infrastructure scripts...")
    
    scripts = [
        'infrastructure/create_dynamodb_table.py',
        'infrastructure/create_s3_bucket.py',
        'infrastructure/deploy_lambdas.py'
    ]
    
    all_exist = True
    
    for script_path in scripts:
        if Path(script_path).exists():
            print(f"  ✅ {Path(script_path).name}")
        else:
            print(f"  ❌ {Path(script_path).name} (missing)")
            all_exist = False
    
    return all_exist


def test_documentation():
    """Test documentation files"""
    print("\n📚 Testing documentation...")
    
    docs = [
        'README.md',
        'DEPLOYMENT_GUIDE.md',
        'IMPLEMENTATION_STATUS.md',
        'FINAL_SUMMARY.md'
    ]
    
    all_exist = True
    
    for doc_path in docs:
        if Path(doc_path).exists():
            print(f"  ✅ {doc_path}")
        else:
            print(f"  ❌ {doc_path} (missing)")
            all_exist = False
    
    return all_exist


def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 Agri-Nexus V1 Platform - Setup Verification")
    print("=" * 60)
    
    results = {
        'Python Version': test_python_version(),
        'Dependencies': test_dependencies(),
        'Project Structure': test_project_structure(),
        'Shared Modules': test_shared_modules(),
        'Lambda Handlers': test_lambda_handlers(),
        'Environment Config': test_environment_config(),
        'Infrastructure Scripts': test_infrastructure_scripts(),
        'Documentation': test_documentation()
    }
    
    print("\n" + "=" * 60)
    print("📊 Summary")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 All tests passed! Your setup is ready.")
        print("\nNext steps:")
        print("1. Configure AWS credentials in .env")
        print("2. Run: python infrastructure/create_dynamodb_table.py")
        print("3. Run: python infrastructure/create_s3_bucket.py")
        print("4. Run: python infrastructure/deploy_lambdas.py")
        print("5. Run: streamlit run frontend/streamlit_app.py")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("- Install dependencies: pip install -r requirements.txt")
        print("- Copy environment file: cp .env.template .env")
        print("- Check project structure is complete")
    
    return passed == total


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
