import io
import os
import time
import re
import spacy
import ast
import pandas as pd
from google.cloud import vision
from driver import general_words

from buycycle.data import sql_db_read

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

# Step 2: Define functions
# Define the text preprocsiing steps, which will be used for both templates_df and response 
def preprocess_text(text, nlp_de, nlp_en, general_words, stop_words):
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
def load_df_templates(csv_file_path, templates_query):
    if os.path.exists(csv_file_path):
        df_templates = pd.read_csv(csv_file_path)
        print("Preprocessed dataframe loaded from CSV file.")
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
        df_templates['combined_tokens'] = df_templates['combined'].apply(lambda text: preprocess_text(text, nlp_de, nlp_en, general_words, stop_words))
        df_templates.to_csv(csv_file_path, index=False)
        print("DataFrame saved to CSV file.")
    return df_templates


def get_5_matches(google_client, source_type, image_source, df_templates, nlp_de, nlp_en, general_words, stop_words):
    if source_type == "local":
        with io.open(image_source, 'rb') as image_file:
            content = image_file.read()
        image = vision.Image(content=content)
    elif source_type == "web":
        image = vision.Image()
        image.source.image_uri = image_source
    response = google_client.web_detection(image=image)
    response_text = extract_response_info(response)
    vision_api_tokens = preprocess_text(response_text, nlp_de, nlp_en, general_words, stop_words)
    df_templates['similarity'] = df_templates['combined_tokens'].apply(lambda tokens: jaccard_similarity(tokens, vision_api_tokens))

    top_5_matches = df_templates.nlargest(5, 'similarity')[["template_id", "brand", "name", "slug", "similarity"]]

    return response, response_text, vision_api_tokens, top_5_matches





