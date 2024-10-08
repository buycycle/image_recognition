import os
import spacy
import pandas as pd
from create_test_data import load_test_file
from driver import processed_templates_path, templates_query, general_words
from google.cloud import vision
from helper import load_spacy_model, load_df_templates, get_5_matches

# Load SpaCy models for English and German
nlp_en = load_spacy_model('en_core_web_sm')
nlp_de = load_spacy_model('de_core_news_sm')
# Combine stopwords from both languages
stop_words = nlp_en.Defaults.stop_words.union(nlp_de.Defaults.stop_words)

test_file_path = "data/test.csv"
df_test = load_test_file(test_file_path)

aws_url = "https://buycycle-prod.s3.eu-central-1.amazonaws.com/images/770/"

# connect to google vision ai api
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "config/bike-image-detection-demo-api.json"
client = vision.ImageAnnotatorClient()
df_templates = load_df_templates(processed_templates_path, templates_query)

def process_row(row):
    file_url = aws_url+row["file_name"]
    matches_df = get_5_matches(client, "web", file_url, df_templates, nlp_de, nlp_en, general_words, stop_words)
    match_ids = matches_df['template_id'].tolist()
    check_match = row['template_id'] in match_ids
    return pd.Series([match_ids, check_match])

df_test[['match_ids', 'check_match']] = df_test.apply(process_row, axis=1) 

# Calculate accuracy
correct_predictions = df_test['check_match'].sum()
total_predictions = len(df_test)
accuracy_rate = correct_predictions / total_predictions

df_test.to_csv("data/test_with_matches.csv", index=False)
print("test completed")
print(f"Accuracy rate: {accuracy_rate:.2%}")