import csv
import json
import re
import pandas as pd

# 1. Load Region Map
with open('region_map_sulteng_full.json', 'r') as f:
    region_data = json.load(f)

# Build a lookup for Desa and Kecamatan based on 10-digit desa_code
# key: 10-digit desa code, value: (kecamatan_name, desa_name)
region_lookup = {}
for kab_code, kab_data in region_data.get('kabupaten', {}).items():
    for kec_code, kec_data in kab_data.get('kecamatan', {}).items():
        kec_name = kec_data['kec_name']
        for desa_code, desa_data in kec_data.get('desa', {}).items():
            desa_name = desa_data['desa_name']
            region_lookup[desa_code] = (kec_name, desa_name)

# 2. Load Petugas Region Map
with open('petugas_region_map.js', 'r') as f:
    content = f.read()
    match = re.search(r'(\{.*\})', content, re.DOTALL)
    if match:
        petugas_map = json.loads(match.group(1))
    else:
        petugas_map = {}

# 3. Process CSV files
files_to_process = [
    'rekap_progres_petugas_2026-07-20.csv',
    'rekap_progres_petugas_2026-07-20 (1).csv'
]

all_rows = []
for file_name in files_to_process:
    try:
        with open(file_name, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                email = row.get('Email / Username')
                kec_set = set()
                desa_set = set()
                
                if email and email in petugas_map:
                    sls_list = petugas_map[email]
                    for sls_full in sls_list:
                        desa_code = sls_full[:10]
                        if desa_code in region_lookup:
                            kec_name, desa_name = region_lookup[desa_code]
                            if kec_name != "-": kec_set.add(kec_name)
                            if desa_name != "-": desa_set.add(desa_name)
                
                row['Kecamatan'] = ", ".join(sorted(kec_set)) if kec_set else "-"
                row['Desa'] = ", ".join(sorted(desa_set)) if desa_set else "-"
                all_rows.append(row)
    except FileNotFoundError:
        print(f"File not found: {file_name}")

if all_rows:
    df = pd.DataFrame(all_rows)
    # Reorder columns to put Kecamatan and Desa after Role (or Email)
    cols = list(df.columns)
    # Move Kecamatan and Desa to index 3 and 4
    for c in ['Kecamatan', 'Desa']:
        cols.remove(c)
    cols.insert(3, 'Kecamatan')
    cols.insert(4, 'Desa')
    df = df[cols]
    
    output_filename = 'Rekap_Progres_Gabungan_Wilayah.xlsx'
    df.to_excel(output_filename, index=False)
    print(f"Successfully combined {len(df)} rows into {output_filename}")
else:
    print("No data to combine.")
