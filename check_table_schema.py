#!/usr/bin/env python3
"""
Table Schema Verification Script for LocNess DynamoDB Table

This script checks if your DynamoDB table has the optimal schema for the 
LocNess Data Writer application.

Optimal Schema:
- Partition Key: 'data' (String)
- Sort Key: 'datetime_utc' (String)
"""

import os
import boto3
from dotenv import load_dotenv
from botocore.exceptions import ClientError

def main():
    # Load environment variables
    load_dotenv()
    
    table_name = os.getenv('DYNAMODB_TABLE_NAME')
    if not table_name:
        print("❌ Error: DYNAMODB_TABLE_NAME environment variable not set!")
        return
    
    # Initialize DynamoDB client
    try:
        dynamodb = boto3.client(
            'dynamodb',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        
        print(f"🔍 Checking DynamoDB table: {table_name}")
        print("="*60)
        
        # Describe table
        response = dynamodb.describe_table(TableName=table_name)
        table_info = response['Table']
        
        # Check key schema
        key_schema = table_info['KeySchema']
        
        print("📊 Current Table Schema:")
        print("-"*30)
        
        partition_key = None
        sort_key = None
        
        for key in key_schema:
            key_type = "Partition Key" if key['KeyType'] == 'HASH' else "Sort Key"
            print(f"  {key_type}: {key['AttributeName']}")
            
            if key['KeyType'] == 'HASH':
                partition_key = key['AttributeName']
            elif key['KeyType'] == 'RANGE':
                sort_key = key['AttributeName']
        
        print("\n🎯 Optimal Schema Check:")
        print("-"*30)
        
        # Check if schema is optimal
        optimal_pk = partition_key == 'data'
        optimal_sk = sort_key == 'datetime_utc'
        
        print(f"  Partition Key 'data': {'✅ YES' if optimal_pk else '❌ NO'} (current: {partition_key})")
        print(f"  Sort Key 'datetime_utc': {'✅ YES' if optimal_sk else '❌ NO'} (current: {sort_key})")
        
        if optimal_pk and optimal_sk:
            print("\n🎉 PERFECT! Your table has the optimal schema for maximum performance!")
            print("   The application will use fast table queries.")
        elif optimal_sk and partition_key != 'data':
            print(f"\n⚠️  PARTIAL: You have the right sort key but partition key is '{partition_key}'")
            print("   The application will fall back to scan operations.")
            print("   Consider migrating data to use 'data' as partition key.")
        else:
            print("\n📈 SUBOPTIMAL: Current schema will use scan operations")
            print("   This will work but may be slower for large datasets.")
            print("   Consider migrating to the optimal schema.")
        
        # Show additional table info
        print("\n📋 Table Details:")
        print("-"*20)
        print(f"  Status: {table_info['TableStatus']}")
        print(f"  Item Count: {table_info.get('ItemCount', 'Unknown')}")
        print(f"  Size: {table_info.get('TableSizeBytes', 0) / (1024*1024):.1f} MB")
        
        billing_mode = table_info.get('BillingModeSummary', {}).get('BillingMode', 'PROVISIONED')
        print(f"  Billing Mode: {billing_mode}")
        
        if billing_mode == 'PROVISIONED':
            read_capacity = table_info['ProvisionedThroughput']['ReadCapacityUnits']
            write_capacity = table_info['ProvisionedThroughput']['WriteCapacityUnits']
            print(f"  Read Capacity: {read_capacity} RCU")
            print(f"  Write Capacity: {write_capacity} WCU")
        
        # Show performance recommendations
        print("\n🚀 Performance Recommendations:")
        print("-"*35)
        
        if optimal_pk and optimal_sk:
            print("  ✅ No changes needed - optimal performance!")
            print("  ✅ Application will use efficient table queries")
        else:
            print("  📊 Current: Application will use scan operations")
            print("  ⚡ Recommended: Migrate to partition key 'data' + sort key 'datetime_utc'")
            print("  📈 Expected improvement: 10-100x faster queries")
        
        # Show GSI info if any
        gsi_list = table_info.get('GlobalSecondaryIndexes', [])
        if gsi_list:
            print(f"\n🔍 Global Secondary Indexes ({len(gsi_list)}):")
            print("-"*40)
            for gsi in gsi_list:
                gsi_name = gsi['IndexName']
                gsi_keys = gsi['KeySchema']
                print(f"  Index: {gsi_name}")
                for key in gsi_keys:
                    key_type = "PK" if key['KeyType'] == 'HASH' else "SK"
                    print(f"    {key_type}: {key['AttributeName']}")
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'ResourceNotFoundException':
            print(f"❌ Error: Table '{table_name}' not found!")
            print("   Check your DYNAMODB_TABLE_NAME environment variable.")
        elif error_code == 'UnauthorizedOperation':
            print("❌ Error: Insufficient permissions to describe table!")
            print("   Check your AWS credentials and IAM permissions.")
        else:
            print(f"❌ Error: {e}")
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
