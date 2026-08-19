import pandas as pd
import json
import re
import glob

print("Loading CSV data dari sqllab_rekap_progress_petugas_20260819T*.csv...")
files = glob.glob('/Users/jihanmaisaroh/scrap_fasih/sqllab_rekap_progress_petugas_20260819T*.csv')
dfs = [pd.read_csv(f, dtype=str) for f in files]
df = pd.concat(dfs, ignore_index=True)

for c in ['open', 'draft', 'submitted_respondent', 'submitted_by_pencacah', 
          'edited_by_pengawas', 'rejected_by_pengawas', 'approved_by_pengawas', 
          'revoked_by_pengawas', 'edited_by_admin_kabupaten', 'rejected_by_admin_kabupaten', 
          'revoked_by_admin_kabupaten', 'completed_by_admin_kabupaten']:
    df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0).astype(int)

df_p = df[df['pencacah_email'].notna() & (df['pencacah_email'] != '')]

# Prepare data
progress_patch = {}
region_patch = {}
for _, row in df_p.iterrows():
    email = str(row['pencacah_email']).strip().lower()
    reg_code = str(row['level_5_full_code']).replace(".0", "")
    
    if email not in progress_patch:
        progress_patch[email] = {
            "target": 0, "submitted_pencacah": 0, "submitted_respondent": 0,
            "approved": 0, "rejected": 0, "draft": 0, "open": 0, "revoked": 0,
            "edited_pengawas": 0, "edited_admin": 0, "completed_admin": 0,
            "sls_details": {}
        }
        region_patch[email] = []
        
    if reg_code not in region_patch[email]:
        region_patch[email].append(reg_code)
    
    progress_patch[email]['target'] += row.get('open', 0) + row.get('draft', 0) + row.get('submitted_respondent', 0) + row.get('submitted_by_pencacah', 0) + row.get('edited_by_pengawas', 0) + row.get('rejected_by_pengawas', 0) + row.get('approved_by_pengawas', 0) + row.get('revoked_by_pengawas', 0) + row.get('edited_by_admin_kabupaten', 0) + row.get('rejected_by_admin_kabupaten', 0) + row.get('revoked_by_admin_kabupaten', 0) + row.get('completed_by_admin_kabupaten', 0)
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

# 1. Patch fast_petugas_progress.js
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
            
    print(f"Added {added} new enumerators and updated stats for all in PETUGAS_PROGRESS_MAP")
    
    new_prog_json = json.dumps(prog_map, indent=4, ensure_ascii=False)
    content_prog = content_prog[:match.start(1)] + new_prog_json + content_prog[match.end(1):]
    with open('fast_petugas_progress.js', 'w', encoding='utf-8') as f:
        f.write(content_prog)

# 2. Patch petugas_region_map.js
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

