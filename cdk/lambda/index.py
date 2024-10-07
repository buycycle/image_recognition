import os
import json
import boto3
from google.cloud import vision
from botocore.exceptions import ClientError
from model import get_google_vision_client, process_image
# Initialize the S3 client
s3_client = boto3.client('s3')
# Initialize the SNS client
sns_client = boto3.client('sns')
# Initialize the Secrets Manager client
secrets_client = boto3.client('secretsmanager')
# The ARN of the SNS topic
SNS_TOPIC_ARN = os.environ['SNS_TOPIC_ARN']
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
        # Process each record in the event
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
            # Construct the message including the object key
            message = {
                'bucket': bucket_name,
                'key': object_key,
                'family_id': most_likely_family_id
            }
            # Publish the result to the SNS topic
            sns_client.publish(
                TopicArn=SNS_TOPIC_ARN,
                Message=json.dumps(message),
                Subject='Image Processing Result'
            )
    except Exception as e:
        error_message = str(e)
        print(f"Error processing request: {error_message}")
