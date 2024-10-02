import os
import json
import boto3
import base64
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
    # Get the bucket and object key from the S3 event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    # Get the image from S3
    response = s3_client.get_object(Bucket=bucket, Key=key)
    image_data = response['Body'].read()
    # Retrieve Google API credentials from Secrets Manager
    secret_name = os.environ['SECRET_NAME']
    secret = get_secret(secret_name)
    google_api_key = secret['IMAGE_RECOGNITION_GOOGLE_API_KEY']
    google_project_name = secret['IMAGE_RECOGNITION_GOOGLE_PROJECT_NAME']
    # Initialize the Google Vision client with the API key
    #vision_client = get_google_vision_client(google_api_key)
    # Process the image using the model logic
    #most_likely_family_id = process_image(image_data, vision_client)
    return {
        'statusCode': 200,
        'body': json.dumps({'most_likely_family_id': "test"})
    }

