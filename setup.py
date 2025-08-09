#!/usr/bin/env python3
"""
Setup script for LocNess Data Writer.
This script helps configure the application for first-time use.
"""

import os
import json
from pathlib import Path


def create_env_file():
    """Create a .env file from the example template."""
    env_example = Path('.env.example')
    env_file = Path('.env')
    
    if env_file.exists():
        print("✓ .env file already exists")
        return
    
    if env_example.exists():
        # Copy the example to .env
        with open(env_example, 'r') as f:
            content = f.read()
        
        with open(env_file, 'w') as f:
            f.write(content)
        
        print("✓ Created .env file from template")
        print("  → Please edit .env file with your actual configuration values")
    else:
        print("✗ .env.example file not found")


def check_google_credentials():
    """Check if Google credentials file exists."""
    creds_file = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
    
    if os.path.exists(creds_file):
        print(f"✓ Google credentials file found: {creds_file}")
        
        # Validate JSON format
        try:
            with open(creds_file, 'r') as f:
                creds = json.load(f)
            
            if 'type' in creds:
                if creds['type'] == 'service_account':
                    print("  → Service account credentials detected")
                else:
                    print("  → OAuth client credentials detected")
            else:
                print("  → Credentials file format validation needed")
                
        except json.JSONDecodeError:
            print(f"  ✗ Invalid JSON format in {creds_file}")
    else:
        print(f"✗ Google credentials file not found: {creds_file}")
        print("  → Download from Google Cloud Console")


def check_aws_config():
    """Check AWS configuration."""
    access_key = os.getenv('AWS_ACCESS_KEY_ID')
    secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    region = os.getenv('AWS_REGION', 'us-east-1')
    table_name = os.getenv('DYNAMODB_TABLE_NAME')
    
    print("\nAWS Configuration:")
    print(f"  Access Key ID: {'Set' if access_key else 'Not set'}")
    print(f"  Secret Access Key: {'Set' if secret_key else 'Not set'}")
    print(f"  Region: {region}")
    print(f"  DynamoDB Table: {table_name or 'Not set'}")


def check_csv_config():
    """Check CSV configuration."""
    path_prefix = os.getenv('CSV_PATH_PREFIX', 'data/hourly_export')
    name_prefix = os.getenv('CSV_NAME_PREFIX', 'locness_data')
    folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
    
    print("\nCSV Configuration:")
    print(f"  Path Prefix: {path_prefix}")
    print(f"  Name Prefix: {name_prefix}")
    print(f"  Google Drive Folder ID: {folder_id or 'Not set (will use root folder)'}")


def setup_google_drive():
    """Guide user through Google Drive setup."""
    print("\n" + "="*50)
    print("GOOGLE DRIVE SETUP GUIDE")
    print("="*50)
    
    print("\n1. Go to Google Cloud Console (https://console.cloud.google.com/)")
    print("2. Create a new project or select existing one")
    print("3. Enable Google Drive API")
    print("\nFor Service Account (Recommended for production):")
    print("4a. Go to IAM & Admin > Service Accounts")
    print("4b. Create a new service account")
    print("4c. Download the JSON key file")
    print("4d. Share your Google Drive folder with the service account email")
    
    print("\nFor OAuth (Development):")
    print("4a. Go to APIs & Services > Credentials")
    print("4b. Create OAuth 2.0 Client ID")
    print("4c. Download client_secret.json file")
    
    print("\n5. Place the JSON file in this directory")
    print("6. Update GOOGLE_CREDENTIALS_FILE in .env")


def setup_aws():
    """Guide user through AWS setup."""
    print("\n" + "="*50)
    print("AWS DYNAMODB SETUP GUIDE")
    print("="*50)
    
    print("\n1. Create IAM user with DynamoDB access")
    print("2. Generate Access Key ID and Secret Access Key")
    print("3. Create DynamoDB table with timestamp attribute")
    print("4. Update AWS_* variables in .env file")
    
    print("\nRequired DynamoDB permissions:")
    print("  - dynamodb:Scan")
    print("  - dynamodb:Query (optional)")


def main():
    """Main setup function."""
    print("LocNess Data Writer Setup")
    print("=" * 25)
    
    # Load environment variables if .env exists
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("Warning: python-dotenv not installed")
    
    # Step 1: Create .env file
    print("\n1. Environment Configuration")
    create_env_file()
    
    # Step 2: Check Google credentials
    print("\n2. Google Drive Configuration")
    check_google_credentials()
    
    # Step 3: Check AWS configuration
    check_aws_config()
    
    # Step 4: Check CSV configuration
    check_csv_config()
    
    # Step 5: Setup guides
    setup_google_drive()
    setup_aws()
    
    print("\n" + "="*50)
    print("NEXT STEPS")
    print("="*50)
    print("1. Edit .env file with your actual values")
    print("2. Place Google credentials JSON file in project directory")
    print("3. Test configuration: uv run python health.py")
    print("4. Run application: uv run python main.py")
    print("5. Deploy to Railway: railway up")


if __name__ == "__main__":
    main()
