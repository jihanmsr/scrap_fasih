import pandas as pd
import glob
import csv
import json

excel_file = max(glob.glob('Rekap Progress Petugas*.xlsx'))
date_str = "2026-08-04"
csv_file = f"fast_petugas_all_{date_str}.csv"

print(f"Loading {excel_file} to create {csv_file}...")
df = pd.read_excel(excel_file)
df_p = df[df['pencacah_email'].notna() & (df['pencacah_email'] != '')]

# Prepare data aggregation
# Columns: "Email", "Role", "Region Code", "Total Target", "OPEN", "DRAFT", "SUBMITTED BY Pencacah", "SUBMITTED RESPONDENT", "APPROVED BY Pengawas", "REJECTED BY Pengawas", "REVOKED BY Pengawas", "EDITED BY Pengawas", "EDITED BY Admin Kabupaten", "REJECTED BY Admin Kabupaten", "COMPLETED BY Admin Kabupaten"

pencacah_map = {}
for _, row in df_p.iterrows():
    email = str(row['pencacah_email']).strip().lower()
    reg = str(row['level_5_full_code']).replace('.0', '')
    
    if email not in pencacah_map:
        pencacah_map[email] = {
            "Role": "Pencacah", "Region Code": set(), "Total Target": 0, "OPEN": 0, "DRAFT": 0, "SUBMITTED BY Pencacah": 0,
            "SUBMITTED RESPONDENT": 0, "APPROVED BY Pengawas": 0, "REJECTED BY Pengawas": 0, "REVOKED BY Pengawas": 0,
            "EDITED BY Pengawas": 0, "EDITED BY Admin Kabupaten": 0, "REJECTED BY Admin Kabupaten": 0, "COMPLETED BY Admin Kabupaten": 0
        }
    
    p = pencacah_map[email]
    p["Region Code"].add(reg)
    p["Total Target"] += 1
    
    status = str(row.get('status', '')).strip().upper()
    if status == 'OPEN': p["OPEN"] += 1
    elif status == 'DRAFT': p["DRAFT"] += 1
    elif status == 'SUBMITTED': p["SUBMITTED BY Pencacah"] += 1
    elif status == 'SUBMITTED_RESPONDENT': p["SUBMITTED RESPONDENT"] += 1
    elif status == 'APPROVED': p["APPROVED BY Pengawas"] += 1
    elif status == 'REJECTED': p["REJECTED BY Pengawas"] += 1
    elif status == 'REVOKED': p["REVOKED BY Pengawas"] += 1
    elif status == 'EDITED_PENGAWAS': p["EDITED BY Pengawas"] += 1
    elif status == 'EDITED_ADMIN': p["EDITED BY Admin Kabupaten"] += 1
    elif status == 'REJECTED_ADMIN': p["REJECTED BY Admin Kabupaten"] += 1
    elif status == 'COMPLETED': p["COMPLETED BY Admin Kabupaten"] += 1
    else: p["OPEN"] += 1 # Default

# Also Pengawas
df_peng = df[df['pengawas_email'].notna() & (df['pengawas_email'] != '')]
for _, row in df_peng.iterrows():
    email = str(row['pengawas_email']).strip().lower()
    reg = str(row['level_5_full_code']).replace('.0', '')
    
    if email not in pencacah_map:
        pencacah_map[email] = {
            "Role": "Pengawas", "Region Code": set(), "Total Target": 0, "OPEN": 0, "DRAFT": 0, "SUBMITTED BY Pencacah": 0,
            "SUBMITTED RESPONDENT": 0, "APPROVED BY Pengawas": 0, "REJECTED BY Pengawas": 0, "REVOKED BY Pengawas": 0,
            "EDITED BY Pengawas": 0, "EDITED BY Admin Kabupaten": 0, "REJECTED BY Admin Kabupaten": 0, "COMPLETED BY Admin Kabupaten": 0
        }
        
    p = pencacah_map[email]
    p["Region Code"].add(reg)
    p["Total Target"] += 1
    
    status = str(row.get('status', '')).strip().upper()
    if status == 'OPEN': p["OPEN"] += 1
    elif status == 'DRAFT': p["DRAFT"] += 1
    elif status == 'SUBMITTED': p["SUBMITTED BY Pencacah"] += 1
    elif status == 'SUBMITTED_RESPONDENT': p["SUBMITTED RESPONDENT"] += 1
    elif status == 'APPROVED': p["APPROVED BY Pengawas"] += 1
    elif status == 'REJECTED': p["REJECTED BY Pengawas"] += 1
    elif status == 'REVOKED': p["REVOKED BY Pengawas"] += 1
    elif status == 'EDITED_PENGAWAS': p["EDITED BY Pengawas"] += 1
    elif status == 'EDITED_ADMIN': p["EDITED BY Admin Kabupaten"] += 1
    elif status == 'REJECTED_ADMIN': p["REJECTED BY Admin Kabupaten"] += 1
    elif status == 'COMPLETED': p["COMPLETED BY Admin Kabupaten"] += 1
    else: p["OPEN"] += 1 # Default

with open(csv_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(["Email", "Role", "Region Code", "Total Target", "OPEN", "DRAFT", "SUBMITTED BY Pencacah", "SUBMITTED RESPONDENT", "APPROVED BY Pengawas", "REJECTED BY Pengawas", "REVOKED BY Pengawas", "EDITED BY Pengawas", "EDITED BY Admin Kabupaten", "REJECTED BY Admin Kabupaten", "COMPLETED BY Admin Kabupaten"])
    
    for email, p in pencacah_map.items():
        writer.writerow([
            email, p["Role"], "|".join(p["Region Code"]), p["Total Target"], p["OPEN"], p["DRAFT"], p["SUBMITTED BY Pencacah"],
            p["SUBMITTED RESPONDENT"], p["APPROVED BY Pengawas"], p["REJECTED BY Pengawas"], p["REVOKED BY Pengawas"],
            p["EDITED BY Pengawas"], p["EDITED BY Admin Kabupaten"], p["REJECTED BY Admin Kabupaten"], p["COMPLETED BY Admin Kabupaten"]
        ])

print(f"Created {csv_file}")
