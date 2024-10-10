# each request 5 credits, only 1000 credits for free acount
import pandes as pd
import requests
import configparser
from driver import templates_query, processed_templates_path, general_words
from helper import load_spacy_model, preprocess_text, jaccard_similarity, load_df_templates

# Read the API key from config.ini
config = configparser.ConfigParser()
config.read('config/config.ini')

result_file_path = "data/scrapingdog_result.txt"
image_url = "https://buycycle-prod.s3.eu-central-1.amazonaws.com/images/770/1074456/6e11006d-683c-4fd1-bb29-3885f33f291f.webp"
test_file_path = "data/test_expanded.csv"
df_test = load_test_file(test_file_path)

# Load SpaCy models for English and German
nlp_en = load_spacy_model('en_core_web_sm')
nlp_de = load_spacy_model('de_core_news_sm')
# Combine stopwords from both languages
stop_words = nlp_en.Defaults.stop_words.union(nlp_de.Defaults.stop_words)

# Load templates dataframe
df_templates = load_df_templates(processed_templates_path, templates_query)

# connect to api and get the response
api_key = config['Scrapingdog']['api_key']

url = "https://api.scrapingdog.com/google_lens"

params = {
    "api_key": api_key,
    "url": f"https://lens.google.com/uploadbyurl?url={image_url}",
}

response = requests.get(url, params=params)

def extract_scarping_info(response):
    response_5_titles = ""
    if response.status_code == 200:
        response_json = response.json()
        titles = [result["title"] for result in response_json["lens_results"]]
        for title in titles:
            response_5_titles += title + " "
        return response_5_titles
    else:
        print(f"Request failed with status code: {response.status_code}")

def get_5_matches(url, params, df_templates, nlp_de, nlp_en, general_words, stop_words):
    response = requests.get(url, params=params)
    response_text = extract_scarping_info(response)
    response_tokens = preprocess_text(response_text, nlp_de, nlp_en, general_words, stop_words)
    if not response_tokens:
        top_5_matches = None
        print("No result found.")
    else:
        df_templates['similarity'] = df_templates['combined_tokens'].apply(lambda tokens: jaccard_similarity(tokens, response_tokens))
        top_5_matches = df_templates.nlargest(5, 'similarity')[["template_id", "brand", "name", "slug", "similarity"]]

    return response, response_text, response_tokens, top_5_matches

def save_result(result_file_path, row, response, response_text, vision_api_tokens, matches_df):
    with open(result_file_path, 'a') as file:
        file.write(f"--- Result with bike_id: {row["bike_id"]} with template {row["template_id"]}, {row["template_name"]} ---\n")
        file.write(f"Image url: {aws_url}{row["file_name"]}\n")
        file.write(f"Top 5 matches: {matches_df}\n")
        file.write(f"Complete response: {response}\n")
        file.write(f"Extracted text: {response_text}\n")
        file.write(f"Preprocessed text: {vision_api_tokens}\n")
        # Write the JSON response
        json_response = {
            "lens_results": matches_df.to_dict(orient='records')
        }
        file.write(f"Response -> {json.dumps(json_response, indent=4)}\n")
        file.write("\n")  

# Function to check for intersection
def check_intersection(similar_template_ids, top_template_ids):
    set1 = set(similar_template_ids)
    set2 = set(top_template_ids)
    intersection = set1.intersection(set2)
    return len(intersection) > 0

def process_row(row):
    url = "https://api.scrapingdog.com/google_lens"
    image_url = aws_url+row["file_name"]
    params = {
        "api_key": api_key,
        "url": f"https://lens.google.com/uploadbyurl?url={image_url}",
    }
    response, response_text, response_tokens, matches_df = get_5_matches(url, params, df_templates, nlp_de, nlp_en, general_words, stop_words)
    match_ids = matches_df['template_id'].tolist()
    match_check = row['template_id'] in match_ids

    similar_template_ids = [template['template_id'] for template in row['similar_templates']]
    loose_check = check_intersection(match_ids, similar_template_ids)

    save_result(result_file_path, row, response, response_text, response_tokens, matches_df)
    return pd.Series([match_ids, match_check, loose_check])

df_test[['match_ids', 'match_check', 'loose_check']] = df_test.apply(process_row, axis=1) 

# Calculate accuracy
total_match = df_test['match_check'].sum()
total_loose_match = df_test['loose_check'].sum()
total_predictions = len(df_test)
accuracy_rate_strict = total_match / total_predictions
accuracy_rate_loose = total_loose_match / total_predictions

df_test.to_csv("data/test_with_matches.csv", index=False)
print("test completed")
print(f"Strict accuracy rate: {accuracy_rate_strict:.2%}")
print(f"Loose accuracy rate: {accuracy_rate_strict:.2%}")


# {
#     "lens_results": [
#         {
#             "position": 1,
#             "title": "Used Ultimate CF SL 7 AXS | CANYON US",
#             "source": "canyon.com",
#             "source_favicon": "https://encrypted-tbn1.gstatic.com/favicon-tbn?q=tbn:ANd9GcR78oFQbOBxhLMpHw117VHE7TpGxGC2Bodofc3IpcAMHsMnMCH9JQehx5sNrPFV_-Cnyn0YmCNOOKPzaz8kEYdG3FmXmmtSGMPtAmToikec25Ep1A",
#             "link": "https://www.canyon.com/en-us/outlet-bikes/road-bikes/ultimate-cf-sl-7-axs/50038215.html",
#             "thumbnail": "https://encrypted-tbn2.gstatic.com/images?q=tbn:ANd9GcR_H-RGRbYiBEFioBttN1QyA98oslEkaCN4f2YAy-3A-GiRxDXB"
#         },
# {
#     'position': 47, 
#     'title': 'Canyon Endurace CF SL 8 Di2 Review | Ultegra 12 Speed Di2 - YouTube', 
#     'source': 'youtube.com', 
#     'source_favicon': 'https://encrypted-tbn2.gstatic.com/favicon-tbn?q=tbn:ANd9GcSJqkDeIp4r8E4YFeIN54NKZVcykOisjz373y_DXCUH9RH3jDLetQvWIzlziT1XObIL62pk_3mp2rXzGbH7ZaM9Qz69T0ZFVKCMXgU4Vls709KL', 
#     'link': 'https://m.youtube.com/watch?v=0l69pG9kc9g', 'thumbnail': 'https://encrypted-tbn2.gstatic.com/images?q=tbn:ANd9GcSJzx7TXT8ne_C_YMew-BO2RI31WeNCDqcYb6M3DtUy4mWQ2seC'
#     },
#         {
#             "position": 2,
#             "title": "2024 Canyon Ultimate CF SL 7 (Canyon Size \"S\" / 54cm) - bicycles - by owner - bike sale - craigslist",
#             "source": "craigslist.org",
#             "source_favicon": "https://encrypted-tbn0.gstatic.com/favicon-tbn?q=tbn:ANd9GcS8U8VGwVkXx6QuoCspgthXaVn6QrKlizkfSi8px-..."
#         },
#         ...
#     ]
# }

 