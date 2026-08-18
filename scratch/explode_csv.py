import pandas as pd
import re

file_path = "/Users/jihanmaisaroh/scrap_fasih/Sulteng_Pertanian.csv"
output_path = "/Users/jihanmaisaroh/scrap_fasih/Sulteng_Pertanian_Exploded.csv"

print("Loading data...")
# use engine='python' or just pd.read_csv to read everything
df = pd.read_csv(file_path, dtype=str)

print("Processing rows...")
# Prepare a list of dictionaries to construct a new dataframe
new_rows = []

for idx, row in df.iterrows():
    val = row['nama_usaha_prelist']
    
    # Base dictionary for the row (exclude nama_usaha_prelist)
    base_dict = row.drop('nama_usaha_prelist').to_dict()
    
    if pd.isna(val) or str(val).strip() == '':
        base_dict.update({
            'prelist_id_art': '',
            'prelist_id_ruta': '',
            'prelist_subsektor': '',
            'prelist_label': '',
            'prelist_source': '',
            'prelist_id_l2': '',
            'prelist_value': '',
            'prelist_idsbr': '',
            'prelist_id_l1': ''
        })
        new_rows.append(base_dict)
        continue
    
    # We want to extract each {...} block. 
    # Because sometimes it's truncated like "{id_art=7201070019000200-054042039-054#01, id_ruta=7201070019000"
    # We can split by '{' and for each block, parse whatever we can find.
    blocks = str(val).split('{')
    
    has_items = False
    for block in blocks[1:]: # skip the first one which is just '[' or empty
        has_items = True
        
        # Helper to safely extract using regex
        def get_val(key):
            m = re.search(f"{key}=([^,}}]+)", block)
            if m:
                res = m.group(1).strip()
                return '' if res == 'null' else res
            return ''
            
        new_dict = dict(base_dict) # copy base
        new_dict.update({
            'prelist_id_art': get_val('id_art'),
            'prelist_id_ruta': get_val('id_ruta'),
            'prelist_subsektor': get_val('subsektor'),
            'prelist_label': get_val('label'),
            'prelist_source': get_val('source'),
            'prelist_id_l2': get_val('id_l2'),
            'prelist_value': get_val('value'),
            'prelist_idsbr': get_val('idsbr'),
            'prelist_id_l1': get_val('id_l1')
        })
        new_rows.append(new_dict)
        
    if not has_items:
        # If somehow it has no '{'
        base_dict.update({
            'prelist_id_art': '',
            'prelist_id_ruta': '',
            'prelist_subsektor': '',
            'prelist_label': '',
            'prelist_source': '',
            'prelist_id_l2': '',
            'prelist_value': '',
            'prelist_idsbr': '',
            'prelist_id_l1': ''
        })
        new_rows.append(base_dict)

print("Constructing dataframe...")
new_df = pd.DataFrame(new_rows)

print("Saving to CSV...")
new_df.to_csv(output_path, sep=';', index=False)
print(f"Saved successfully to {output_path}. Total rows: {len(new_df)}")
