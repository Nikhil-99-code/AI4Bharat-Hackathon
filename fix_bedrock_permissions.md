# Fix Bedrock Permissions

## Issue
Your IAM user `agri-nexus` doesn't have permission to invoke Bedrock models.

## Quick Fix (AWS Console)

### Step 1: Add Bedrock Permissions to IAM User

1. Go to **AWS Console** → **IAM** → **Users** → **agri-nexus**
2. Click **"Add permissions"** → **"Attach policies directly"**
3. Search for and select: **`AmazonBedrockFullAccess`**
4. Click **"Add permissions"**

### Step 2: Enable Model Access in Bedrock

1. Go to **AWS Console** → **Amazon Bedrock** → **Model access** (left sidebar)
2. Click **"Manage model access"** or **"Request model access"**
3. Find **"Anthropic"** section
4. Check the box for **"Claude 3.5 Sonnet"** or **"Claude 3.5 Sonnet v2"**
5. Click **"Request model access"** or **"Save changes"**
6. Wait 1-2 minutes for access to be granted (usually instant)

### Step 3: Verify Setup

Run the test again:
```bash
python test_bedrock_setup.py
```

---

## Alternative: Custom Policy (More Secure)

If you want minimal permissions instead of full access:

1. Go to **IAM** → **Users** → **agri-nexus** → **Add permissions** → **Create inline policy**
2. Switch to **JSON** tab
3. Paste this policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": [
        "arn:aws:bedrock:ap-south-1::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0",
        "arn:aws:bedrock:ap-south-1:146688728731:inference-profile/apac.anthropic.claude-3-5-sonnet-20241022-v2:0"
      ]
    }
  ]
}
```

4. Name it: `BedrockInvokeAccess`
5. Click **"Create policy"**

---

## Important Notes

- **Model access** is separate from IAM permissions - you need BOTH
- Model access is per AWS account (one-time setup)
- IAM permissions are per user/role
- Some regions may not have all models available

---

## After Fixing

Once you've added the permissions and enabled model access:

1. Wait 1-2 minutes
2. Run: `python test_bedrock_setup.py`
3. If successful, your Streamlit app will work!

---

## Troubleshooting

If still not working:

1. **Check region**: Claude 3.5 Sonnet might not be in `ap-south-1`
   - Try `us-east-1` or `us-west-2` instead
   - Update `AWS_REGION` in `.env` file

2. **Check model ID**: The exact model ID might be different
   - Go to Bedrock console → Model access
   - Copy the exact model ID shown there

3. **Wait longer**: Model access can take up to 5 minutes to activate
