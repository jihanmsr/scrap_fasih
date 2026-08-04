import pandas as pd
import json
import re
import glob
import os

excel_files = glob.glob('Rekap Progress Petugas*.xlsx')
if not excel_files:
    print("No Excel files found.")
    exit(1)
latest_excel = max(excel_files, key=os.path.getctime)

print(f"Loading Excel data from {latest_excel}...")
df = pd.read_excel(latest_excel)
df_p = df[df['pencacah_email'].notna() & (df['pencacah_email'] != '')]

excel_petugas_regions = {}
for _, row in df_p.iterrows():
    email = str(row['pencacah_email']).strip()
    if email not in excel_petugas_regions:
        excel_petugas_regions[email] = []
    reg_code = str(row['level_5_full_code']).replace(".0", "")
    if not any(r['regionCode'] == reg_code for r in excel_petugas_regions[email]):
        excel_petugas_regions[email].append({
            "regionCode": reg_code,
            "regionName": "-"
        })

for js_file in ['assign_data.js', 'fast_master_assign_data.js']:
    print(f"Patching {js_file}...")
    if not os.path.exists(js_file):
        continue
    with open(js_file, 'r', encoding='utf-8') as f:
        content = f.read()

    match_umum = re.search(r'window\.(?:ASSIGN_DATA_UMUM|PETUGAS_DATA_UMUM)\s*=\s*(\[.*?\]);', content, re.DOTALL)
    if match_umum:
        data_umum = json.loads(match_umum.group(1))
        existing_emails = {p.get('email', p.get('username')) for p in data_umum}
        
        added_count = 0
        for email, regions in excel_petugas_regions.items():
            if email not in existing_emails:
                data_umum.append({
                    "username": email,
                    "email": email,
                    "fullname": "-",
                    "roleName": "Pencacah",
                    "regions": regions,
                    "totalRegions": len(regions)
                })
                added_count += 1
                
        print(f"Added {added_count} missing enumerators to {js_file}")
        
        new_umum_json = json.dumps(data_umum, indent=4, ensure_ascii=False)
        content = content[:match_umum.start(1)] + new_umum_json + content[match_umum.end(1):]
        
        with open(js_file, 'w', encoding='utf-8') as f:
            f.write(content)
    else:
        print(f"Failed to find variable in {js_file}")
