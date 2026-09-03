import os
import pandas as pd
import json

BASE_DIR = '/Users/jihanmaisaroh/scrap_fasih'
F_PROGRES = os.path.join(BASE_DIR, 'rekap_progress_petugas_03_09.xlsx')
F_MUATAN = os.path.join(BASE_DIR, 'muatan', 'muatan_sls_72 2.xlsx')
if not os.path.exists(F_MUATAN):
    F_MUATAN = os.path.join(BASE_DIR, 'muatan_sls_72.xlsx')

KAB_MAP = {
    '7201': 'BANGGAI KEPULAUAN', '7202': 'BANGGAI', '7203': 'MOROWALI',
    '7204': 'POSO', '7205': 'DONGGALA', '7206': 'TOLI-TOLI', '7207': 'BUOL',
    '7208': 'PARIGI MOUTONG', '7209': 'TOJO UNA-UNA', '7210': 'SIGI',
    '7211': 'BANGGAI LAUT', '7212': 'MOROWALI UTARA', '7271': 'PALU'
}

print("Loading muatan lookup...")
df_muatan = pd.read_excel(F_MUATAN)
muatan_map = {}
for _, row in df_muatan.iterrows():
    raw_id = str(row['idsubsls_25_2']).split('.')[0].strip()
    if raw_id and raw_id != 'nan':
        subsls_id = raw_id.zfill(16)
        muatan_map[subsls_id] = {
            'nmkab': str(row.get('nmkab', '')).strip(),
            'nmkec': str(row.get('nmkec', '')).strip(),
            'nmdesa': str(row.get('nmdesa', '')).strip(),
            'nmsls': str(row.get('nmsls', '')).strip()
        }

print("Loading progress data...")
df_prog = pd.read_excel(F_PROGRES)
df_prog['level_5_full_code'] = df_prog['level_5_full_code'].astype(str).str.split('.').str[0].str.zfill(14)
df_prog['level_6_code'] = df_prog['level_6_code'].astype(str).str.split('.').str[0].str.zfill(2)
df_prog['id_subsls'] = df_prog['level_5_full_code'] + df_prog['level_6_code']

status_cols = ['open', 'draft', 'submitted_respondent', 'submitted_by_pencacah', 
               'edited_by_pengawas', 'rejected_by_pengawas', 'approved_by_pengawas', 
               'revoked_by_pengawas', 'edited_by_admin_kabupaten', 'rejected_by_admin_kabupaten', 
               'revoked_by_admin_kabupaten', 'completed_by_admin_kabupaten']

for c in status_cols:
    if c in df_prog.columns:
        df_prog[c] = pd.to_numeric(df_prog[c], errors='coerce').fillna(0).astype(int)

subsls_dict = {}
for _, row in df_prog.iterrows():
    sub_id = row['id_subsls']
    if len(sub_id) != 16: continue
    
    if sub_id not in subsls_dict:
        m = muatan_map.get(sub_id, {})
        subsls_dict[sub_id] = {
            'id': sub_id,
            'sls_code': sub_id[:14],
            'kab_code': sub_id[:4],
            'kec_code': sub_id[:7],
            'desa_code': sub_id[:10],
            'nmkab': m.get('nmkab', KAB_MAP.get(sub_id[:4], 'Unknown')),
            'nmkec': m.get('nmkec', ''),
            'nmdesa': m.get('nmdesa', ''),
            'nmsls': m.get('nmsls', ''),
            'pencacah': str(row.get('pencacah_email', '')).strip(),
            'pengawas': str(row.get('pengawas_email', '')).strip(),
            'open': 0, 'draft': 0, 'submitted_respondent': 0, 'submitted_pencacah': 0,
            'edited_pengawas': 0, 'rejected_pengawas': 0, 'approved': 0, 'revoked_pengawas': 0,
            'edited_admin': 0, 'rejected_admin': 0, 'revoked_admin': 0, 'completed_admin': 0,
            'belum': 0, 'selesai': 0, 'total': 0, 'pct': 0.0
        }
    
    sd = subsls_dict[sub_id]
    sd['open'] += int(row.get('open', 0))
    sd['draft'] += int(row.get('draft', 0))
    sd['submitted_respondent'] += int(row.get('submitted_respondent', 0))
    sd['submitted_pencacah'] += int(row.get('submitted_by_pencacah', 0))
    sd['edited_pengawas'] += int(row.get('edited_by_pengawas', 0))
    sd['rejected_pengawas'] += int(row.get('rejected_by_pengawas', 0))
    sd['approved'] += int(row.get('approved_by_pengawas', 0))
    sd['revoked_pengawas'] += int(row.get('revoked_by_pengawas', 0))
    sd['edited_admin'] += int(row.get('edited_by_admin_kabupaten', 0))
    sd['rejected_admin'] += int(row.get('rejected_by_admin_kabupaten', 0))
    sd['revoked_admin'] += int(row.get('revoked_by_admin_kabupaten', 0))
    sd['completed_admin'] += int(row.get('completed_by_admin_kabupaten', 0))

