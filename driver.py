# self defined variables

processed_templates_path = "data/preprocessed_templates.csv"

templates_query = """
SELECT t.id as template_id, t.name, t.slug, b.name as brand, t.family_id, t.family_model_id, fm.name as model, f.name as family
FROM bike_templates t
LEFT JOIN brands b ON t.brand_id = b.id
LEFT JOIN families f ON t.family_id = f.id
LEFT JOIN family_models fm ON t.family_model_id = fm.id
"""

general_words = {'buycycle', 'bike', 'bicycle', 'cycle', 'velo', 'mountain', 'gravel', 'race', 'sport', 'road', 'cyclocross', 'cyclo', 'cross', 'triathlon', 'frame', 'electric', 'hybrid', 'cyclocross', 'buy', 'use', 'page', 'fahrrad','bici','sparen','brauchen', 'serie','compare', 'review', 'shop', 'online', 'top', 'good', 'sale', 'rate', 'race', 'aluminum', 'carbon', 'edition', 'pro'}

image_path = "images/test_4.png"
