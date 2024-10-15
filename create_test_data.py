# take 100 images from bike_files, with its template_id, excluding 79204(customerized)
# for each bike_id, only take the first picture, which is high chance the main image
import requests
from buycycle.data import sql_db_read

test_data_query = """
SELECT 
    bf.bike_id, 
    b.brand_id AS brand_id,
    br.name AS brand,
    b.bike_template_id AS template_id, 
    bt.name AS template_name, 
    bt.family_id AS family_id, 
    f.name AS family,
    bt.family_model_id AS family_model_id,
    fm.name AS family_model,
    bf.file_name
FROM bike_files bf
LEFT JOIN bikes b ON bf.bike_id = b.id
LEFT JOIN bike_templates bt ON b.bike_template_id = bt.id
LEFT JOIN families f ON b.family_id = f.id
LEFT JOIN family_models fm ON b.family_model_id = fm.id
LEFT JOIN brands br ON b.brand_id = br.id
WHERE bf.sort_order = 0
AND b.price >= 2000
AND b.bike_template_id != 79204
AND b.created_at < '2023-10-01'
ORDER BY b.created_at DESC
LIMIT 170
"""

# most_used_family_model_id = """
# WITH top_family_model_ids AS (
#     SELECT family_model_id, count(*) as count
#     FROM bikes 
#     WHERE family_model_id is not NULL
#     GROUP BY family_model_id 
#     ORDER BY count DESC 
#     LIMIT 100
# ),
# ranked_bikes AS (
#     SELECT 
#         bf.bike_id, 
#         b.brand_id AS brand_id,
#         br.name AS brand,
#         b.bike_template_id AS template_id, 
#         bt.name AS template_name, 
#         bt.family_id AS family_id, 
#         f.name AS family,
#         bt.family_model_id AS family_model_id,
#         fm.name AS family_model,
#         bf.file_name,
#         ROW_NUMBER() OVER (PARTITION BY bt.family_model_id ORDER BY b.created_at DESC) as row_num
#     FROM bike_files bf
#     LEFT JOIN bikes b ON bf.bike_id = b.id
#     LEFT JOIN bike_templates bt ON b.bike_template_id = bt.id
#     LEFT JOIN families f ON b.family_id = f.id
#     LEFT JOIN family_models fm ON b.family_model_id = fm.id
#     LEFT JOIN brands br ON b.brand_id = br.id
#     WHERE bf.sort_order = 0
#     AND b.bike_template_id != 79204
#     AND b.created_at < '2023-10-01'
#     AND bt.family_model_id IN (SELECT family_model_id FROM top_family_model_ids
# )

# SELECT 
#     bike_id, 
#     brand_id,
#     brand,
#     template_id, 
#     template_name, 
#     family_id, 
#     family,
#     family_model_id,
#     family_model,
#     file_name
# FROM ranked_bikes
# WHERE row_num = 1
# LIMIT 100
# """

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

    # manually checked, part, unclear, duplicate, and catalog photos
    bad_images = [420484 ,420481, 420477,420254, 420243, 420169, 420166, 420130, 420097, 420063, 420037, 420015, 419963, 419956, 419951, 419950, 419944, 419943, 419936, 419935, 419929, 420426, 420253,420250, 420246, 420239, 419975, 419970, 419923, 419919, 419916, 419911, 419910, 419902, 419889, 419744, 419772, 419820, 419859, 419718, 419727, 419729, 419734, 419778, 419668, 419675, 419619, 419663, 419665]
    df_test = df_test[~df_test['bike_id'].isin(bad_images)]

    df_test['image_url'] = df_test.apply(lambda row: f"{aws_url}{row['file_name']}", axis=1)
    df_test.reset_index(drop=True, inplace=True)
    df_test.to_csv(test_file_path, index=False)
    return df_test
