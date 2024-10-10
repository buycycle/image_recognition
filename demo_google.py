import io
import os
import time
import re
import spacy
import ast
import pandas as pd
from google.cloud import vision
# import self defined variables
from driver import templates_query, processed_templates_path, general_words
from helper import load_spacy_model, preprocess_text, extract_response_info, jaccard_similarity, load_df_templates, get_5_matches
from buycycle.data import sql_db_read

image_path = "images/test_4.png"
image_url = "https://static.bike-resale.de/prod/public/media/bf/c9/8e/1727352959/Cube%20Hyde%202022%20-%20Fitnessbike%20-RA-10050%20(2).JPG"

# Load SpaCy models for English and German
nlp_en = load_spacy_model('en_core_web_sm')
nlp_de = load_spacy_model('de_core_news_sm')
# Combine stopwords from both languages
stop_words = nlp_en.Defaults.stop_words.union(nlp_de.Defaults.stop_words)

# Load templates dataframe
df_templates = load_df_templates(processed_templates_path, templates_query)

# Connect api and instantiate the client
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "config/bike-image-detection-demo-api.json"
client = vision.ImageAnnotatorClient()

print(get_5_matches(client, "local", image_path, df_templates, nlp_de, nlp_en, general_words, stop_words))
print(get_5_matches(client, "web", image_url, df_templates, nlp_de, nlp_en, general_words, stop_words))









