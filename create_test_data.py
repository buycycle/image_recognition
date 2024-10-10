# take 100 images from bike_files, with its template_id, excluding 79204(customerized)
# for each bike_id, only take the first picture, which is high chance the main image
import requests
from buycycle.data import sql_db_read
from helper import load_spacy_model, load_df_templates, jaccard_similarity
from driver import templates_query, processed_templates_path, general_words

# Load Spacy models for English 
nlp_en = load_spacy_model('en_core_web_sm')
stop_words = nlp_en.Defaults.stop_words

# Load df_templates for similarity calculation
df_templates = load_df_templates(processed_templates_path, templates_query, nlp_en, general_words, stop_words)

test_data_query = """
SELECT 
    bf.bike_id, 
    b.bike_template_id AS template_id, 
    bt.name AS template_name, 
    bt.family_id AS family_id, 
    bf.file_name
FROM 
    bike_files bf
LEFT JOIN 
    bikes b ON bf.bike_id = b.id
LEFT JOIN 
    bike_templates bt ON b.bike_template_id = bt.id
WHERE bf.sort_order = 0
AND b.bike_template_id != 79204
AND b.created_at >= DATE_SUB(NOW(), INTERVAL 1 DAY)
ORDER BY b.created_at DESC
LIMIT 5;
"""

test_file_path = "data/df_text.csv"

def load_test_file(test_file_path):
    """
    Load the test data, and remove the row with invalid URLs
    """
    df_test = sql_db_read(
        query=test_data_query,
        DB="DB_BIKES",
        config_paths="config/config.ini",
        dtype="",
        index_col="bike_id",
    )
    df_test.reset_index(inplace=True)
    print("Test data read.")

    # Check if the URLs in the file_name column are valid
    aws_url = "https://buycycle-prod.s3.eu-central-1.amazonaws.com/images/770/"
    invalid_rows = []
    for index, row in df_test.iterrows():
        image_url = f"{aws_url}{row['file_name']}"
        try:
            response = requests.head(image_url)
            if response.status_code != 200:
                print(f"URL {image_url} is not accessible. Deleting row {index}.")
                invalid_rows.append(index)
        except requests.RequestException as e:
            print(f"An error occurred while trying to access {image_url}: {e}. Deleting row {index}.")
            invalid_rows.append(index)
        
    # Drop invalid rows
    df_test.drop(invalid_rows, inplace=True, errors='ignore')
    df_test.reset_index(drop=True, inplace=True)
    df_test.to_csv(test_file_path, index=False)
    return df_test


load_test_file(test_file_path)
