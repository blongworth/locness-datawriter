#!/usr/bin/env python3
"""
Helper script to format Google Service Account credentials for Railway deployment.
This script reads your credentials.json file and outputs it in a format suitable
for the GOOGLE_CREDENTIALS_JSON environment variable.
"""

import json
import os

def main():
    credentials_file = "./credentials.json"
    
    if not os.path.exists(credentials_file):
        print(f"❌ Error: {credentials_file} not found!")
        print("\nPlease ensure your Google Service Account credentials file is present.")
        return
    
    try:
        with open(credentials_file, 'r') as f:
            creds_data = json.load(f)
        
        # Validate it's a service account
        if creds_data.get('type') != 'service_account':
            print("❌ Error: This doesn't appear to be a service account credentials file!")
            return
        
        # Output the JSON as a single line (required for environment variables)
        json_string = json.dumps(creds_data, separators=(',', ':'))
        
        print("✅ Google Service Account credentials ready for Railway!")
        print("\n" + "="*80)
        print("ENVIRONMENT VARIABLE NAME:")
        print("GOOGLE_CREDENTIALS_JSON")
        print("\n" + "="*80)
        print("ENVIRONMENT VARIABLE VALUE:")
        print("(Copy the entire line below)")
        print("-"*80)
        print(json_string)
        print("-"*80)
        
        print("\n📋 Instructions:")
        print("1. Copy the JSON string above")
        print("2. In Railway dashboard, go to your project")
        print("3. Click 'Variables' tab")
        print("4. Add new variable:")
        print("   - Name: GOOGLE_CREDENTIALS_JSON")
        print("   - Value: [paste the JSON string]")
        print("5. Deploy your application")
        
        print("\n🔒 Security Note:")
        print("- Keep this JSON string secure")
        print("- Never commit it to git")
        print("- Only use it in Railway environment variables")
        
        # Also show some credential info (without sensitive data)
        print("\n📊 Credential Info:")
        print(f"- Project ID: {creds_data.get('project_id', 'N/A')}")
        print(f"- Client Email: {creds_data.get('client_email', 'N/A')}")
        print(f"- Type: {creds_data.get('type', 'N/A')}")
        
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in {credentials_file}")
        print(f"Details: {e}")
    except Exception as e:
        print(f"❌ Error reading {credentials_file}")
        print(f"Details: {e}")

if __name__ == "__main__":
    main()
