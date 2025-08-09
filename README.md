# LocNess Data Writer

A Python application that reads new data from AWS DynamoDB every minute and writes it to CSV files on Google Shared Drive. The app creates a new CSV file every hour with configurable path and name prefixes.

## Features

- ⏰ Reads from DynamoDB every minute
- 📊 Updates the current hourly CSV file each minute
- 🔄 Replaces the file on Google Drive with updated data
- 🕐 Creates a new CSV file every hour
- ☁️ Uploads to Google Drive automatically
- 🚀 Configured for Railway deployment
- 📦 Uses `uv` for fast dependency management

## Prerequisites

1. **AWS DynamoDB**: Table with a `timestamp` attribute (configurable)
2. **Google Drive API**: Service account or OAuth credentials
3. **Python 3.13+**
4. **uv** package manager

## Setup

### 1. Install uv (if not already installed)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone and setup the project

```bash
git clone <your-repo>
cd locness-datawriter
uv sync
```

### 3. Configure environment variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# AWS Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_REGION=us-east-1
DYNAMODB_TABLE_NAME=your_table_name

# Google Drive Configuration
GOOGLE_CREDENTIALS_FILE=path/to/your/credentials.json
GOOGLE_DRIVE_FOLDER_ID=your_google_drive_folder_id

# CSV Configuration
CSV_NAME_PREFIX=locness_data

# Railway Configuration (optional)
PORT=8080
```

### 4. Google Drive Setup

#### Option A: Service Account (Recommended for production)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google Drive API
4. Create a Service Account
5. Download the JSON credentials file
6. Share your Google Drive folder with the service account email

#### Option B: OAuth (For development)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create OAuth 2.0 credentials
3. Download the client secrets JSON file
4. Set `GOOGLE_CREDENTIALS_FILE` to the path of this file

### 5. AWS DynamoDB Setup

Ensure your DynamoDB table has a `datetime_utc` attribute. If your timestamp attribute has a different name, update the code in `DynamoDBDataReader.get_new_data()` method.

## Usage

### Local Development

```bash
# Run with uv
uv run python main.py

# Or activate the virtual environment
source .venv/bin/activate
python main.py
```

### File Naming Convention

CSV files are named using the pattern:
```
{CSV_NAME_PREFIX}_{YYYYMMDD_HH}.csv
```

Example: `locness_data_20250809_14.csv`

### Behavior

1. **Every minute**: The app reads new data from DynamoDB and updates the current hour's CSV file on Google Drive
2. **File replacement**: If data exists for the current hour, the existing file is replaced with updated content
3. **New hourly files**: At the start of each hour, a new CSV file is created
4. **Continuous updates**: Each minute's new data is appended to the current hour's dataset and the file is updated

## Railway Deployment

### 1. Install Railway CLI

```bash
npm install -g @railway/cli
```

### 2. Login and deploy

```bash
railway login
railway init
railway up
```

### 3. Set environment variables

```bash
railway variables set AWS_ACCESS_KEY_ID=your_value
railway variables set AWS_SECRET_ACCESS_KEY=your_value
railway variables set AWS_REGION=us-east-1
railway variables set DYNAMODB_TABLE_NAME=your_table
railway variables set GOOGLE_DRIVE_FOLDER_ID=your_folder_id
railway variables set CSV_NAME_PREFIX=locness_data
```

### 4. Upload Google credentials

For Railway deployment, you'll need to upload your Google credentials file and set the path:

```bash
# Upload the file through Railway dashboard or CLI
railway variables set GOOGLE_CREDENTIALS_FILE=/app/credentials.json
```

## Configuration

### Environment Variables

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `AWS_ACCESS_KEY_ID` | Yes | AWS access key | - |
| `AWS_SECRET_ACCESS_KEY` | Yes | AWS secret key | - |
| `AWS_REGION` | No | AWS region | `us-east-1` |
| `DYNAMODB_TABLE_NAME` | Yes | DynamoDB table name | - |
| `GOOGLE_CREDENTIALS_FILE` | Yes | Path to Google credentials JSON | - |
| `GOOGLE_DRIVE_FOLDER_ID` | No | Google Drive folder ID | Root folder |
| `CSV_NAME_PREFIX` | No | CSV file name prefix | `locness_data` |
| `PORT` | No | Port for Railway | `8080` |

### Customizing DynamoDB Schema

If your DynamoDB table uses a different attribute name for timestamps, update the `DynamoDBDataReader.get_new_data()` method:

```python
# Change 'datetime_utc' to your attribute name
ExpressionAttributeNames={
    '#ts': 'your_timestamp_field'
},
```

## Architecture

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│  DynamoDB   │───▶│   Python     │───▶│ Google      │
│   Table     │    │   App        │    │ Drive       │
└─────────────┘    └──────────────┘    └─────────────┘
     ▲                     │                   │
     │              Every minute          Every minute
     │              (read data)       (update CSV file)
     │                     │                   │
     └─────────────────────┼───────────────────┘
                          │
                    ┌──────────────┐
                    │   Railway    │
                    │  (hosting)   │
                    └──────────────┘
```

## Logging

The application logs to both console and `app.log` file. Logs include:
- Data reading from DynamoDB
- CSV file generation
- Google Drive uploads
- Error handling

## Error Handling

- DynamoDB connection errors are logged and the app continues
- Google Drive upload failures are logged
- The app gracefully handles shutdown signals

## Development

### Adding new features

1. Fork the repository
2. Create a feature branch
3. Make changes
4. Test locally
5. Submit a pull request

### Testing

```bash
# Run with debug logging
export LOG_LEVEL=DEBUG
uv run python main.py
```

## License

MIT License - see LICENSE file for details.