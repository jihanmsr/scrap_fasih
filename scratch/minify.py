import json
import os
import math

file_path = '/Users/jihanmaisaroh/scrap_fasih/data_hilang_keluarga.js'

print("Loading...")
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

json_str = content.replace('window.dataHilangKeluarga = ', '').strip()
if json_str.endswith(';'):
    json_str = json_str[:-1]

json_str = json_str.replace(': NaN', ': null')

data = json.loads(json_str)

print("Minifying...")
# Remove null values to save space
for item in data:
    keys_to_delete = []
    for k, v in item.items():
        if v is None or v == 'nan' or v == '' or v == '-':
            keys_to_delete.append(k)
    for k in keys_to_delete:
        del item[k]

with open(file_path, 'w', encoding='utf-8') as f:
    f.write('window.dataHilangKeluarga=')
    json.dump(data, f, separators=(',', ':'), ensure_ascii=False)
    f.write(';')

print(f"Done! New size: {os.path.getsize(file_path) / (1024*1024):.2f} MB")
