import io
import os
import time
import re
import spacy
import ast
import pandas as pd
from google.cloud import vision

from buycycle.data import sql_db_read

# self defined variables
templates_query = """
SELECT t.id as template_id, t.name, t.slug, b.name as brand
FROM bike_templates t
LEFT JOIN brands b
ON t.brand_id = b.id
"""
csv_file_path = "data/preprocessed_templates.csv"
general_words = {'buycycle', 'bike', 'bicycle', 'cycle', 'mountain', 'gravel', 'race', 'sport', 'road', 'cyclocross', 'triathlon', 'frame', 'electric','hybrid', 'buy', 'use', 'page', 'fahrrad','bici','sparen','brauchen', 'serie','compare', 'review', 'shop', 'online', 'top', 'good', 'sale', 'rate', 'race'}

image_path = "images/test_4.png"
with io.open(image_path, 'rb') as image_file:
    content = image_file.read()
# image_url = ""


# Step 1: Preparing necessary resources
# Helper function to load SpaCy models
def load_spacy_model(model_name):
    try:
        nlp = spacy.load(model_name)
        print(f"{model_name} is already loaded.")
    except OSError:
        from spacy.cli import download
        download(model_name)
        nlp = spacy.load(model_name)
        print(f"{model_name} has been downloaded and loaded.")
    return nlp

# Load SpaCy models for English and German
nlp_en = load_spacy_model('en_core_web_sm')
nlp_de = load_spacy_model('de_core_news_sm')
# Combine stopwords from both languages
stop_words = nlp_en.Defaults.stop_words.union(nlp_de.Defaults.stop_words)

# Step 2: Define functions
# Define the text preprocsiing steps, which will be used for both templates_df and response 
def preprocess_text(text, general_words):
    if not isinstance(text, str):
        text = str(text)
    text = re.sub(r'[^\w\s.]', ' ', text)  # Remove special characters except periods
    
    # Process text using SpaCy for German
    doc_de = nlp_de(text)
    tokens_de = [token.lemma_ for token in doc_de]

    text_de = ' '.join(tokens_de)
    text_en = text_de.lower()

    # Process text using SpaCy for English
    doc_en = nlp_en(text_en)
    tokens_en = [token.lemma_ for token in doc_en]

    # Convert tokens to a single string for further processing with the German model
    tokens = [word for word in tokens_en if word not in stop_words and word not in general_words]

    return set(tokens)

# combine infos from response and retuen a string
def extract_response_info(response):
    response_text = ""
    # Concatenate descriptions from web entities
    for web_entity in response.web_detection.web_entities:
        if web_entity.description:
            response_text += " " + web_entity.description

    # Concatenate page titles from pages with matching images
    for page in response.web_detection.pages_with_matching_images:
        if page.page_title:
            response_text += " " + page.page_title

    # Concatenate best guess labels
    for label in response.web_detection.best_guess_labels:
        if label.label:
            response_text += " " + label.label
    return response_text

# Define Jaccard Similarity
def jaccard_similarity(set1, set2):
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return intersection / union if union != 0 else 0


# Step 3: Preparing bike templates df, combine name ,slug and brand values and preprocess text
if os.path.exists(csv_file_path):
    df_templates = pd.read_csv(csv_file_path)
    print("Preprocessed dataFrame loaded from CSV file.")
    # Convert the 'combined_tokens' column back to sets
    df_templates['combined_tokens'] = df_templates['combined_tokens'].apply(ast.literal_eval)
else:
    df_templates = sql_db_read(
            query=templates_query,
            DB="DB_BIKES",
            config_paths="config/config.ini",
            dtype="",
            index_col="template_id",
        )
    df_templates.reset_index(inplace=True)
    df_templates['combined'] = df_templates['name'] + " " + df_templates['slug']+ " " + df_templates['brand']
    df_templates['combined_tokens'] = df_templates['combined'].apply(lambda text: preprocess_text(text, general_words))
    df_templates.to_csv(csv_file_path, index=False)
    print("DataFrame saved to CSV file.")


# Step 4: Connect api, send request and match template_id
# instantiate the client
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "config/bike-image-detection-demo-api.json"
client = vision.ImageAnnotatorClient()

# prepare the image (local source)
image = vision.Image(content=content)

# prepare the image (web source)
# image = vision.Image()
# image.source.image_uri = image_url

start_time = time.time()
response = client.web_detection(image=image)
print(f"Step 1: Vision API call took: {time.time() - start_time:.4f} seconds")
start_time = time.time()
response_text = extract_response_info(response)

# for testing without connecting cloud vision ai
# response_text = "Mountain Bike Bike Road Bike Canyon Bicycles Hybrid Bike Canyon Racing bicycle Electric Bike Bike Frame Buy a used Canyon Speedmax | buycycle Ireland Bici Triathlon Canyon | Risparmia sulle bici usate | buycycle Italia Canyon Triathlon Bikes | Sparen Sie bei gebrauchten Fahrrädern Canyon Speedmax CFR eTap used in M | buycycle USA 2024 Cervélo P-Series Ultegra Di2 vs Canyon Speedmax CF SLX 8 ... 2023 Canyon Speedmax CFR AXS 1by - 99 Spokes 2024 Ribble Ultra Tri Disc - Hero – Specs, Comparisons, Reviews 2022 Canyon Speedmax CF SLX Hawaii LTD - 99 Spokes mountain bike"

vision_api_tokens = preprocess_text(response_text, general_words)
df_templates['similarity'] = df_templates['combined_tokens'].apply(lambda tokens: jaccard_similarity(tokens, vision_api_tokens))

# Get the top 5 matches
print(f"Step 2: Matching: {time.time() - start_time:.4f} seconds")
top_5_matches = df_templates.nlargest(5, 'similarity')[["template_id", "brand", "name", "slug", "similarity"]]

print("Top 5 matches:")
print(top_5_matches)


# optional, for saving result
result_file_path = "data/output.txt"
with open(result_file_path, 'w') as file:
    file.write(f"Complete response: {response}\n")
    file.write(f"Extracted text: {response_text}\n")
    file.write(f"Preprocessed text: {vision_api_tokens}\n")
    file.write(f"Top 5 matches: {top_5_matches}\n")





