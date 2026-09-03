import os
import re
import json
import pandas as pd

BASE_DIR = '/Users/jihanmaisaroh/scrap_fasih'
F_PROGRES = os.path.join(BASE_DIR, 'rekap_progress_petugas_03_09.xlsx')

print("Membaca data progres dari:", F_PROGRES)
df = pd.read_excel(F_PROGRES, dtype=str)
print(f"-> {len(df):,} baris data progres petugas dibaca")

numeric_cols = [
    'open', 'draft', 'submitted_respondent', 'submitted_by_pencacah',
    'edited_by_pengawas', 'rejected_by_pengawas', 'approved_by_pengawas',
    'revoked_by_pengawas', 'edited_by_admin_kabupaten',
    'rejected_by_admin_kabupaten', 'revoked_by_admin_kabupaten',
    'completed_by_admin_kabupaten'
]
for c in numeric_cols:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0).astype(int)

df_p = df[df['pencacah_email'].notna() & (df['pencacah_email'].str.strip() != '')]

progress_patch = {}
region_patch = {}

for _, row in df_p.iterrows():
    email = str(row['pencacah_email']).strip().lower()
    reg_code = str(row['level_5_full_code']).replace('.0', '').strip()

    if email not in progress_patch:
        progress_patch[email] = {
            'target': 0, 'submitted_pencacah': 0, 'submitted_respondent': 0,
            'approved': 0, 'rejected': 0, 'draft': 0, 'open': 0, 'revoked': 0,
            'edited_pengawas': 0, 'edited_admin': 0, 'completed_admin': 0,
            'sls_details': {}
        }
        region_patch[email] = []

    if reg_code not in region_patch[email]:
        region_patch[email].append(reg_code)

    def g(col):
        return int(row[col]) if col in row.index and str(row[col]).strip() not in ('', 'nan') else 0

    progress_patch[email]['target'] += (
        g('open') + g('draft') + g('submitted_respondent') +
        g('submitted_by_pencacah') + g('edited_by_pengawas') +
        g('rejected_by_pengawas') + g('approved_by_pengawas') +
        g('revoked_by_pengawas') + g('edited_by_admin_kabupaten') +
        g('rejected_by_admin_kabupaten') + g('revoked_by_admin_kabupaten') +
        g('completed_by_admin_kabupaten')
    )
    progress_patch[email]['open']                 += g('open')
    progress_patch[email]['draft']                += g('draft')
    progress_patch[email]['submitted_respondent'] += g('submitted_respondent')
    progress_patch[email]['submitted_pencacah']   += g('submitted_by_pencacah')
    progress_patch[email]['approved']             += g('approved_by_pengawas')
    progress_patch[email]['rejected']             += g('rejected_by_pengawas') + g('rejected_by_admin_kabupaten')
    progress_patch[email]['revoked']              += g('revoked_by_pengawas')
    progress_patch[email]['edited_pengawas']      += g('edited_by_pengawas')
    progress_patch[email]['edited_admin']         += g('edited_by_admin_kabupaten')
    progress_patch[email]['completed_admin']      += g('completed_by_admin_kabupaten')

prog_path = os.path.join(BASE_DIR, 'fast_petugas_progress.js')
with open(prog_path, 'r', encoding='utf-8') as f:
    content_prog = f.read()

match = re.search(r'window\.PETUGAS_PROGRESS_MAP\s*=\s*(\{.*?\});', content_prog, re.DOTALL)
if match:
    prog_map = json.loads(match.group(1))
    if 'Pencacah' not in prog_map:
        prog_map['Pencacah'] = {}

    added = updated = 0
    for email, data in progress_patch.items():
        existing = prog_map['Pencacah'].get(email, {})
        data['sls_details'] = existing.get('sls_details', {})
        if email not in prog_map['Pencacah']:
            added += 1
        else:
            updated += 1
        prog_map['Pencacah'][email] = data

    new_json = json.dumps(prog_map, indent=4, ensure_ascii=False)
    content_prog = content_prog[:match.start(1)] + new_json + content_prog[match.end(1):]
    with open(prog_path, 'w', encoding='utf-8') as f:
        f.write(content_prog)
    print(f"OK fast_petugas_progress.js: +{added} baru, ~{updated} diupdate")

reg_path = os.path.join(BASE_DIR, 'petugas_region_map.js')
with open(reg_path, 'r', encoding='utf-8') as f:
    content_reg = f.read()

match_reg = re.search(r'window\.PETUGAS_REGION_MAP\s*=\s*(\{.*?\});', content_reg, re.DOTALL)
if match_reg:
    reg_map = json.loads(match_reg.group(1))
    added = 0
    for email, regs in region_patch.items():
        if email not in reg_map:
            reg_map[email] = regs
            added += 1
        else:
            for r in regs:
                if r not in reg_map[email]:
                    reg_map[email].append(r)
    new_json_reg = json.dumps(reg_map, indent=4, ensure_ascii=False)
    content_reg = content_reg[:match_reg.start(1)] + new_json_reg + content_reg[match_reg.end(1):]
    with open(reg_path, 'w', encoding='utf-8') as f:
        f.write(content_reg)
    print(f"OK petugas_region_map.js: +{added} baru/update")

print("Update selesai!")
