import os
import re
import spacy
import ast
import pandas as pd
import requests
from collections import Counter

from buycycle.data import sql_db_read


def load_spacy_model(model_name):
    """
    load spacy models if it doesn't exist
    """
    try:
        nlp = spacy.load(model_name)
        print(f"{model_name} is already loaded.")
    except OSError:
        from spacy.cli import download
        download(model_name)
        nlp = spacy.load(model_name)
        print(f"{model_name} has been downloaded and loaded.")
    return nlp


def load_df_templates(csv_file_path, templates_query, nlp_en, general_words, stop_words):
    """
    Load or download df_templates,
    which is based on table bike_templates and complement with extra columns,
    and will be used in calculate similarity

    Returns: processed templates dataframe
    """
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
        # combine all relevant columns
        df_templates['combined'] = df_templates['brand']+ " " +df_templates['family_model']
        # process text
        df_templates['combined_tokens'] = df_templates['combined'].apply(lambda text: preprocess_text(text, nlp_en, general_words, stop_words)[0])

        df_templates.to_csv(csv_file_path, index=False)
        print("DataFrame saved to CSV file.")
    return df_templates


# Define the text preprocsiing steps, which will be used for both templates_df and response
def preprocess_text(text, nlp_en, general_words, stop_words):
    """
    Process the text before calculating the similarity
    Returns:
        set(tokens), applied for templates_df preprocessing
        set(filtered_tokens), applied for response preprocessing
    """
    if not isinstance(text, str):
        text = str(text)
    text = text.lower()
    text = text.strip()
    text = re.sub(r'[^\w\s.]', ' ', text)  # Remove special characters except periods

    # Process text using Spacy for English
    doc = nlp_en(text)
    tokens = [token.lemma_ for token in doc]

    # remove empty word, stop words and self-defined general words
    tokens = [word for word in tokens if word not in stop_words and word not in general_words and word.strip() and word != "."]

    # further process for request string
    # take 10 results, filter the words appear more then 3 times
    token_counts = Counter(tokens)
    filtered_tokens = [word for word in tokens if token_counts[word] > 3]

    return set(tokens), set(filtered_tokens)


def jaccard_similarity(set1, set2):
    """
    Calculate the similarity according to how many words appear in both sets
    Returns: similarity score
    """
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return intersection / union if union != 0 else 0


def extract_scarping_info(url, params, num):
    """
    take the response from Scrapingdog, and extract the titles from the response
    Params:
        response: the response directly from Scrapingdog api
        num: the amount of titles to extract
    Returns:
        response_text: string of combined titles
    """
    response = requests.get(url, params=params)
    if response.status_code == 200:
        response_json = response.json()
        titles = [result["title"] for result in response_json["lens_results"][:num]]
        response_text = " ".join(titles)
        return response, response_text

    print(f"Request for url {params['url']} failed with status code: {response.status_code}")
    return response, None

def get_matches_scraping(url, params, df_templates, num, nlp_en, general_words, stop_words):
    """
    Workflow for whole process
    Returns: results of every phase, can be used for saving file and checking the result
    """
    # extract required titles and return a string
    response, response_text = extract_scarping_info(url, params, num)
    # preprocess text and tokenize
    response_tokens = preprocess_text(response_text, nlp_en, general_words, stop_words)[1]
    # calculate similarity and get the top matches
    if response_tokens:
        df_templates['similarity'] = df_templates['combined_tokens'].apply(lambda tokens: jaccard_similarity(tokens, response_tokens))
        top_matches = df_templates.nlargest(num, 'similarity')

        return response, response_text, response_tokens, top_matches

    print("No result found.")
    return response, None, None, None



        


    
    

    

