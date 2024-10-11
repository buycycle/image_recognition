import json
import requests
import configparser
from driver import templates_query, processed_templates_path, general_words
from helper import load_spacy_model, load_df_templates, get_matches_scraping

# Load Spacy models for English
nlp_en = load_spacy_model('en_core_web_sm')
stop_words = nlp_en.Defaults.stop_words

# Load df_templates for similarity calculation
df_templates = load_df_templates(processed_templates_path, templates_query, nlp_en, general_words, stop_words)

# Read the API key from config.ini
config = configparser.ConfigParser()
config.read('config/config.ini')

# get the image
aws_url = "https://buycycle-prod.s3.eu-central-1.amazonaws.com/images/770/"
file_url = "1076247/6adf8b65-35fc-4da4-b6b2-aa494383bd2b.webp"
image_url = f"{aws_url}{file_url}"

# Check first is the image_url valid
try:
    response = requests.head(image_url)
    if response.status_code != 200:
        raise Exception(f"URL {image_url} is not accessible. Ending process.")
except requests.RequestException as e:
    raise Exception(f"An error occurred while trying to access {image_url}: {e}")

# setup for scrapingdog api
api_key = config['Scrapingdog']['api_key']
url = "https://api.scrapingdog.com/google_lens"
params = {
    "api_key": api_key,
    "url": f"https://lens.google.com/uploadbyurl?url={image_url}",
}

# get the top similarity matches
response, response_text, response_tokens, matches_df = get_matches_scraping(url, params, df_templates, 5, nlp_en, general_words, stop_words)
print(matches_df.to_string())


# optional, saving result to the txt file
folder_name = file_url.split('/')[0]
result_file_path = f"data/result-{folder_name}.txt"
with open(result_file_path, 'w') as file:
    file.write(f"--- Result ---\n")
    file.write(f"Image url: {image_url}\n")
    file.write(f"Top 5 matches: {matches_df.to_string()}\n")
    # Write the JSON response
    file.write("Response ->\n")
    file.write(json.dumps(response.json(), indent=4))
    file.write("\n")
    file.write(f"Extracted text: {response_text}\n")
    file.write(f"Preprocessed text: {response_tokens}\n")
    file.write("\n")
print("Result saved!")




