"""
S3 Bucket Creation Script for Agri-Nexus V1 Platform
Creates S3 bucket for storing crop images and audio files with appropriate CORS configuration
"""

import boto3
import os
import json
from dotenv import load_dotenv

load_dotenv()

def create_s3_bucket():
    """
    Create S3 bucket with CORS configuration for Streamlit frontend access
    """
    
    s3_client = boto3.client(
        's3',
        region_name=os.getenv('AWS_REGION', 'us-east-1'),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )
    bucket_name = os.getenv('IMAGE_BUCKET', 'agri-nexus-images')
    region = os.getenv('AWS_REGION', 'us-east-1')
    
    try:
        # Create bucket
        if region == 'us-east-1':
            # us-east-1 doesn't need LocationConstraint
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={'LocationConstraint': region}
            )
        
        print(f"✅ S3 bucket '{bucket_name}' created successfully!")
        
        # Configure CORS for Streamlit frontend access
        cors_configuration = {
            'CORSRules': [
                {
                    'AllowedHeaders': ['*'],
                    'AllowedMethods': ['GET', 'PUT', 'POST', 'DELETE', 'HEAD'],
                    'AllowedOrigins': ['*'],  # In production, restrict to specific domains
                    'ExposeHeaders': ['ETag'],
                    'MaxAgeSeconds': 3000
                }
            ]
        }
        
        s3_client.put_bucket_cors(
            Bucket=bucket_name,
            CORSConfiguration=cors_configuration
        )
        
        print(f"✅ CORS configuration applied to bucket '{bucket_name}'")
        
        # Configure lifecycle policy to delete old files after 90 days
        lifecycle_configuration = {
            'Rules': [
                {
                    'ID': 'DeleteOldImages',
                    'Status': 'Enabled',
                    'Prefix': 'images/',
                    'Expiration': {'Days': 90}
                },
                {
                    'ID': 'DeleteOldAudio',
                    'Status': 'Enabled',
                    'Prefix': 'audio/',
                    'Expiration': {'Days': 30}
                }
            ]
        }
        
        s3_client.put_bucket_lifecycle_configuration(
            Bucket=bucket_name,
            LifecycleConfiguration=lifecycle_configuration
        )
        
        print(f"✅ Lifecycle policy applied to bucket '{bucket_name}'")
        
        # Enable versioning for data protection
        s3_client.put_bucket_versioning(
            Bucket=bucket_name,
            VersioningConfiguration={'Status': 'Enabled'}
        )
        
        print(f"✅ Versioning enabled for bucket '{bucket_name}'")
        
        # Add bucket tagging
        s3_client.put_bucket_tagging(
            Bucket=bucket_name,
            Tagging={
                'TagSet': [
                    {'Key': 'Project', 'Value': 'Agri-Nexus-V1'},
                    {'Key': 'Environment', 'Value': os.getenv('ENVIRONMENT', 'development')}
                ]
            }
        )
        
        print(f"✅ Tags applied to bucket '{bucket_name}'")
        print(f"\n📦 Bucket URL: https://{bucket_name}.s3.{region}.amazonaws.com")
        
        return bucket_name
        
    except s3_client.exceptions.BucketAlreadyOwnedByYou:
        print(f"⚠️  Bucket '{bucket_name}' already exists and is owned by you!")
        return bucket_name
    except s3_client.exceptions.BucketAlreadyExists:
        print(f"❌ Bucket '{bucket_name}' already exists and is owned by someone else!")
        print("Please choose a different bucket name in your .env file")
        return None
    except Exception as e:
        print(f"❌ Error creating bucket: {str(e)}")
        raise


def delete_s3_bucket():
    """Delete the S3 bucket and all its contents (useful for testing/cleanup)"""
    s3_client = boto3.client(
        's3',
        region_name=os.getenv('AWS_REGION', 'us-east-1'),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )
    s3_resource = boto3.resource(
        's3',
        region_name=os.getenv('AWS_REGION', 'us-east-1'),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )
    bucket_name = os.getenv('IMAGE_BUCKET', 'agri-nexus-images')
    
    try:
        # Delete all objects in bucket first
        bucket = s3_resource.Bucket(bucket_name)
        bucket.objects.all().delete()
        bucket.object_versions.all().delete()
        
        # Delete the bucket
        s3_client.delete_bucket(Bucket=bucket_name)
        print(f"✅ Bucket '{bucket_name}' and all contents deleted!")
    except s3_client.exceptions.NoSuchBucket:
        print(f"⚠️  Bucket '{bucket_name}' does not exist!")
    except Exception as e:
        print(f"❌ Error deleting bucket: {str(e)}")
        raise


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'delete':
        delete_s3_bucket()
    else:
        create_s3_bucket()
