import json
import boto3
import base64
import os
from google.cloud import vision
from botocore.exceptions import ClientError
from model import get_google_vision_client, process_image
# Initialize the S3 client
s3_client = boto3.client('s3')
# Initialize the Secrets Manager client
secrets_client = boto3.client('secretsmanager')
def get_secret(secret_name):
    try:
        response = secrets_client.get_secret_value(SecretId=secret_name)
        secret = json.loads(response['SecretString'])
        return secret
    except ClientError as e:
        print(f"Error retrieving secret: {e}")
        raise e
def lambda_handler(event, context):
    try:
        # Log the incoming event
        print("Received event: " + json.dumps(event, indent=2))
        # Get the bucket and object key from the S3 event
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']
        # Log the bucket and key
        print(f"Bucket: {bucket}, Key: {key}")
        # Get the image from S3
        response = s3_client.get_object(Bucket=bucket, Key=key)
        image_data = response['Body'].read()
        # Log the image data size
        print(f"Image data size: {len(image_data)} bytes")
        # Retrieve Google API credentials from Secrets Manager
        secret_name = os.environ['SECRET_NAME']
        secret = get_secret(secret_name)
        google_api_key = secret['IMAGE_RECOGNITION_GOOGLE_API_KEY']
        google_project_name = secret['IMAGE_RECOGNITION_GOOGLE_PROJECT_NAME']
        # Log the Google API key and project name
        print(f"Google API Key: {google_api_key}, Project Name: {google_project_name}")
        # Initialize the Google Vision client with the API key
        # vision_client = get_google_vision_client(google_api_key)
        # Process the image using the model logic
        # most_likely_family_id = process_image(image_data, vision_client)
        return {
            'statusCode': 200,
            'body': json.dumps({'most_likely_family_id': "test"})
        }
    except Exception as e:
        print(f"Error processing request: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Internal server error'})
        }

