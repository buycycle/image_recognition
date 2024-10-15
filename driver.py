# self defined variables

processed_templates_path = "data/preprocessed_templates.csv"

templates_query = """
SELECT t.id as template_id, t.name,t.brand_id, b.name as brand, t.family_id, f.name as family, t.family_model_id, fm.name as family_model
FROM bike_templates t
LEFT JOIN brands b ON t.brand_id = b.id
LEFT JOIN families f ON t.family_id = f.id
LEFT JOIN family_models fm ON t.family_model_id = fm.id
"""

general_words = {'buycycle', 'bike', 'bicycle', 'cycle', 'velo','bici', 'buy', 'use', 'page', 'review', 'shop', 'online', 'top', 'good', 'sale', 'rate'}

image_path = "images/test_4.png"