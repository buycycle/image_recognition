# take 100 images from bike_files, with its template_id, but not 79204(customerized)
# for each bike_id, only take the first picture, which is high chance the main image
# take the template name, using similarity to find the simaliar template with similarity > ??
import os
import pandas as pd
from buycycle.data import sql_db_read
from helper import load_spacy_model, load_df_templates, jaccard_similarity
from driver import templates_query, processed_templates_path, general_words

# Load Spacy models for English 
nlp_en = load_spacy_model('en_core_web_sm')
stop_words = nlp_en.Defaults.stop_words

# Load df_templates for similarity calculation
df_templates = load_df_templates(processed_templates_path, templates_query, nlp_en, general_words, stop_words)

test_data_query = """
SELECT bf.bike_id, b.bike_template_id AS template_id, bt.name AS template_name, bt.family_id, bf.file_name
FROM bike_files bf
LEFT JOIN bikes b ON bf.bike_id = b.id
LEFT JOIN bike_templates bt ON b.bike_template_id = bt.id
WHERE bf.sort_order = 0
AND b.bike_template_id != 79204
ORDER BY b.created_at DESC
LIMIT 100
"""

test_file_path = "data/test_expanded.csv"

def load_test_file(test_file_path):
    if os.path.exists(test_file_path):
        df_test = pd.read_csv(test_file_path)
        print("Test data loaded from CSV file.")
    else:
        df_test = sql_db_read(
                query=test_data_query,
                DB="DB_BIKES",
                config_paths="config/config.ini",
                dtype="",
                index_col="bike_id",
            )
        df_test.reset_index(inplace=True)
        print("Test data read.")
    # add column which compare df_templates name to find similar_templates, which is a dic contains id and template name
    similarity_threshold = 0.5
    # Add column which compares df_templates name to find similar_templates
    similar_templates = []
    sum_similar_tids = []
    for _, row in df_test.iterrows():
        template_name_set = set(row['template_name'].split())
        similar_templates_for_row = []
        for _, template_row in df_templates.iterrows():
            template_name_set_2 = set(str(template_row['name']).split())
            similarity = jaccard_similarity(template_name_set, template_name_set_2)
            if similarity > similarity_threshold:
                similar_templates_for_row.append({
                    'template_id': template_row['template_id'],
                    'template_name': template_row['name'],
                    'simialrity': similarity
                })
        similar_templates.append(similar_templates_for_row)
        sum_similar_tids.append(len(similar_templates_for_row))
    
    df_test['sum_similar_tids'] = sum_similar_tids
    df_test['similar_templates'] = similar_templates

    df_test.to_csv(test_file_path, index=False)

    return df_test

load_test_file(test_file_path)