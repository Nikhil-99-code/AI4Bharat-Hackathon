# Quick Deployment Guide - Agri-Nexus Platform

## Option 1: Streamlit Community Cloud (Recommended - FREE & FAST)

### Prerequisites
- GitHub account
- Streamlit Community Cloud account (free at share.streamlit.io)

### Steps:

1. **Push to GitHub** (if not already done):
```bash
git init
git add .
git commit -m "Agri-Nexus Platform ready for deployment"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

2. **Deploy on Streamlit Cloud**:
   - Go to https://share.streamlit.io
   - Click "New app"
   - Select your repository
   - Set main file path: `agri_nexus_app.py`
   - Click "Deploy"

3. **Add Secrets** (in Streamlit Cloud dashboard):
   - Go to App Settings → Secrets
   - Add your `.env` contents:
```toml
AWS_ACCESS_KEY_ID = "your_access_key"
AWS_SECRET_ACCESS_KEY = "your_secret_key"
AWS_REGION = "ap-south-1"
DYNAMODB_TABLE_NAME = "agri-nexus-data"
S3_BUCKET_NAME = "agri-nexus-media-311923415823"
BEDROCK_MODEL_ID = "apac.anthropic.claude-3-5-sonnet-20241022-v2:0"
SNS_TOPIC_ARN = "your_sns_topic_arn"
VERIFIED_PHONE_NUMBER = "+918847894318"
```

4. **Done!** Your app will be live at: `https://your-app-name.streamlit.app`

---

## Option 2: AWS EC2 (Self-Hosted)

### Quick EC2 Setup:

1. **Launch EC2 Instance**:
   - AMI: Ubuntu 22.04 LTS
   - Instance Type: t2.medium (or t2.small for testing)
   - Security Group: Allow ports 22 (SSH), 8501 (Streamlit)

2. **Connect and Setup**:
```bash
# SSH into instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3-pip python3-venv -y

# Clone your repo
git clone <your-repo-url>
cd <repo-name>

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
nano .env
# (paste your environment variables)

# Run Streamlit
streamlit run agri_nexus_app.py --server.port 8501 --server.address 0.0.0.0
```

3. **Keep Running (using screen)**:
```bash
# Install screen
sudo apt install screen -y

# Start screen session
screen -S agrinexus

# Run app
streamlit run agri_nexus_app.py --server.port 8501 --server.address 0.0.0.0

# Detach: Press Ctrl+A then D
# Reattach: screen -r agrinexus
```

4. **Access**: `http://your-ec2-ip:8501`

---

## Option 3: Docker (Local or Cloud)

### Quick Docker Setup:

1. **Build and Run**:
```bash
# Build image
docker build -t agri-nexus .

# Run container
docker run -p 8501:8501 --env-file .env agri-nexus
```

2. **Access**: `http://localhost:8501`

---

## Option 4: Local Development (Immediate)

### Run Locally Right Now:

```bash
# Activate virtual environment
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Run the app
streamlit run agri_nexus_app.py
```

**Access**: `http://localhost:8501`

---

## Recommended: Streamlit Community Cloud

**Why?**
- ✅ FREE hosting
- ✅ Automatic HTTPS
- ✅ Easy updates (just push to GitHub)
- ✅ Built-in secrets management
- ✅ No server maintenance
- ✅ Fast deployment (< 5 minutes)

**Limitations:**
- Public by default (can make private with password)
- Resource limits (but sufficient for demos/hackathons)

---

## Post-Deployment Checklist

- [ ] App loads successfully
- [ ] AWS credentials work (check sidebar status)
- [ ] Dr. Crop image upload works
- [ ] Sahayak voice assistant works
- [ ] Market alerts can be set
- [ ] All tabs are accessible
- [ ] Mobile responsive design works
- [ ] PWA install prompt appears

---

## Troubleshooting

### App won't start:
- Check `requirements.txt` has all dependencies
- Verify `.env` or secrets are configured correctly
- Check logs for missing packages

### AWS services not working:
- Verify IAM permissions
- Check AWS credentials in secrets
- Ensure region is correct (ap-south-1)

### Slow loading:
- Streamlit Cloud: Normal on first load (cold start)
- EC2: Consider upgrading instance type
- Check network connectivity to AWS services

---

## Next Steps (CI/CD)

For production CI/CD, consider:
- GitHub Actions for automated testing
- AWS Amplify for hosting
- Docker + ECS/EKS for containerized deployment
- CloudFormation/Terraform for infrastructure as code
