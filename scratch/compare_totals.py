import pandas as pd
import json
import re
import os

base_dir = '/Users/jihanmaisaroh/scrap_fasih'
js_file = os.path.join(base_dir, 'data_hilang_keluarga.js')
excel_file = os.path.join(base_dir, 'New 25 Agustus', 'Total_keluarga_yang_tidak_ditemukan_dan_tidak_ada_padanannya per kab kot.xlsx')

# 1. Read JS data
with open(js_file, 'r', encoding='utf-8') as f:
    js_content = f.read()

# Strip "window.dataHilangKeluarga = " and ";"
json_str = js_content.replace('window.dataHilangKeluarga = ', '').strip()
if json_str.endswith(';'):
    json_str = json_str[:-1]

data_keluarga = json.loads(json_str)
print(f"Total rows in JS data: {len(data_keluarga)}")

# Count by kab
js_counts = {}
for row in data_keluarga:
    kab = str(row.get('kab', 'Unknown')).strip().upper()
    js_counts[kab] = js_counts.get(kab, 0) + 1

print("\n--- Counts in Web Data (JS) ---")
for k, v in sorted(js_counts.items()):
    print(f"{k}: {v}")

print("\n=====================================\n")

# 2. Read Excel data
df = pd.read_excel(excel_file)
print(f"Excel Columns: {list(df.columns)}")
print(df.head(20).to_string())

print("\n--- Comparison ---")
# Wait, let's see what the excel columns are first before comparing
