# Railway Deployment Guide

This guide covers deploying the LocNess Data Writer to Railway.app.

## Prerequisites

1. Railway account: [Sign up at railway.app](https://railway.app)
2. Railway CLI installed: `npm install -g @railway/cli`
3. Application tested locally
4. Google credentials file ready

## Step 1: Prepare for Deployment

### 1.1 Verify Project Structure

Ensure your project has these files:
```
├── main.py              # Main application
├── pyproject.toml       # uv dependencies
├── railway.json         # Railway configuration
├── Procfile            # Process definition
├── Dockerfile          # Container definition
├── .env.example        # Environment template
└── credentials.json    # Google API credentials (not in git)
```

### 1.2 Test Locally

```bash
# Install dependencies
uv sync

# Test configuration
uv run python test_setup.py

# Run application (Ctrl+C to stop)
uv run python main.py
```

## Step 2: Railway Setup

### 2.1 Login and Initialize

```bash
# Login to Railway
railway login

# Initialize project
railway init

# Choose "Empty Project" when prompted
```

### 2.2 Configure Environment Variables

Set up all required environment variables:

```bash
# AWS Configuration
railway variables set AWS_ACCESS_KEY_ID="your_access_key"
railway variables set AWS_SECRET_ACCESS_KEY="your_secret_key"
railway variables set AWS_REGION="us-east-1"
railway variables set DYNAMODB_TABLE_NAME="your_table_name"

# Google Drive Configuration
railway variables set GOOGLE_DRIVE_FOLDER_ID="your_folder_id"
railway variables set CSV_PATH_PREFIX="data/hourly_export"
railway variables set CSV_NAME_PREFIX="locness_data"

# Railway Configuration
railway variables set PORT="8080"
```

### 2.3 Handle Google Credentials

Railway needs your Google credentials file. You have two options:

#### Option A: Base64 Encode (Recommended)

```bash
# Encode credentials file
base64 -i credentials.json | tr -d '\n' > credentials_base64.txt

# Set as environment variable
railway variables set GOOGLE_CREDENTIALS_BASE64="$(cat credentials_base64.txt)"

# Clean up
rm credentials_base64.txt
```

Then modify your application to decode it:

```python
# Add to main.py before creating GoogleDriveUploader
import base64

# Decode credentials if base64 encoded
credentials_base64 = os.getenv('GOOGLE_CREDENTIALS_BASE64')
if credentials_base64:
    credentials_json = base64.b64decode(credentials_base64).decode('utf-8')
    with open('/tmp/credentials.json', 'w') as f:
        f.write(credentials_json)
    os.environ['GOOGLE_CREDENTIALS_FILE'] = '/tmp/credentials.json'
```

#### Option B: Railway Volume (Alternative)

```bash
# Upload credentials file
railway file upload credentials.json

# Set path
railway variables set GOOGLE_CREDENTIALS_FILE="/app/credentials.json"
```

## Step 3: Deploy

### 3.1 Deploy Application

```bash
# Deploy to Railway
railway up

# Monitor deployment
railway logs
```

### 3.2 Verify Deployment

```bash
# Check application status
railway status

# View logs
railway logs --tail

# Test health endpoint (if you add one)
curl https://your-app.railway.app/health
```

## Step 4: Configure Service

### 4.1 Railway Service Settings

In the Railway dashboard:

1. Go to your project
2. Click on your service
3. Configure settings:
   - **Name**: `locness-datawriter`
   - **Environment**: `production`
   - **Build Command**: `uv sync`
   - **Start Command**: `python main.py`

### 4.2 Domain Configuration (Optional)

```bash
# Generate Railway domain
railway domain

# Or use custom domain
railway domain add yourdomain.com
```

## Step 5: Monitoring and Maintenance

### 5.1 View Logs

```bash
# Real-time logs
railway logs --tail

# Recent logs
railway logs

# Filter logs
railway logs --filter="ERROR"
```

### 5.2 Environment Management

```bash
# List variables
railway variables

# Update variable
railway variables set AWS_REGION="us-west-2"

# Delete variable
railway variables delete UNUSED_VAR
```

### 5.3 Scaling (If Needed)

In Railway dashboard:
1. Go to service settings
2. Adjust resources:
   - **Memory**: 512MB (recommended minimum)
   - **CPU**: 0.5 vCPU (recommended minimum)

## Troubleshooting

### Common Issues

#### 1. Import Errors
```
Error: ModuleNotFoundError: No module named 'boto3'
```
**Solution**: Ensure `pyproject.toml` has all dependencies and run `railway up` again.

#### 2. Google Credentials Not Found
```
Error: GOOGLE_CREDENTIALS_FILE not set
```
**Solution**: Verify credentials are uploaded and environment variable is set.

#### 3. DynamoDB Access Denied
```
Error: An error occurred (AccessDeniedException)
```
**Solution**: Check AWS credentials and IAM permissions.

#### 4. Application Exits Immediately
```
The application keeps restarting
```
**Solution**: Check logs for specific errors, verify all environment variables.

### Debug Commands

```bash
# Check environment variables
railway run env

# Connect to service shell
railway shell

# Redeploy
railway up --detach

# View build logs
railway logs --deployment
```

### Health Check Script

Add this to your `main.py` for better monitoring:

```python
import signal
import sys

def signal_handler(sig, frame):
    """Handle shutdown gracefully."""
    logger.info("Received shutdown signal, stopping application...")
    app.stop()
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
```

## Production Checklist

- [ ] All environment variables set
- [ ] Google credentials uploaded
- [ ] AWS permissions verified
- [ ] Application logs clean
- [ ] DynamoDB table accessible
- [ ] Google Drive folder accessible
- [ ] CSV files being created
- [ ] No error logs after 1 hour
- [ ] Memory usage stable
- [ ] Application survives restarts

## Cost Optimization

Railway pricing is based on usage:

1. **Hobby Plan**: $5/month (sufficient for most use cases)
2. **Pro Plan**: $20/month (for higher usage)

To minimize costs:
- Monitor resource usage in Railway dashboard
- Use efficient queries for DynamoDB
- Implement proper error handling to prevent crashes
- Consider batching operations

## Support

- Railway Documentation: [docs.railway.app](https://docs.railway.app)
- Railway Discord: [discord.gg/railway](https://discord.gg/railway)
- Application logs: `railway logs`
- Health check: `uv run python health.py`
