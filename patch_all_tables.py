import pandas as pd
import json
import re
import glob

excel_file = max(glob.glob('Rekap Progress Petugas*.xlsx'))

print("Loading Excel data...")
df = pd.read_excel(excel_file)
df_p = df[df['pencacah_email'].notna() & (df['pencacah_email'] != '')]

# Prepare data
progress_patch = {}
region_patch = {}
for _, row in df_p.iterrows():
    email = str(row['pencacah_email']).strip().lower()
    reg_code = str(row['level_5_full_code']).replace(".0", "")
    
    if email not in progress_patch:
        progress_patch[email] = {
            "target": 0,
            "submitted_pencacah": 0,
            "submitted_respondent": 0,
            "approved": 0,
            "rejected": 0,
            "draft": 0,
            "open": 0,
            "sls_details": {}
        }
        region_patch[email] = []
        
    if reg_code not in region_patch[email]:
        region_patch[email].append(reg_code)
    
    # Increase target count for this sls
    progress_patch[email]['target'] += 1
    progress_patch[email]['open'] += 1

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
            prog_map['Pencacah'][email] = data
            added += 1
            
    print(f"Added {added} enumerators to PETUGAS_PROGRESS_MAP")
    
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
            # Merge missing regions
            for r in regs:
                if r not in reg_map[email]:
                    reg_map[email].append(r)
            
    print(f"Added regions for {added} enumerators to PETUGAS_REGION_MAP")
    
    new_reg_json = json.dumps(reg_map, indent=4, ensure_ascii=False)
    content_reg = content_reg[:match.start(1)] + new_reg_json + content_reg[match.end(1):]
    with open('petugas_region_map.js', 'w', encoding='utf-8') as f:
        f.write(content_reg)
