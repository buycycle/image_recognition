# take the first 100 images from bike_files, with its template_id, but not df["template_id"] != 79204(customerized)
# group by bike_id, only choose the first one, which is high chance the main image
import os
import pandas as pd
from buycycle.data import sql_db_read

test_data_query = """
SELECT bf.bike_id, b.bike_template_id AS template_id, bf.file_name
FROM bike_files bf
LEFT JOIN bikes b
ON bf.bike_id = b.id
WHERE bf.sort_order = 0
AND b.bike_template_id != 79204
ORDER BY b.created_at DESC
LIMIT 100
"""

test_file_path = "data/test.csv"

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
        df_test.to_csv(test_file_path, index=False)
        print("Test data saved to CSV file.")
    return df_test
