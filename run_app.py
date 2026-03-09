#!/usr/bin/env python3
"""
Quick launcher for Agri-Nexus Platform
Checks dependencies and starts the Streamlit app
"""

import sys
import subprocess
import os
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        sys.exit(1)
    print(f"✅ Python version: {sys.version_info.major}.{sys.version_info.minor}")

def check_env_file():
    """Check if .env file exists"""
    if not Path(".env").exists():
        print("⚠️  Warning: .env file not found")
        print("   Create .env file with your AWS credentials")
        print("   See .env.template for reference")
        return False
    print("✅ .env file found")
    return True

def check_dependencies():
    """Check if required packages are installed"""
    try:
        import streamlit
        import boto3
        import PIL
        print("✅ Core dependencies installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e.name}")
        print("   Run: pip install -r requirements.txt")
        return False

def check_aws_credentials():
    """Check if AWS credentials are configured"""
    from dotenv import load_dotenv
    load_dotenv()
    
    if not os.getenv('AWS_ACCESS_KEY_ID'):
        print("⚠️  Warning: AWS_ACCESS_KEY_ID not set")
        return False
    if not os.getenv('AWS_SECRET_ACCESS_KEY'):
        print("⚠️  Warning: AWS_SECRET_ACCESS_KEY not set")
        return False
    
    print("✅ AWS credentials configured")
    return True

def start_app():
    """Start the Streamlit app"""
    print("\n" + "="*60)
    print("🚀 Starting Agri-Nexus Platform...")
    print("="*60 + "\n")
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "agri_nexus_app.py",
            "--server.port=8501",
            "--server.headless=false"
        ])
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down Agri-Nexus Platform...")
        sys.exit(0)

def main():
    """Main function"""
    print("\n" + "="*60)
    print("🌾 Agri-Nexus Platform - Quick Launcher")
    print("="*60 + "\n")
    
    # Run checks
    check_python_version()
    env_ok = check_env_file()
    deps_ok = check_dependencies()
    
    if not deps_ok:
        print("\n❌ Please install dependencies first:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
    
    if env_ok:
        check_aws_credentials()
    
    # Start app
    print("\n" + "="*60)
    print("✅ All checks passed!")
    print("="*60)
    
    start_app()

if __name__ == "__main__":
    main()
