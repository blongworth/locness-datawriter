import os
import time
import logging
import schedule
from datetime import datetime, timezone, timedelta
from io import BytesIO
from typing import Dict, List, Any, Optional

import boto3
import pandas as pd
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from botocore.exceptions import BotoCoreError, ClientError

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Google Drive API scopes
SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/drive.file']


class DynamoDBDataReader:
    """Handles reading data from AWS DynamoDB."""
    
    def __init__(self):
        self.table_name = os.getenv('DYNAMODB_TABLE_NAME')
        if not self.table_name:
            raise ValueError("DYNAMODB_TABLE_NAME environment variable is required")
        
        # Initialize DynamoDB client
        self.dynamodb = boto3.resource(
            'dynamodb',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        self.table = self.dynamodb.Table(self.table_name)
        self.last_read_timestamp = None
    
    def get_new_data(self) -> List[Dict[str, Any]]:
        """Fetch new data from DynamoDB since last read."""
        try:
            # If this is the first read, get data from the last hour
            if self.last_read_timestamp is None:
                # Set to 1 hour ago in ISO format
                one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
                self.last_read_timestamp = one_hour_ago.strftime('%Y-%m-%dT%H:%M:%SZ')
            
            current_time = datetime.now(timezone.utc)
            current_timestamp = current_time.strftime('%Y-%m-%dT%H:%M:%SZ')
            
            logger.info(f"Searching for data between {self.last_read_timestamp} and {current_timestamp}")
            
            # Scan for items with timestamp greater than last read
            # Using string comparison for ISO datetime strings
            response = self.table.scan(
                FilterExpression='#ts > :last_ts AND #ts <= :current_ts',
                ExpressionAttributeNames={
                    '#ts': 'datetime_utc'  # Your timestamp attribute name
                },
                ExpressionAttributeValues={
                    ':last_ts': self.last_read_timestamp,
                    ':current_ts': current_timestamp
                }
            )
            
            items = response.get('Items', [])
            
            # Handle pagination if needed
            while 'LastEvaluatedKey' in response:
                response = self.table.scan(
                    FilterExpression='#ts > :last_ts AND #ts <= :current_ts',
                    ExpressionAttributeNames={'#ts': 'datetime_utc'},
                    ExpressionAttributeValues={
                        ':last_ts': self.last_read_timestamp,
                        ':current_ts': current_timestamp
                    },
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
                items.extend(response.get('Items', []))
            
            # Update last read timestamp to current time
            self.last_read_timestamp = current_timestamp
            logger.info(f"Retrieved {len(items)} new items from DynamoDB")
            
            if items:
                # Log a sample of the timestamps found
                sample_timestamps = [item.get('datetime_utc', 'N/A') for item in items[:3]]
                logger.info(f"Sample timestamps found: {sample_timestamps}")
            
            return items
            
        except (BotoCoreError, ClientError) as e:
            logger.error(f"Error reading from DynamoDB: {e}")
            return []


class GoogleDriveUploader:
    """Handles uploading CSV files to Google Drive."""
    
    def __init__(self):
        self.folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
        self.shared_drive_id = os.getenv('GOOGLE_SHARED_DRIVE_ID')  # Add support for shared drives
        self.credentials_file = os.getenv('GOOGLE_CREDENTIALS_FILE')
        
        if not self.credentials_file:
            raise ValueError("GOOGLE_CREDENTIALS_FILE environment variable is required")
        
        self.service = self._get_drive_service()
        self.file_cache = {}  # Cache file IDs by filename
        
        # Verify shared drive access if specified
        if self.shared_drive_id:
            self._verify_shared_drive_access()
    
    def _get_drive_service(self):
        """Authenticate and return Google Drive service."""
        import json
        
        # Check if it's a service account credentials file
        try:
            with open(self.credentials_file, 'r') as f:
                creds_data = json.load(f)
            
            if creds_data.get('type') == 'service_account':
                # Use service account authentication
                logger.info("Using service account credentials for Google Drive")
                creds = ServiceAccountCredentials.from_service_account_file(
                    self.credentials_file, 
                    scopes=SCOPES
                )
                return build('drive', 'v3', credentials=creds)
            
        except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
            logger.warning(f"Could not parse credentials as service account: {e}")
        
        # Fall back to OAuth flow for installed app credentials
        logger.info("Using OAuth credentials for Google Drive")
        creds = None
        token_file = 'token.json'
        
        # Load existing credentials
        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)
        
        # If no valid credentials, authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(token_file, 'w') as token:
                token.write(creds.to_json())
        
        return build('drive', 'v3', credentials=creds)
    
    def _verify_shared_drive_access(self):
        """Verify that we can access the specified shared drive."""
        try:
            # Try to get information about the shared drive
            drive_info = self.service.drives().get(
                driveId=self.shared_drive_id,
                fields='id,name'
            ).execute()
            
            logger.info(f"Successfully verified access to shared drive: {drive_info.get('name', 'Unknown')} (ID: {self.shared_drive_id})")
            
        except Exception as e:
            logger.error(f"Cannot access shared drive {self.shared_drive_id}: {e}")
            logger.error("Make sure the service account has been added to the shared drive with appropriate permissions")
            raise ValueError(f"Cannot access shared drive: {e}")
    
    def _find_existing_file(self, filename: str) -> Optional[str]:
        """Find existing file by name in the target folder."""
        try:
            # Check cache first
            if filename in self.file_cache:
                return self.file_cache[filename]
            
            # Build query
            query = f"name='{filename}' and trashed=false"
            if self.folder_id:
                query += f" and '{self.folder_id}' in parents"
            
            # Search parameters
            search_params = {
                'q': query,
                'fields': "files(id, name)"
            }
            
            # Add shared drive support
            if self.shared_drive_id:
                search_params['driveId'] = self.shared_drive_id
                search_params['corpora'] = 'drive'
                search_params['includeItemsFromAllDrives'] = True
                search_params['supportsAllDrives'] = True
            
            # Search for the file
            results = self.service.files().list(**search_params).execute()
            
            files = results.get('files', [])
            if files:
                file_id = files[0]['id']
                self.file_cache[filename] = file_id
                return file_id
            
            return None
            
        except Exception as e:
            logger.error(f"Error searching for existing file {filename}: {e}")
            return None
    
    def upload_or_update_csv(self, csv_content: str, filename: str) -> Optional[str]:
        """Upload new CSV or update existing one."""
        try:
            # Check if file already exists
            existing_file_id = self._find_existing_file(filename)
            
            # Create media upload object with proper encoding
            csv_bytes = csv_content.encode('utf-8')
            media = MediaIoBaseUpload(
                BytesIO(csv_bytes),
                mimetype='text/csv',
                resumable=True
            )
            
            if existing_file_id:
                # Update existing file
                update_params = {
                    'fileId': existing_file_id,
                    'media_body': media,
                    'fields': 'id'
                }
                
                # Add shared drive support
                if self.shared_drive_id:
                    update_params['supportsAllDrives'] = True
                
                file = self.service.files().update(**update_params).execute()
                
                file_id = file.get('id')
                logger.info(f"Successfully updated {filename} on Google Drive (ID: {file_id})")
                return file_id
            else:
                # Create new file
                file_metadata = {
                    'name': filename,
                    'mimeType': 'text/csv'
                }
                
                # Handle folder specification for shared drives vs regular drives
                if self.shared_drive_id and self.folder_id:
                    # File in a specific folder within a shared drive
                    file_metadata['parents'] = [self.folder_id]
                elif self.folder_id and not self.shared_drive_id:
                    # File in a regular Drive folder
                    file_metadata['parents'] = [self.folder_id]
                # If shared_drive_id but no folder_id, file goes to shared drive root (no parents needed)
                
                # Create parameters
                create_params = {
                    'body': file_metadata,
                    'media_body': media,
                    'fields': 'id'
                }
                
                # Add shared drive support
                if self.shared_drive_id:
                    create_params['supportsAllDrives'] = True
                
                # Upload file
                file = self.service.files().create(**create_params).execute()
                
                file_id = file.get('id')
                # Cache the new file ID
                self.file_cache[filename] = file_id
                logger.info(f"Successfully uploaded new {filename} to Google Drive (ID: {file_id})")
                return file_id
            
        except Exception as e:
            logger.error(f"Error uploading/updating Google Drive file {filename}: {e}")
            return None
    
    def upload_csv(self, csv_content: str, filename: str) -> Optional[str]:
        """Legacy method - redirects to upload_or_update_csv."""
        return self.upload_or_update_csv(csv_content, filename)


class CSVDataWriter:
    """Handles CSV data formatting and management."""
    
    def __init__(self):
        self.path_prefix = os.getenv('CSV_PATH_PREFIX', 'data/hourly_export')
        self.name_prefix = os.getenv('CSV_NAME_PREFIX', 'locness_data')
        self.current_hour_data = []
        self.current_hour = None
    
    def add_data(self, data: List[Dict[str, Any]]):
        """Add new data to the current hour's collection."""
        if not data:
            return
        
        current_hour = datetime.now().strftime('%Y%m%d_%H')
        
        # Start new hour if needed
        if self.current_hour != current_hour:
            # Clear data for new hour (don't process previous hour here)
            self.current_hour = current_hour
            self.current_hour_data = []
        
        self.current_hour_data.extend(data)
        logger.info(f"Added {len(data)} items to current hour data. Total: {len(self.current_hour_data)}")
    
    def _write_hour_data(self) -> Optional[str]:
        """Write accumulated hour data to CSV and return the CSV content."""
        if not self.current_hour_data:
            return None
        
        try:
            # Convert to DataFrame for easier CSV handling
            df = pd.DataFrame(self.current_hour_data)
            
            # Generate CSV content
            csv_content = df.to_csv(index=False)
            
            logger.info(f"Generated CSV with {len(self.current_hour_data)} records for hour {self.current_hour}")
            return csv_content
            
        except Exception as e:
            logger.error(f"Error generating CSV: {e}")
            return None
    
    def get_current_filename(self) -> str:
        """Generate filename for current hour."""
        if self.current_hour:
            return f"{self.name_prefix}_{self.current_hour}.csv"
        return f"{self.name_prefix}_{datetime.now().strftime('%Y%m%d_%H')}.csv"
    
    def get_current_csv_content(self) -> Optional[str]:
        """Get current hour's CSV content without clearing data."""
        return self._write_hour_data()
    
    def force_write_current_data(self) -> Optional[str]:
        """Force write current hour data (useful for shutdown)."""
        return self._write_hour_data()


class DataWriterApp:
    """Main application class that orchestrates the data flow."""
    
    def __init__(self):
        self.db_reader = DynamoDBDataReader()
        self.drive_uploader = GoogleDriveUploader()
        self.csv_writer = CSVDataWriter()
        self.is_running = False
    
    def read_and_write_data(self):
        """Read new data from DynamoDB and update the current hourly CSV file."""
        logger.info("Reading new data from DynamoDB...")
        new_data = self.db_reader.get_new_data()
        
        if new_data:
            self.csv_writer.add_data(new_data)
            
            # Generate current CSV content and upload/update the file
            csv_content = self.csv_writer.get_current_csv_content()
            if csv_content:
                filename = self.csv_writer.get_current_filename()
                self.drive_uploader.upload_or_update_csv(csv_content, filename)
        else:
            logger.info("No new data found")
    
    def upload_hourly_csv(self):
        """Ensure the current hourly CSV is uploaded (called at hour boundaries)."""
        logger.info("Hour boundary reached - ensuring current CSV is uploaded...")
        csv_content = self.csv_writer.get_current_csv_content()
        
        if csv_content:
            filename = self.csv_writer.get_current_filename()
            self.drive_uploader.upload_or_update_csv(csv_content, filename)
        else:
            logger.info("No data for current hour to upload")
    
    def start(self):
        """Start the scheduled data reading and writing."""
        logger.info("Starting LocNess Data Writer...")
        
        # Schedule data reading every minute
        schedule.every().minute.do(self.read_and_write_data)
        
        # Schedule CSV upload at the start of each hour
        schedule.every().hour.at(":00").do(self.upload_hourly_csv)
        
        self.is_running = True
        
        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received shutdown signal...")
            self.stop()
    
    def stop(self):
        """Stop the application and upload any remaining data."""
        logger.info("Stopping LocNess Data Writer...")
        self.is_running = False
        
        # Upload any remaining data
        csv_content = self.csv_writer.get_current_csv_content()
        if csv_content:
            filename = self.csv_writer.get_current_filename()
            self.drive_uploader.upload_or_update_csv(csv_content, filename)
        
        logger.info("Application stopped")


def main():
    """Main entry point."""
    try:
        app = DataWriterApp()
        app.start()
    except Exception as e:
        logger.error(f"Application error: {e}")
        raise


if __name__ == "__main__":
    main()
