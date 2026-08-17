import pandas as pd
import json
import sys

file_path = sys.argv[1] if len(sys.argv) > 1 else '/Users/jihanmaisaroh/scrap_fasih/SubSLS_Open.xlsx'

if file_path.endswith('.csv'):
    df = pd.read_csv(file_path, sep=",")
else:
    df = pd.read_excel(file_path)

# Convert NaN/float issues
df = df.fillna('')

# Ensure data types are correct to match old format
data_list = []
for idx, row in df.iterrows():
    item = {
        "kode_kab": int(row['kode_kab']) if str(row['kode_kab']).isdigit() else row['kode_kab'],
        "kabupaten": str(row['kabupaten']),
        "kode_kecamatan": int(row['kode_kecamatan']) if str(row['kode_kecamatan']).isdigit() else row['kode_kecamatan'],
        "kecamatan": str(row['kecamatan']),
        "kode_desa": int(row['kode_desa']) if str(row['kode_desa']).isdigit() else row['kode_desa'],
        "desa": str(row['desa']),
        "kode_sls": int(row['kode_sls']) if str(row['kode_sls']).isdigit() else row['kode_sls'],
        "sls": str(row['sls']),
        "kode_sub_sls": int(row['kode_sub_sls']) if str(row['kode_sub_sls']).isdigit() else row['kode_sub_sls'],
        "nama_sub_sls": str(row['nama_sub_sls']),
        "nama_petugas": str(row['nama_petugas']) if row['nama_petugas'] else None,
        "jumlah_prelist": int(row['jumlah_prelist']) if str(row['jumlah_prelist']).isdigit() else 0
    }
    data_list.append(item)

js_content = f"window.OPEN_SUBSLS_DATA = {json.dumps(data_list, ensure_ascii=False)};"

with open('/Users/jihanmaisaroh/scrap_fasih/open_subsls_data.js', 'w', encoding='utf-8') as f:
    f.write(js_content)
    
print(f"Successfully updated open_subsls_data.js with {len(data_list)} rows!")
