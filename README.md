# Agri-Nexus V1 Platform

A comprehensive agricultural application platform that empowers farmers with AI-powered crop diagnosis, voice-based assistance, and proactive market price alerts.

## Features

### 🌾 Dr. Crop
AI-powered crop disease diagnosis using computer vision and AWS Bedrock Claude 3.5 Sonnet. Upload crop images and receive instant disease identification with treatment recommendations.

### 🎤 Sahayak (Voice Assistant)
Voice-based farmer assistance with speech-to-text and text-to-speech capabilities. Ask questions in your local language and receive spoken guidance.

### 📊 Price Alerts
Configurable price alert system with SMS notifications. Set target prices for your crops and get notified when market prices reach your desired levels.

## Technology Stack

- **Frontend**: Python Streamlit
- **Backend**: AWS Lambda (Python)
- **AI/ML**: AWS Bedrock (Claude 3.5 Sonnet)
- **Database**: AWS DynamoDB (single-table design)
- **Storage**: AWS S3
- **Notifications**: AWS SNS
- **Authentication**: AWS Cognito
- **Infrastructure**: AWS CDK/CloudFormation

## Prerequisites

- Python 3.12+
- AWS Account with appropriate permissions
- AWS CLI configured
- pip (Python package manager)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd AI4Bharat-Hackathon-1
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.template .env
# Edit .env with your AWS credentials and configuration
```

## Project Structure

```
.
├── frontend/           # Streamlit application
├── backend/            # AWS Lambda functions
├── shared/             # Shared utilities and clients
├── tests/              # Unit and integration tests
├── infrastructure/     # AWS CDK/CloudFormation templates
├── requirements.txt    # Python dependencies
└── .env.template       # Environment variable template
```

## Running Locally

1. Start the Streamlit application:
```bash
streamlit run frontend/streamlit_app.py
```

2. Access the application at `http://localhost:8501`

## Deployment

Deploy the complete infrastructure using the deployment script:

```bash
python infrastructure/deploy.py
```

## Testing

Run all tests:
```bash
pytest tests/
```

Run specific test categories:
```bash
pytest tests/unit/          # Unit tests
pytest tests/property/      # Property-based tests
pytest tests/integration/   # Integration tests
```

## Multilingual Support

The application supports:
- 🇬🇧 English (en)
- 🇧🇩 Bengali (bn)
- 🇮🇳 Hindi (hi)

## License

MIT License

## Contributing

Contributions are welcome! Please read the contributing guidelines before submitting pull requests.

## Support

For issues and questions, please open an issue on GitHub.
