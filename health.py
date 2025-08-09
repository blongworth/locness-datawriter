"""
Health check and utility functions for the LocNess Data Writer application.
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)


def health_check() -> Dict[str, Any]:
    """
    Perform a basic health check of the application.
    
    Returns:
        Dict containing health status information
    """
    status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "0.1.0",
        "environment": {
            "python_version": os.sys.version,
            "aws_region": os.getenv('AWS_REGION', 'not_set'),
            "dynamodb_table": os.getenv('DYNAMODB_TABLE_NAME', 'not_set'),
            "google_drive_folder": os.getenv('GOOGLE_DRIVE_FOLDER_ID', 'not_set'),
        },
        "services": {}
    }
    
    # Check AWS credentials
    try:
        if os.getenv('AWS_ACCESS_KEY_ID') and os.getenv('AWS_SECRET_ACCESS_KEY'):
            status["services"]["aws"] = "configured"
        else:
            status["services"]["aws"] = "missing_credentials"
            status["status"] = "degraded"
    except Exception as e:
        status["services"]["aws"] = f"error: {str(e)}"
        status["status"] = "unhealthy"
    
    # Check Google credentials
    try:
        if os.getenv('GOOGLE_CREDENTIALS_FILE'):
            if os.path.exists(os.getenv('GOOGLE_CREDENTIALS_FILE')):
                status["services"]["google_drive"] = "configured"
            else:
                status["services"]["google_drive"] = "credentials_file_missing"
                status["status"] = "degraded"
        else:
            status["services"]["google_drive"] = "missing_credentials"
            status["status"] = "degraded"
    except Exception as e:
        status["services"]["google_drive"] = f"error: {str(e)}"
        status["status"] = "unhealthy"
    
    return status


def get_app_info() -> Dict[str, Any]:
    """
    Get application information.
    
    Returns:
        Dict containing application information
    """
    return {
        "name": "LocNess Data Writer",
        "description": "DynamoDB to Google Drive CSV data writer",
        "version": "0.1.0",
        "author": "LocNess Team",
        "configuration": {
            "read_interval": "1 minute",
            "update_interval": "1 minute", 
            "csv_name_prefix": os.getenv('CSV_NAME_PREFIX', 'locness_data'),
        }
    }


if __name__ == "__main__":
    # Simple health check when run directly
    import json
    
    health = health_check()
    print(json.dumps(health, indent=2))
    
    if health["status"] != "healthy":
        exit(1)
