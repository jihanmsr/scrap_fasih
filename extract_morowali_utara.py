import csv
import json
import re
import pandas as pd

# 1. Load Region Map
with open('region_map_sulteng_full.json', 'r') as f:
    region_data = json.load(f)

# Build a lookup for Desa and Kecamatan
# key: 10-digit desa code, value: (kecamatan_name, desa_name)
region_lookup = {}
if '7212' in region_data['kabupaten']:
    kab_data = region_data['kabupaten']['7212']
    for kec_code, kec_data in kab_data['kecamatan'].items():
        kec_name = kec_data['kec_name']
        for desa_code, desa_data in kec_data['desa'].items():
            desa_name = desa_data['desa_name']
            region_lookup[desa_code] = (kec_name, desa_name)

# 2. Load Petugas Region Map
with open('petugas_region_map.js', 'r') as f:
    content = f.read()
    # It might be an export default or just an object
    match = re.search(r'(\{.*\})', content, re.DOTALL)
    if match:
        petugas_map = json.loads(match.group(1))
    else:
        petugas_map = {}

# 3. Load CSV and build data
output_data = []

with open('rekap_progres_petugas_2026-07-20.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        email = row.get('Email / Username')
        if email and email in petugas_map:
            # Check if assigned to Morowali Utara (7212)
            sls_list = petugas_map[email]
            mu_sls_list = [s for s in sls_list if s.startswith('7212')]
            if mu_sls_list:
                for sls_full in mu_sls_list:
                    desa_code = sls_full[:10]
                    sls_code = sls_full[10:14]
                    subsls = sls_full[14:16]
                    
                    kec_name, desa_name = region_lookup.get(desa_code, ("-", "-"))
                    
                    output_data.append({
                        "Nama Petugas": row.get('Nama Petugas'),
                        "Email / Username": email,
                        "Role": row.get('Role'),
                        "Kecamatan": kec_name,
                        "Desa": desa_name,
                        "Kode SLS": sls_code,
                        "Sub SLS": subsls,
                        "Full SLS Code": sls_full,
                        "% Capaian": row.get('% Capaian'),
                        "Total Target": row.get('Total Target'),
                        "Selesai (Total)": row.get('Selesai (Total)')
                    })

df = pd.DataFrame(output_data)
if not df.empty:
    df.to_excel('Petugas_Pencacah_Morowali_Utara.xlsx', index=False)
    print(f"Exported {len(df)} rows to Petugas_Pencacah_Morowali_Utara.xlsx")
else:
    print("No data found for Morowali Utara.")
