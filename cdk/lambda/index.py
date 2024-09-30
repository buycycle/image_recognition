import json
import boto3
import base64
from google.cloud import vision
from botocore.exceptions import ClientError
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
    secret_name = 'your-secret-name'  # Replace with your secret name
    secret = get_secret(secret_name)
    google_api_key = secret['IMAGE_RECOGNITION_GOOGLE_API_KEY']
    google_project_name = secret['IMAGE_RECOGNITION_GOOGLE_PROJECT_NAME']

    # Initialize the Google Vision client with the API key
    vision_client = vision.ImageAnnotatorClient.from_service_account_json(google_api_key)

    # Convert image data to base64
    image_base64 = base64.b64encode(image_data).decode('utf-8')

    # Call Google Vision API
    response = vision_client.web_detection({
        'image': {
            'content': image_base64
        }
    })

    # Process the response
    web_detection = response.web_detection
    entities = web_detection.web_entities
    # Filter entities based on score
    filtered_entities = [entity for entity in entities if entity.score > 0.5]

    # Match entities to family IDs (example logic)
    family_ids = ['mountain_bike', 'road_bike', 'hybrid_bike']
    matches = []
    for entity in filtered_entities:
        for family_id in family_ids:
            if family_id in entity.description.lower():
                matches.append(family_id)

    # Determine the most likely family_id
    most_likely_family_id = max(set(matches), key=matches.count) if matches else None
    return {
        'statusCode': 200,
        'body': json.dumps({'most_likely_family_id': most_likely_family_id})
    }

