import base64
import os
import json
import boto3
from google.cloud import vision
from google.api_core.client_options import ClientOptions
from google.oauth2 import service_account
from botocore.exceptions import ClientError
def get_secret(secret_name, region_name="eu-central-1"):
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        # Handle as needed
        print(f"Error retrieving secret: {e}")
        raise e
    return json.loads(get_secret_value_response['SecretString'])
def get_google_vision_client():
    # Retrieve the service account JSON from Secrets Manager
    secret_name = os.environ['SECRET_NAME']
    service_account_info = get_secret(secret_name)

    # Create credentials from the service account info
    credentials = service_account.Credentials.from_service_account_info(service_account_info)

    # Initialize the client with the credentials
    client = vision.ImageAnnotatorClient(credentials=credentials)
    return client


def process_image(image_data, vision_client):

   image = vision.Image(content=image_data)
   # Call Google Vision API
   response = vision_client.web_detection(image=image)
   print(response)

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

   return ["canyon", "trek"]

