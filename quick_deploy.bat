@echo off
REM Quick Deployment Script for Agri-Nexus Platform (Windows)

echo ============================================================
echo   Agri-Nexus Platform - Quick Deployment
echo ============================================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo.

REM Install/Update dependencies
echo Installing dependencies...
pip install -r requirements.txt --quiet
echo.

REM Check for .env file
if not exist ".env" (
    echo WARNING: .env file not found!
    echo Please create .env file with your AWS credentials
    echo See .env.template for reference
    echo.
    pause
)

REM Start the application
echo ============================================================
echo   Starting Agri-Nexus Platform...
echo   Access at: http://localhost:8501
echo ============================================================
echo.
echo Press Ctrl+C to stop the server
echo.

streamlit run agri_nexus_app.py

pause
