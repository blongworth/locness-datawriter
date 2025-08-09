#!/usr/bin/env python3
"""
Test script for LocNess Data Writer components.
"""

import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_aws_connection():
    """Test AWS DynamoDB connection."""
    print("Testing AWS DynamoDB connection...")
    
    try:
        import boto3
        from botocore.exceptions import BotoCoreError, ClientError
        
        # Check environment variables
        access_key = os.getenv('AWS_ACCESS_KEY_ID')
        secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        region = os.getenv('AWS_REGION', 'us-east-1')
        table_name = os.getenv('DYNAMODB_TABLE_NAME')
        
        if not all([access_key, secret_key, table_name]):
            print("  ✗ Missing AWS credentials or table name")
            return False
        
        # Initialize DynamoDB client
        dynamodb = boto3.resource(
            'dynamodb',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        
        table = dynamodb.Table(table_name)
        
        # Test table access (describe table)
        response = table.meta.client.describe_table(TableName=table_name)
        print(f"  ✓ Connected to table: {table_name}")
        print(f"  ✓ Table status: {response['Table']['TableStatus']}")
        print(f"  ✓ Item count: {response['Table']['ItemCount']}")
        
        # Test scan operation (limit to 1 item)
        scan_response = table.scan(Limit=1)
        items = scan_response.get('Items', [])
        print(f"  ✓ Sample scan successful, {len(items)} items returned")
        
        if items:
            print("  ✓ Sample item structure:")
            sample_item = items[0]
            for key in list(sample_item.keys())[:5]:  # Show first 5 keys
                print(f"    - {key}: {type(sample_item[key]).__name__}")
        
        return True
        
    except (BotoCoreError, ClientError) as e:
        print(f"  ✗ AWS Error: {e}")
        return False
    except Exception as e:
        print(f"  ✗ Unexpected error: {e}")
        return False


def test_google_drive_connection():
    """Test Google Drive API connection."""
    print("\nTesting Google Drive API connection...")
    
    try:
        from googleapiclient.discovery import build
        from google.oauth2.service_account import Credentials as ServiceAccountCredentials
        
        credentials_file = os.getenv('GOOGLE_CREDENTIALS_FILE')
        
        if not credentials_file:
            print("  ✗ GOOGLE_CREDENTIALS_FILE not set")
            return False
        
        if not os.path.exists(credentials_file):
            print(f"  ✗ Credentials file not found: {credentials_file}")
            return False
        
        print(f"  ✓ Credentials file found: {credentials_file}")
        
        # Determine credential type
        with open(credentials_file, 'r') as f:
            creds_data = json.load(f)
        
        SCOPES = ['https://www.googleapis.com/auth/drive.file']
        
        if creds_data.get('type') == 'service_account':
            print("  ✓ Using service account credentials")
            creds = ServiceAccountCredentials.from_service_account_file(
                credentials_file, scopes=SCOPES
            )
        else:
            print("  ✓ Using OAuth credentials (development mode)")
            # For OAuth, we'll just validate the file format
            required_fields = ['client_id', 'client_secret', 'auth_uri', 'token_uri']
            if 'installed' in creds_data:
                creds_info = creds_data['installed']
                missing_fields = [field for field in required_fields if field not in creds_info]
                if missing_fields:
                    print(f"  ✗ Missing OAuth fields: {missing_fields}")
                    return False
                print("  ✓ OAuth credentials format valid")
                return True  # Skip actual connection test for OAuth in automated testing
            else:
                print("  ✗ Invalid OAuth credentials format")
                return False
        
        # Test Drive API connection
        service = build('drive', 'v3', credentials=creds)
        
        # Test by listing a few files
        results = service.files().list(pageSize=1, fields="files(id, name)").execute()
        files = results.get('files', [])
        
        print("  ✓ Successfully connected to Google Drive API")
        print(f"  ✓ Can access files (tested with {len(files)} files)")
        
        # Test folder access if folder ID is specified
        folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
        if folder_id:
            try:
                folder = service.files().get(fileId=folder_id).execute()
                print(f"  ✓ Target folder accessible: {folder.get('name', 'Unknown')}")
            except Exception as e:
                print(f"  ✗ Cannot access target folder {folder_id}: {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"  ✗ Google Drive API error: {e}")
        return False


def test_csv_generation():
    """Test CSV generation functionality."""
    print("\nTesting CSV generation...")
    
    try:
        import pandas as pd
        
        # Sample data similar to what might come from DynamoDB
        sample_data = [
            {
                'id': '001',
                'timestamp': datetime.now().timestamp(),
                'value': 42.5,
                'status': 'active',
                'location': 'sensor_01'
            },
            {
                'id': '002',
                'timestamp': datetime.now().timestamp(),
                'value': 38.2,
                'status': 'active',
                'location': 'sensor_02'
            }
        ]
        
        # Test DataFrame creation
        df = pd.DataFrame(sample_data)
        print(f"  ✓ DataFrame created with {len(df)} rows, {len(df.columns)} columns")
        
        # Test CSV generation
        csv_content = df.to_csv(index=False)
        print(f"  ✓ CSV content generated ({len(csv_content)} characters)")
        
        # Validate CSV content
        lines = csv_content.strip().split('\n')
        if len(lines) >= 2:  # Header + at least one data row
            print(f"  ✓ CSV format valid: {len(lines)} lines (including header)")
            print(f"  ✓ Columns: {lines[0]}")
        else:
            print("  ✗ Invalid CSV format")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ✗ CSV generation error: {e}")
        return False


def test_environment_config():
    """Test environment configuration."""
    print("\nTesting environment configuration...")
    
    required_vars = [
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY',
        'DYNAMODB_TABLE_NAME',
        'GOOGLE_CREDENTIALS_FILE'
    ]
    
    optional_vars = [
        'AWS_REGION',
        'GOOGLE_DRIVE_FOLDER_ID',
        'CSV_NAME_PREFIX'
    ]
    
    all_good = True
    
    print("  Required variables:")
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"    ✓ {var}: Set")
        else:
            print(f"    ✗ {var}: Not set")
            all_good = False
    
    print("  Optional variables:")
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"    ✓ {var}: {value}")
        else:
            print(f"    - {var}: Using default")
    
    return all_good


def main():
    """Run all tests."""
    print("LocNess Data Writer - Component Tests")
    print("=" * 40)
    
    # Test results
    results = {
        'environment': test_environment_config(),
        'csv_generation': test_csv_generation(),
        'aws_connection': test_aws_connection(),
        'google_drive': test_google_drive_connection()
    }
    
    # Summary
    print("\n" + "=" * 40)
    print("TEST SUMMARY")
    print("=" * 40)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    all_passed = all(results.values())
    print(f"\nOverall Status: {'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}")
    
    if not all_passed:
        print("\nTo fix failing tests:")
        print("1. Run: uv run python setup.py")
        print("2. Edit .env file with correct values")
        print("3. Place Google credentials file in project directory")
        print("4. Verify AWS and Google Drive access")
        
        sys.exit(1)
    else:
        print("\n🎉 Your configuration is ready!")
        print("Run: uv run python main.py")


if __name__ == "__main__":
    main()
