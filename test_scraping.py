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
test_result_path = "data/test_with_matches.csv"

test_file_path = "data/test_expanded.csv"
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

def save_result(result_file_path, row, response, response_text, vision_api_tokens, matches_df):
    """
    Write the results of process to txt file for later check
    """
    with open(result_file_path, 'a') as file:
        file.write(f"---------- Result with bike_id: {row['bike_id']} ----------\n")
        file.write(f"Image url: {aws_url}{row['file_name']}\n")
        file.write(f"Bike template: {row['template_id']}  {row['template_name']}\n")
        file.write(f"Family id: {row['family_id']}\n")
        file.write(f"Family Model id: {row['family_model_id']}\n")
        if matches_df is not None:
            file.write("Top 5 matches:\n")
            file.write(matches_df.to_string(index=False))
            file.write("\n")
        else:
            file.write("No matches found.\n")
        file.write(f"Complete response: {response}\n")
        file.write(f"Extracted text: {response_text}\n")
        file.write(f"Preprocessed text: {vision_api_tokens}\n")
        # Write the JSON response
        if matches_df is not None:
            json_response = {
                "lens_results": matches_df.to_dict(orient='records')
            }
            file.write(f"Response -> {json.dumps(json_response, indent=4)}\n")
        file.write("\n")

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
    response, response_text, response_tokens, matches_df = get_matches_scraping(url, params, df_templates, 5, nlp_en, general_words, stop_words)
    # matches_df ["template_id", "brand", "name", "slug","family_id", "similarity"]

    if matches_df is None or matches_df.empty:
        # Handle the case where no matches are found
        template_check = False
        family_check = False
        model_check = False
        match_tids = []
        most_common_family_id = None
        most_common_family_model_id = None
    else:
        match_tids = matches_df['template_id'].tolist()
        match_fids = matches_df['family_id'].tolist()
        match_fmids = matches_df['family_model_id'].tolist()

        # first check, if the template_id is in the top 25 matches
        template_check = row['template_id'] in match_tids

        # second check, if the most frequently returned family_id the right family_id
        most_common_family_id = Counter(match_fids).most_common(1)[0][0]
        family_check = most_common_family_id == row["family_id"]
        most_common_family_model_id = Counter(match_fmids).most_common(1)[0][0]
        model_check = most_common_family_model_id == row["family_model_id"]

    save_result(response_file_path, row, response, response_text, response_tokens, matches_df)
    return pd.Series([template_check,  family_check, model_check, match_tids, match_fids , match_fmids])


# add result to df_test and save it
df_test[['template_check', 'family_check', 'model_check', 'match_template_ids', 'match_family_id', 'match_family_model_id']] = df_test.apply(process_row, axis=1)
df_test.to_csv(test_result_path, index=False)

# Calculate accuracy
template_match = df_test['template_check'].sum()
family_match = df_test['family_check'].sum()
model_match = df_test['model_check'].sum()
total_predictions = len(df_test)
template_accuracy_rate = template_match / total_predictions
family_accuracy_rate = family_match / total_predictions
model_accuracy_rate = model_match / total_predictions

print("test completed")
print(f"template_id accuracy rate: {template_accuracy_rate:.2%}")
print(f"family_id accuracy rate: {family_accuracy_rate:.2%}")
print(f"model_id accuracy rate: {model_accuracy_rate:.2%}")