for sd in subsls_dict.values():
    sd['belum'] = sd['open'] + sd['draft']
    sd['selesai'] = (sd['submitted_respondent'] + sd['submitted_pencacah'] + sd['edited_pengawas'] + 
                     sd['rejected_pengawas'] + sd['approved'] + sd['revoked_pengawas'] + 
                     sd['edited_admin'] + sd['rejected_admin'] + sd['revoked_admin'] + sd['completed_admin'])
    sd['total'] = sd['belum'] + sd['selesai']
    sd['pct'] = round((sd['selesai'] / sd['total'] * 100), 1) if sd['total'] > 0 else 0.0

kab_map = {}
kec_map = {}
desa_map = {}

for s in subsls_dict.values():
    k_code = s['kab_code']
    kc_code = s['kec_code']
    d_code = s['desa_code']
    
    if k_code not in kab_map: kab_map[k_code] = {'code': k_code, 'name': s['nmkab'], 'open': 0, 'draft': 0, 'belum': 0, 'submit_ppl': 0, 'approved': 0, 'completed': 0, 'selesai': 0, 'total': 0, 'pct': 0, 'kec_count': 0, 'desa_count': 0, 'sls_count': 0}
    if kc_code not in kec_map: kec_map[kc_code] = {'code': kc_code, 'kab_code': k_code, 'name': s['nmkec'], 'open': 0, 'draft': 0, 'belum': 0, 'submit_ppl': 0, 'approved': 0, 'completed': 0, 'selesai': 0, 'total': 0, 'pct': 0, 'desa_count': 0, 'sls_count': 0}
    if d_code not in desa_map: desa_map[d_code] = {'code': d_code, 'kec_code': kc_code, 'kab_code': k_code, 'name': s['nmdesa'], 'open': 0, 'draft': 0, 'belum': 0, 'submit_ppl': 0, 'approved': 0, 'completed': 0, 'selesai': 0, 'total': 0, 'pct': 0, 'sls_count': 0}
    
    for kb in [kab_map[k_code], kec_map[kc_code], desa_map[d_code]]:
        kb['total'] += s['total']
        kb['open'] += s['open']
        kb['draft'] += s['draft']
        kb['belum'] += s['belum']
        kb['submit_ppl'] += s['submitted_pencacah']
        kb['approved'] += s['approved']
        kb['completed'] += s['completed_admin']
        kb['selesai'] += s['selesai']
        kb['sls_count'] += 1

for kb in kab_map.values():
    kb['pct'] = round((kb['selesai'] / kb['total'] * 100), 1) if kb['total'] > 0 else 0.0
    kb['kec_count'] = len([kc for kc in kec_map.values() if kc['kab_code'] == kb['code']])
    kb['desa_count'] = len([d for d in desa_map.values() if d['kab_code'] == kb['code']])

for kc in kec_map.values():
    kc['pct'] = round((kc['selesai'] / kc['total'] * 100), 1) if kc['total'] > 0 else 0.0
    kc['desa_count'] = len([d for d in desa_map.values() if d['kec_code'] == kc['code']])

for d in desa_map.values():
    d['pct'] = round((d['selesai'] / d['total'] * 100), 1) if d['total'] > 0 else 0.0

kab_list = sorted(list(kab_map.values()), key=lambda x: x['code'])
kec_by_kab = {}
for kc in kec_map.values():
    k_code = kc['kab_code']
    if k_code not in kec_by_kab: kec_by_kab[k_code] = []
    kec_by_kab[k_code].append(kc)

desa_by_kec = {}
for d in desa_map.values():
    kc_code = d['kec_code']
    if kc_code not in desa_by_kec: desa_by_kec[kc_code] = []
    desa_by_kec[kc_code].append(d)

sls_by_desa = {}
for s in subsls_dict.values():
    d_code = s['desa_code']
    if d_code not in sls_by_desa: sls_by_desa[d_code] = []
    sls_by_desa[d_code].append(s)

output_data = {
    'kab': kab_list,
    'kec_by_kab': kec_by_kab,
    'desa_by_kec': desa_by_kec,
    'sls_by_desa': sls_by_desa
}

out_path = os.path.join(BASE_DIR, 'rekap_status_sls.js')
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(f"window.REKAP_STATUS_DATA = {json.dumps(output_data, ensure_ascii=False)};\n")

print("OK rekap_status_sls.js diperbarui.")
