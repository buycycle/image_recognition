import io
import os
import pandas as pd
from google.cloud import vision

# instantiate the client
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "config/bike-image-detection-demo-api.json"
client = vision.ImageAnnotatorClient()

# prepare the image (local source)
image_path = "images/test_1.png"
with io.open(image_path, 'rb') as image_file:
    content = image_file.read()
image = vision.Image(content=content)

# # prepare the image (web source)
# image_url = ""
# image = vision.Image()
# image.source.image_uri = image_url

response = client.web_detection(image=image)
for web_entity in response.web_detection.web_entities:
    print(web_entity.description, web_entity.score)