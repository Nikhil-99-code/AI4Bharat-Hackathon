# Agri-Nexus Python Lambda Functions

Python-based serverless Lambda functions for easy AWS deployment.

## Structure

```
lambda_python/
├── lib/                    # Shared libraries
│   ├── bedrock_client.py   # Amazon Bedrock integration
│   ├── dynamodb_repository.py  # DynamoDB operations
│   └── prompt_templates.py # Multilingual prompts
├── dr_crop/                # Crop diagnosis service
├── market_agent/           # Market intelligence service
├── voice_interface/        # Voice processing service
├── market_data/            # Market data ingestion
└── requirements.txt        # Python dependencies

## Installation

```bash
pip install -r requirements.txt
```

## Deployment

Each function can be deployed independently to AWS Lambda with:
- Runtime: Python 3.11
- Handler: {module}.handler
- Environment variables: TABLE_NAME, IMAGE_BUCKET, AWS_REGION

## Testing

```bash
pytest
```
