import base64
from google.cloud import vision
from google.api_core.client_options import ClientOptions
def get_google_vision_client(api_key):
    # Set up client options with the API key
    client_options = ClientOptions(api_key=api_key)

    # Create a client with the API key
    client = vision.ImageAnnotatorClient(client_options=client_options)

    return client

def process_image(image_data, vision_client):
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

   return most_likely_family_id

