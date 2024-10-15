import json
import datetime
import pandas as pd
import configparser
from collections import Counter
from driver import templates_query, processed_templates_path, general_words
from helper import load_spacy_model, load_df_templates, get_matches_scraping
from create_test_data import load_test_file

# Read the API key from config.ini
config = configparser.ConfigParser()
config.read('config/config.ini')

# define the path for result
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
response_file_path = f"data/scrapingdog_response_{timestamp}.txt"
test_result_path = f"data/test_with_matches_{timestamp}.csv"
test_file_path = f"data/test_df_{timestamp}.csv"

# load test data
df_test = load_test_file(test_file_path)

# Load SpaCy models for English and German
nlp_en = load_spacy_model('en_core_web_sm')
stop_words = nlp_en.Defaults.stop_words

# Load df_templates for similarity calculation
df_templates = load_df_templates(processed_templates_path, templates_query, nlp_en, general_words, stop_words)

# connect to api and get the response
api_key = config['Scrapingdog']['api_key']
url = "https://api.scrapingdog.com/google_lens"
aws_url = "https://buycycle-prod.s3.eu-central-1.amazonaws.com/images/770/"

def save_result(result_file_path, row, response, response_text, response_tokens, matches_df, most_common_family_id, top_3_family_model_ids):
    """
    Write the results of process to txt file for later check
    """
    with open(result_file_path, 'a') as file:
        file.write(f"---------- Result with bike_id: {row["bike_id"]} ----------\n")
        file.write(f"Image url: {aws_url}{row["file_name"]}\n")
        file.write(f"Brand: {row["brand_id"]} {row["brand"]}\n")
        file.write(f"Tmplate: {row["template_id"]} {row["template_name"]}\n")
        file.write(f"Family: {row["family_id"]} {row["family"]} -> Return: {most_common_family_id}\n")
        file.write(f"Family model: {row["family_model_id"]} {row["family_model"]} -> Return: {top_3_family_model_ids}\n")
        if matches_df is not None:
            file.write("Top 5 matches:\n")
            file.write(matches_df.to_string(index=False))
            file.write("\n\n")
        else: 
            file.write("No matches found.\n")
        file.write(f"Preprocessed text: {response_tokens}\n\n") 
        file.write(f"Extracted text: {response_text}\n\n")
        # Write the complete response
        file.write(f"Complete response: {response}\n")
        if response.status_code == 200:
            json_response = response.json()
            formatted_json = json.dumps(json_response, indent=4)
            file.write(f"Response -> {formatted_json}\n\n\n\n") 


def process_row(row):
    """
    Process each row of the test data
    """
    file_url = row["file_name"]
    image_url = f"{aws_url}{file_url}"
    params = {
        "api_key": api_key,
        "url": f"https://lens.google.com/uploadbyurl?url={image_url}",
    }
    response, response_text, response_tokens, matches_df = get_matches_scraping(url, params, df_templates, 25, nlp_en, general_words, stop_words) 
    
    if matches_df is None or matches_df.empty:
        # Handle the case where no matches are found
        match_tids = []
        most_common_family_id = None
        top_3_family_model_ids = None
        template_check = False
        family_check = False
        family_model_check = False
        top_family_models_check = False
    else:
        match_tids = matches_df['template_id'].tolist()
        match_fids = matches_df['family_id'].tolist()
        match_fmids = matches_df['family_model_id'].tolist()
        
        # first check, if the template_id is in the top 25 matches
        template_check = row['template_id'] in match_tids

        # check family_id and family_model_id
        most_common_family_id = Counter(match_fids).most_common(1)[0][0]
        top_3_family_model_ids = [item[0] for item in Counter(match_fmids).most_common(3)]

        family_check = most_common_family_id == row["family_id"]
        family_model_check = top_3_family_model_ids[0] == row["family_model_id"]
        top_family_models_check = row["family_model_id"] in top_3_family_model_ids

    save_result(response_file_path, row, response, response_text, response_tokens, matches_df, most_common_family_id, top_3_family_model_ids)
    return pd.Series([match_tids, template_check, most_common_family_id, family_check, top_3_family_model_ids, family_model_check, top_family_models_check])


# add result to df_test and save it
df_test[['match_ids', 'template_check', 'match_family_id', 'family_check','top_3_family_model_ids', 'family_model_check', 'top_family_models_check']] = df_test.apply(process_row, axis=1) 
df_test.to_csv(test_result_path, index=False)

# Calculate accuracy
template_match = df_test['template_check'].sum()
family_match = df_test['family_check'].sum()
family_model_match = df_test['family_model_check'].sum()
top_family_models_match = df_test['top_family_models_check'].sum()
total_predictions = len(df_test)
template_accuracy_rate = template_match / total_predictions
family_accuracy_rate = family_match / total_predictions
family_model_accuracy_rate = family_model_match / total_predictions
top_family_models_accuracy_rate = top_family_models_match / total_predictions

# add the summary back to text 
with open(response_file_path, 'r') as file:
    existing_content = file.read()
# Insert the new sentence at the beginning
summary = f"template_id accuracy rate(25 returned template_ids): {template_accuracy_rate:.2%}\nfamily_id accuracy rate(most returned family_id): {family_accuracy_rate:.2%}\nfamily_model_id accuracy rate(most returned family_model_id): {family_model_accuracy_rate:.2%}\ntop 3 family_model_id accuracy rate: {top_family_models_accuracy_rate:.2%}\n\n\n"
modified_content = summary + existing_content
# Write the modified content back to the file
with open(response_file_path, 'w') as file:
    file.write(modified_content)

print("test completed")
print(f"template_id accuracy rate: {template_accuracy_rate:.2%}")
print(f"family_id accuracy rate: {family_accuracy_rate:.2%}")
print(f"family_model_id accuracy rate: {family_model_accuracy_rate:.2%}")
print(f"top_family_model_ids accuracy rate: {top_family_models_accuracy_rate:.2%}")

