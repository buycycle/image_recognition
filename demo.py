import io
import os
import pandas as pd
from google.cloud import vision
import re
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

# Load NLTK data
stop_words = set(stopwords.words('english'))
lemmatizer = WordNetLemmatizer()

# instantiate the client
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "config/bike-image-detection-demo-api.json"
client = vision.ImageAnnotatorClient()

# prepare the image (local source)
image_path = "images/test_4.png"
with io.open(image_path, 'rb') as image_file:
    content = image_file.read()
image = vision.Image(content=content)

# # prepare the image (web source)
# image_url = ""
# image = vision.Image()
# image.source.image_uri = image_url

response = client.web_detection(image=image)
print(response)
# for web_entity in response.web_detection.web_entities:
#     print(web_entity.description, web_entity.score)

# preprocessing the text from vision ai
general_words = {'bike', 'bicycle', 'mountain', 'gravel', 'racing', 'road', 'cyclocross'}

def preprocess_text(text, general_words):
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)  # Remove special characters

    tokens = word_tokenize(text)

    # Remove stopwords/self defined general words and lemmatize
    tokens = [lemmatizer.lemmatize(word) 
              for word in tokens 
              if word not in stop_words and word not in general_words]

# convert text to vector

# compute similarity