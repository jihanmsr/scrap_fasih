import os
import pandas as pd
import json

base_dir = '/Users/jihanmaisaroh/scrap_fasih'
csv_file = os.path.join(base_dir, 'Usaha_nonaktif_vs_keluarga_ditemukan__25 Agus.csv')
output_js = os.path.join(base_dir, 'data_usaha_nonaktif.js')

print("Reading CSV file...")
df = pd.read_csv(csv_file)
# Convert NaN to None
df = df.where(pd.notnull(df), None)

print(f"Total rows: {len(df)}")

print(f"Writing to {output_js}...")
with open(output_js, 'w', encoding='utf-8') as f:
    f.write('window.dataUsahaNonaktif = ')
    json.dump(df.to_dict(orient='records'), f, ensure_ascii=False)
    f.write(';\n')

print("Done!")
