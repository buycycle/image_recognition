import os
import json
import boto3
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
        print("Received event:", json.dumps(event, indent=2))

        # Extract bucket name and object key from the event
        for record in event['Records']:
            bucket_name = record['s3']['bucket']['name']
            object_key = record['s3']['object']['key']

            # Log the bucket name and object key
            print(f"Processing file from bucket: {bucket_name}, key: {object_key}")

            # Download the image from S3
            response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
            image_data = response['Body'].read()

            # Initialize the Google Vision client
            vision_client = get_google_vision_client()

            # Process the image using the model logic
            most_likely_family_id = process_image(image_data, vision_client)

            # Log the result
            print(f"Most likely family ID: {most_likely_family_id}")

    except Exception as e:
        error_message = str(e)
        print(f"Error processing request: {error_message}")

