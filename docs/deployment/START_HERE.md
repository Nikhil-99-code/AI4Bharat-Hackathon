# 🌾 Agri-Nexus Platform - START HERE

## 🚀 Quick Start (Choose One)

### Option 1: Windows Quick Start (EASIEST)
```bash
# Just double-click this file:
quick_deploy.bat
```
**Done!** App opens at http://localhost:8501

---

### Option 2: Python Script (All Platforms)
```bash
python run_app.py
```
**Done!** App opens at http://localhost:8501

---

### Option 3: Manual Start
```bash
# Activate virtual environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Run app
streamlit run agri_nexus_app.py
```
**Done!** App opens at http://localhost:8501

---

### Option 4: Docker (If you have Docker)
```bash
docker-compose up
```
**Done!** App opens at http://localhost:8501

---

## 🌐 Deploy to Internet (FREE)

### Streamlit Community Cloud (Recommended)

1. **Push to GitHub**:
```bash
git init
git add .
git commit -m "Agri-Nexus Platform"
git remote add origin <your-github-url>
git push -u origin main
```

2. **Deploy**:
   - Visit: https://share.streamlit.io
   - Click "New app"
   - Select your repo
   - Main file: `agri_nexus_app.py`
   - Add secrets from `.env` file
   - Click "Deploy"

3. **Live in 5 minutes!** 🎉

---

## ✅ What You Get

- 🔬 **Dr. Crop**: AI-powered crop disease diagnosis
- 🎤 **Sahayak**: Voice assistant for farmers
- 📈 **Market Alerts**: Price tracking and notifications
- 🏛️ **Gov Schemes**: Agricultural schemes database
- 📅 **Crop Calendar**: Planting schedules
- 🌤️ **Weather**: Live weather updates
- 💰 **Price Charts**: Market price analysis
- 💬 **Community Forum**: Q&A platform
- 📱 **PWA**: Install as mobile app

---

## 📋 Prerequisites

- Python 3.8 or higher
- AWS account with credentials
- Internet connection

---

## 🔧 Configuration

Your `.env` file should have:
```env
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=ap-south-1
DYNAMODB_TABLE_NAME=agri-nexus-data
S3_BUCKET_NAME=agri-nexus-media-311923415823
BEDROCK_MODEL_ID=apac.anthropic.claude-3-5-sonnet-20241022-v2:0
VERIFIED_PHONE_NUMBER=+918847894318
```

---

## 🆘 Need Help?

### App won't start?
```bash
# Install dependencies
pip install -r requirements.txt
```

### AWS errors?
- Check `.env` file exists
- Verify AWS credentials
- Ensure IAM permissions

### Port 8501 busy?
```bash
# Windows
netstat -ano | findstr :8501
taskkill /PID <pid> /F

# Linux/Mac
lsof -ti:8501 | xargs kill -9
```

---

## 📚 Documentation

- `DEPLOYMENT_OPTIONS.md` - All deployment methods
- `QUICK_DEPLOYMENT.md` - Detailed deployment guide
- `README.md` - Full project documentation

---

## 🎯 For Hackathon Judges

**Live Demo**: [Your Streamlit Cloud URL]

**Test Credentials**: Provided in submission

**Key Features**:
1. AI-powered crop diagnosis using AWS Bedrock
2. Voice assistant with speech-to-text
3. Real-time market alerts via SMS
4. Comprehensive farmer support platform
5. Mobile-first responsive design
6. PWA for offline access

---

## 🎉 You're All Set!

Choose your preferred method above and start the app!

**Questions?** Check the documentation files or raise an issue.

**Happy Farming! 🌾**
