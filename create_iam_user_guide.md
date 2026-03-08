# Quick IAM User Setup Guide

## Step 1: Create IAM User (AWS Console)

1. Go to AWS Console → IAM → Users → "Create user"
2. Username: `agri-nexus-deployer` (or any name you prefer)
3. Check "Provide user access to the AWS Management Console" - OPTIONAL
4. Click "Next"

## Step 2: Attach Permissions

Choose "Attach policies directly" and select these managed policies:

### Required Policies:
- ✅ `AmazonDynamoDBFullAccess` - For DynamoDB tables
- ✅ `AmazonS3FullAccess` - For S3 buckets
- ✅ `AWSLambda_FullAccess` - For Lambda functions
- ✅ `AmazonAPIGatewayAdministrator` - For API Gateway
- ✅ `AmazonSNSFullAccess` - For SMS notifications
- ✅ `IAMFullAccess` - For creating Lambda execution roles
- ✅ `CloudWatchLogsFullAccess` - For Lambda logs

### Alternative (More Secure - Custom Policy):
If you want minimal permissions, create a custom policy with:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:*",
        "s3:*",
        "lambda:*",
        "apigateway:*",
        "sns:*",
        "iam:CreateRole",
        "iam:AttachRolePolicy",
        "iam:PassRole",
        "iam:GetRole",
        "logs:*"
      ],
      "Resource": "*"
    }
  ]
}
```

## Step 3: Create Access Keys

1. After creating user, click on the username
2. Go to "Security credentials" tab
3. Scroll to "Access keys" section
4. Click "Create access key"
5. Choose "Command Line Interface (CLI)" or "Application running outside AWS"
6. Check the confirmation box
7. Click "Create access key"
8. **IMPORTANT**: Copy both:
   - Access key ID (starts with AKIA...)
   - Secret access key (shown only once!)

## Step 4: Update .env File

Replace the credentials in your `.env` file:

```env
AWS_ACCESS_KEY_ID=<your-new-access-key-id>
AWS_SECRET_ACCESS_KEY=<your-new-secret-access-key>
```

## Step 5: Delete Old Credentials

**CRITICAL SECURITY STEP:**

1. Go to IAM → Users → Find the old user with key `AKIAURIAVTMHSRER6OAN`
2. Go to "Security credentials" tab
3. Find the access key and click "Actions" → "Delete"
4. Confirm deletion

## Quick Checklist

- [ ] Created new IAM user
- [ ] Attached required policies (7 policies listed above)
- [ ] Created access keys
- [ ] Copied Access Key ID and Secret Access Key
- [ ] Updated `.env` file with new credentials
- [ ] Deleted old exposed credentials

## Next Steps After IAM Setup

Once your `.env` is updated with new credentials:

```bash
# 1. Create S3 bucket (30 seconds)
python infrastructure/create_s3_bucket.py

# 2. Deploy Lambda functions (15 minutes)
python infrastructure/deploy_lambdas.py

# 3. Create API Gateway (5 minutes)
python deploy_api_gateway.py

# 4. Update .env with API Gateway URL (from step 3 output)

# 5. Run Streamlit demo
streamlit run frontend/streamlit_app.py
```

## Time Estimate
- IAM user creation: 3-5 minutes
- Remaining deployment: 20-25 minutes
- **Total: ~30 minutes** (well within your 1-hour deadline!)
