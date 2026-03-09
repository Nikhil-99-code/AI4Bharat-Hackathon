# 🚀 Agri-Nexus Platform - Deployment Options

## ⚡ FASTEST: Run Locally (30 seconds)

### Windows:
```bash
# Double-click or run:
quick_deploy.bat
```

### Linux/Mac:
```bash
# Make executable
chmod +x run_app.py

# Run
python run_app.py
```

**Access**: http://localhost:8501

---

## 🌐 RECOMMENDED: Streamlit Community Cloud (5 minutes)

### Why Streamlit Cloud?
- ✅ **FREE** hosting forever
- ✅ **HTTPS** included
- ✅ **Auto-deploy** on git push
- ✅ **No server** management
- ✅ **Perfect** for hackathons/demos

### Steps:

1. **Push to GitHub**:
```bash
git init
git add .
git commit -m "Deploy Agri-Nexus"
git remote add origin https://github.com/yourusername/agri-nexus.git
git push -u origin main
```

2. **Deploy**:
   - Go to https://share.streamlit.io
   - Click "New app"
   - Select your repo
   - Main file: `agri_nexus_app.py`
   - Click "Deploy"

3. **Add Secrets** (App Settings → Secrets):
```toml
AWS_ACCESS_KEY_ID = "your_key"
AWS_SECRET_ACCESS_KEY = "your_secret"
AWS_REGION = "ap-south-1"
DYNAMODB_TABLE_NAME = "agri-nexus-data"
S3_BUCKET_NAME = "agri-nexus-media-311923415823"
BEDROCK_MODEL_ID = "apac.anthropic.claude-3-5-sonnet-20241022-v2:0"
VERIFIED_PHONE_NUMBER = "+918847894318"
```

4. **Done!** App live at: `https://your-app.streamlit.app`

---

## 🐳 Docker Deployment (2 minutes)

### Build and Run:
```bash
# Build image
docker build -t agri-nexus .

# Run with .env file
docker run -p 8501:8501 --env-file .env agri-nexus
```

**Access**: http://localhost:8501

### Docker Compose (even easier):
```bash
docker-compose up
```

---

## ☁️ AWS EC2 Deployment (10 minutes)

### Quick Setup:

1. **Launch EC2**:
   - Ubuntu 22.04 LTS
   - t2.medium
   - Security: Allow 22, 8501

2. **Setup Script**:
```bash
# SSH into instance
ssh -i key.pem ubuntu@your-ec2-ip

# Run setup
curl -sSL https://raw.githubusercontent.com/yourusername/agri-nexus/main/setup_ec2.sh | bash
```

3. **Access**: `http://your-ec2-ip:8501`

---

## 📊 Comparison Table

| Method | Time | Cost | Difficulty | Best For |
|--------|------|------|------------|----------|
| **Local** | 30s | Free | ⭐ Easy | Development |
| **Streamlit Cloud** | 5m | Free | ⭐⭐ Easy | Demos/Hackathons |
| **Docker** | 2m | Free | ⭐⭐ Medium | Testing |
| **EC2** | 10m | ~$10/mo | ⭐⭐⭐ Medium | Production |
| **ECS/EKS** | 30m | ~$30/mo | ⭐⭐⭐⭐ Hard | Enterprise |

---

## 🎯 Quick Decision Guide

**Choose Streamlit Cloud if:**
- You want FREE hosting
- You need it live in 5 minutes
- It's for a hackathon/demo
- You want automatic updates

**Choose Local if:**
- You're still developing
- You want to test quickly
- You don't need public access

**Choose Docker if:**
- You want consistent environments
- You're deploying to cloud later
- You need easy scaling

**Choose EC2 if:**
- You need full control
- You have custom requirements
- You want a dedicated server

---

## 🔥 RECOMMENDED FOR HACKATHON

**Use Streamlit Community Cloud!**

Reasons:
1. ✅ Free forever
2. ✅ Live in 5 minutes
3. ✅ HTTPS included
4. ✅ Easy to share URL
5. ✅ No maintenance needed
6. ✅ Judges can access easily
7. ✅ Auto-updates on git push

---

## 📝 Post-Deployment Checklist

After deployment, verify:

- [ ] App loads successfully
- [ ] Header shows "Agri-Nexus Platform"
- [ ] Sidebar shows system info
- [ ] All 9 tabs are accessible
- [ ] Dr. Crop image upload works
- [ ] Weather widget shows data
- [ ] Status indicators are green
- [ ] Mobile responsive works
- [ ] PWA install prompt appears

---

## 🆘 Troubleshooting

### App won't start:
```bash
# Check Python version
python --version  # Should be 3.8+

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### AWS errors:
- Check `.env` file exists
- Verify AWS credentials are correct
- Ensure IAM permissions are set
- Check region is `ap-south-1`

### Port already in use:
```bash
# Windows
netstat -ano | findstr :8501
taskkill /PID <pid> /F

# Linux/Mac
lsof -ti:8501 | xargs kill -9
```

---

## 🎉 You're Ready!

Choose your deployment method and get your app live!

For hackathon: **Use Streamlit Cloud** → 5 minutes to live! 🚀
