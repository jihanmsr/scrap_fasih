import pandas as pd
import json
import re
import csv
import glob
import os

excel_file = "/Users/jihanmaisaroh/scrap_fasih/update_26/rekap_progress_petugas (2).xlsx"
print(f"Reading {excel_file}...")
df = pd.read_excel(excel_file)

# 1. Generate fast_petugas_all_2026-08-26.csv
csv_file = "fast_petugas_all_2026-08-26.csv"
status_cols = [
    'open', 'draft', 'submitted_by_pencacah', 'submitted_respondent',
    'approved_by_pengawas', 'rejected_by_pengawas', 'revoked_by_pengawas',
    'edited_by_pengawas', 'edited_by_admin_kabupaten', 'rejected_by_admin_kabupaten',
    'completed_by_admin_kabupaten'
]
all_cols_for_target = status_cols + ['revoked_by_admin_kabupaten']

for c in all_cols_for_target:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0).astype(int)
    else:
        df[c] = 0

with open(csv_file, mode='w', newline='', encoding='utf-8') as f_csv:
    writer = csv.writer(f_csv)
    writer.writerow([
        "Email", "Role", "Total Target", "OPEN", "DRAFT", 
        "SUBMITTED BY Pencacah", "SUBMITTED RESPONDENT", 
        "APPROVED BY Pengawas", "REJECTED BY Pengawas", 
        "REVOKED BY Pengawas", "EDITED BY Pengawas", 
        "EDITED BY Admin Kabupaten", "REJECTED BY Admin Kabupaten", 
        "COMPLETED BY Admin Kabupaten"
    ])
    
    for _, row in df.iterrows():
        email = str(row.get('pencacah_email', '')).strip()
        if not email or email.lower() == 'nan':
            continue
        
        total_target = sum(row.get(col, 0) for col in all_cols_for_target)
        
        writer.writerow([
            email,
            "Pencacah",
            total_target,
            row.get('open', 0),
            row.get('draft', 0),
            row.get('submitted_by_pencacah', 0),
            row.get('submitted_respondent', 0),
            row.get('approved_by_pengawas', 0),
            row.get('rejected_by_pengawas', 0),
            row.get('revoked_by_pengawas', 0),
            row.get('edited_by_pengawas', 0),
            row.get('edited_by_admin_kabupaten', 0),
            row.get('rejected_by_admin_kabupaten', 0),
            row.get('completed_by_admin_kabupaten', 0)
        ])

print(f"Generated {csv_file}")

# 2. Prepare aggregated data for fast_petugas_progress.js and petugas_region_map.js
df_p = df[df['pencacah_email'].notna() & (df['pencacah_email'] != '')]

progress_patch = {}
region_patch = {}

for _, row in df_p.iterrows():
    email = str(row['pencacah_email']).strip().lower()
    reg_code = str(row['level_5_full_code']).replace(".0", "").strip()
    
    if email not in progress_patch:
        progress_patch[email] = {
            "target": 0, "submitted_pencacah": 0, "submitted_respondent": 0,
            "approved": 0, "rejected": 0, "draft": 0, "open": 0, "revoked": 0,
            "edited_pengawas": 0, "edited_admin": 0, "completed_admin": 0,
            "sls_details": {}
        }
        region_patch[email] = []
        
    if reg_code and reg_code not in region_patch[email]:
        region_patch[email].append(reg_code)
    
    progress_patch[email]['target'] += sum(row.get(col, 0) for col in all_cols_for_target)
    progress_patch[email]['open'] += row.get('open', 0)
    progress_patch[email]['draft'] += row.get('draft', 0)
    progress_patch[email]['submitted_respondent'] += row.get('submitted_respondent', 0)
    progress_patch[email]['submitted_pencacah'] += row.get('submitted_by_pencacah', 0)
    progress_patch[email]['approved'] += row.get('approved_by_pengawas', 0)
    progress_patch[email]['rejected'] += row.get('rejected_by_pengawas', 0) + row.get('rejected_by_admin_kabupaten', 0)
    progress_patch[email]['revoked'] += row.get('revoked_by_pengawas', 0)
    progress_patch[email]['edited_pengawas'] += row.get('edited_by_pengawas', 0)
    progress_patch[email]['edited_admin'] += row.get('edited_by_admin_kabupaten', 0)
    progress_patch[email]['completed_admin'] += row.get('completed_by_admin_kabupaten', 0)

# Patch fast_petugas_progress.js
with open('fast_petugas_progress.js', 'r', encoding='utf-8') as f:
    content_prog = f.read()

match = re.search(r'window\.PETUGAS_PROGRESS_MAP\s*=\s*(\{.*?\});', content_prog, re.DOTALL)
if match:
    prog_map = json.loads(match.group(1))
    if 'Pencacah' not in prog_map:
        prog_map['Pencacah'] = {}
        
    added = 0
    for email, data in progress_patch.items():
        if email not in prog_map['Pencacah']:
            added += 1
        
        existing_data = prog_map['Pencacah'].get(email, {})
        data['sls_details'] = existing_data.get('sls_details', {})
        prog_map['Pencacah'][email] = data
            
    print(f"Added {added} new enumerators and updated stats in PETUGAS_PROGRESS_MAP")
    
    new_prog_json = json.dumps(prog_map, indent=4, ensure_ascii=False)
    content_prog = content_prog[:match.start(1)] + new_prog_json + content_prog[match.end(1):]
    with open('fast_petugas_progress.js', 'w', encoding='utf-8') as f:
        f.write(content_prog)

# Patch petugas_region_map.js
with open('petugas_region_map.js', 'r', encoding='utf-8') as f:
    content_reg = f.read()

match = re.search(r'window\.PETUGAS_REGION_MAP\s*=\s*(\{.*?\});', content_reg, re.DOTALL)
if match:
    reg_map = json.loads(match.group(1))
    
    added = 0
    for email, regs in region_patch.items():
        if email not in reg_map:
            reg_map[email] = regs
            added += 1
        else:
            for r in regs:
                if r not in reg_map[email]:
                    reg_map[email].append(r)
            
    print(f"Added regions for {added} enumerators to PETUGAS_REGION_MAP")
    
    new_reg_json = json.dumps(reg_map, indent=4, ensure_ascii=False)
    content_reg = content_reg[:match.start(1)] + new_reg_json + content_reg[match.end(1):]
    with open('petugas_region_map.js', 'w', encoding='utf-8') as f:
        f.write(content_reg)

print("Progress data patched successfully!")
