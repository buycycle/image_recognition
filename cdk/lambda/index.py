import os
import sys
# Add the 'lib' directory to the Python path
current_dir = os.path.dirname(os.path.realpath(__file__))
lib_dir = os.path.join(current_dir, 'lib')
sys.path.append(lib_dir)

import json
import boto3
import base64
from google.cloud import vision
from botocore.exceptions import ClientError
from model import get_google_vision_client, process_image
from io import BytesIO
import cgi
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
def parse_multipart(event):
    # Get the content type from headers
    content_type = event['headers'].get('Content-Type') or event['headers'].get('content-type')
    if not content_type:
        raise ValueError("Content-Type header is missing")
    # Decode the body if it's base64 encoded
    body = event['body']
    if event.get('isBase64Encoded', False):
        body = base64.b64decode(body)
    else:
        body = body.encode('utf-8')  # Ensure the body is in bytes
    # Prepare the environment and headers for FieldStorage
    environ = {'REQUEST_METHOD': 'POST'}
    headers = {'content-type': content_type}
    # Parse the multipart form data
    fs = cgi.FieldStorage(fp=BytesIO(body), environ=environ, headers=headers)
    # Access the file part
    file_item = fs['file']
    if not file_item.file:
        raise ValueError("File part is missing in the form data")
    # Return the file content directly
    return file_item.file.read()

def lambda_handler(event, context):
    try:
        # Log the incoming event
        print("Received event:")
            # Handle API Gateway multipart/form-data event
        image_data = parse_multipart(event)
        # Log the image data size
        print(f"Image data size: {len(image_data)} bytes")
        # Initialize the Google Vision client
        vision_client = get_google_vision_client()
        # Process the image using the model logic
        most_likely_family_id = process_image(image_data, vision_client)
        return {
            'statusCode': 200,
            'body': json.dumps({'most_likely_family_id': most_likely_family_id})
        }
    except Exception as e:
        error_message = str(e)
        print(f"Error processing request: {error_message}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Internal server error', 'error': error_message})
        }

