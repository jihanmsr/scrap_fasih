import os
import pandas as pd
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPDATE_DIR = os.path.join(BASE_DIR, 'update_1sept')
F_PROGRES = os.path.join(UPDATE_DIR, 'rekap_progress_petugas (5).xlsx')
F_MUATAN = os.path.join(BASE_DIR, 'muatan', 'muatan_sls_72 2.xlsx')
if not os.path.exists(F_MUATAN):
    F_MUATAN = os.path.join(BASE_DIR, 'muatan_sls_72.xlsx')

KAB_MAP = {
    '7201': 'BANGGAI KEPULAUAN', '7202': 'BANGGAI', '7203': 'MOROWALI',
    '7204': 'POSO', '7205': 'DONGGALA', '7206': 'TOLI-TOLI', '7207': 'BUOL',
    '7208': 'PARIGI MOUTONG', '7209': 'TOJO UNA-UNA', '7210': 'SIGI',
    '7211': 'BANGGAI LAUT', '7212': 'MOROWALI UTARA', '7271': 'KOTA PALU'
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

for col in status_cols:
    df_prog[col] = pd.to_numeric(df_prog[col], errors='coerce').fillna(0).astype(int)

# Aggregate per subsls
subsls_dict = {}
for _, row in df_prog.iterrows():
    sub_id = row['id_subsls']
    if sub_id not in subsls_dict:
        m_info = muatan_map.get(sub_id, {})
        subsls_dict[sub_id] = {
            'id': sub_id,
            'sls_code': row['level_5_full_code'],
            'kab_code': sub_id[:4],
            'kec_code': sub_id[:7],
            'desa_code': sub_id[:10],
            'nmkab': m_info.get('nmkab', KAB_MAP.get(sub_id[:4], '')),
            'nmkec': m_info.get('nmkec', ''),
            'nmdesa': m_info.get('nmdesa', ''),
            'nmsls': m_info.get('nmsls', ''),
            'pencacah': str(row.get('pencacah_email', '')).strip() if str(row.get('pencacah_email', '')) != 'nan' else '',
            'pengawas': str(row.get('pengawas_email', '')).strip() if str(row.get('pengawas_email', '')) != 'nan' else '',
            'open': 0, 'draft': 0, 'submitted_respondent': 0, 'submitted_pencacah': 0,
            'edited_pengawas': 0, 'rejected_pengawas': 0, 'approved': 0,
            'revoked_pengawas': 0, 'edited_admin': 0, 'rejected_admin': 0,
            'revoked_admin': 0, 'completed_admin': 0
        }
    
    s = subsls_dict[sub_id]
    s['open'] = max(s['open'], int(row['open']))
    s['draft'] = max(s['draft'], int(row['draft']))
    s['submitted_respondent'] = max(s['submitted_respondent'], int(row['submitted_respondent']))
    s['submitted_pencacah'] = max(s['submitted_pencacah'], int(row['submitted_by_pencacah']))
    s['edited_pengawas'] = max(s['edited_pengawas'], int(row['edited_by_pengawas']))
    s['rejected_pengawas'] = max(s['rejected_pengawas'], int(row['rejected_by_pengawas']))
    s['approved'] = max(s['approved'], int(row['approved_by_pengawas']))
    s['revoked_pengawas'] = max(s['revoked_pengawas'], int(row['revoked_by_pengawas']))
    s['edited_admin'] = max(s['edited_admin'], int(row['edited_by_admin_kabupaten']))
    s['rejected_admin'] = max(s['rejected_admin'], int(row['rejected_by_admin_kabupaten']))
    s['revoked_admin'] = max(s['revoked_admin'], int(row['revoked_by_admin_kabupaten']))
    s['completed_admin'] = max(s['completed_admin'], int(row['completed_by_admin_kabupaten']))

    if not s['pencacah'] and str(row.get('pencacah_email', '')) != 'nan':
        s['pencacah'] = str(row['pencacah_email']).strip()
    if not s['pengawas'] and str(row.get('pengawas_email', '')) != 'nan':
        s['pengawas'] = str(row['pengawas_email']).strip()

print(f"Total SubSLS: {len(subsls_dict)}")

# Compute totals and build hierarchy
# SubSLS totals
for s in subsls_dict.values():
    s['belum'] = s['open'] + s['draft']
    s['selesai'] = (s['submitted_pencacah'] + s['submitted_respondent'] + s['approved'] + 
                    s['completed_admin'] + s['rejected_pengawas'] + s['revoked_pengawas'] + 
                    s['edited_pengawas'] + s['edited_admin'] + s['rejected_admin'] + s['revoked_admin'])
    s['total'] = s['belum'] + s['selesai']
    s['pct'] = round((s['selesai'] / s['total'] * 100), 1) if s['total'] > 0 else 0.0

# Groupings
desa_map = {}
kec_map = {}
kab_map = {}

for s in subsls_dict.values():
    k_code = s['kab_code']
    kc_code = s['kec_code']
    d_code = s['desa_code']

    # Desa level
    if d_code not in desa_map:
        desa_map[d_code] = {
            'code': d_code,
            'kab_code': k_code,
            'kec_code': kc_code,
            'name': s['nmdesa'] or f"Desa {d_code}",
            'nmkab': s['nmkab'],
            'nmkec': s['nmkec'],
            'total': 0, 'belum': 0, 'selesai': 0,
            'open': 0, 'draft': 0, 'submitted_pencacah': 0, 'submitted_respondent': 0,
            'approved': 0, 'completed_admin': 0, 'rejected_pengawas': 0, 'revoked_pengawas': 0,
            'edited_pengawas': 0, 'edited_admin': 0, 'rejected_admin': 0, 'revoked_admin': 0,
            'sls_count': 0
        }
    d = desa_map[d_code]
    d['total'] += s['total']
    d['belum'] += s['belum']
    d['selesai'] += s['selesai']
    d['open'] += s['open']
    d['draft'] += s['draft']
    d['submitted_pencacah'] += s['submitted_pencacah']
    d['submitted_respondent'] += s['submitted_respondent']
    d['approved'] += s['approved']
    d['completed_admin'] += s['completed_admin']
    d['rejected_pengawas'] += s['rejected_pengawas']
    d['revoked_pengawas'] += s['revoked_pengawas']
    d['edited_pengawas'] += s['edited_pengawas']
    d['edited_admin'] += s['edited_admin']
    d['rejected_admin'] += s['rejected_admin']
    d['revoked_admin'] += s['revoked_admin']
    d['sls_count'] += 1

    # Kec level
    if kc_code not in kec_map:
        kec_map[kc_code] = {
            'code': kc_code,
            'kab_code': k_code,
            'name': s['nmkec'] or f"Kecamatan {kc_code}",
            'nmkab': s['nmkab'],
            'total': 0, 'belum': 0, 'selesai': 0,
            'open': 0, 'draft': 0, 'submitted_pencacah': 0, 'submitted_respondent': 0,
            'approved': 0, 'completed_admin': 0, 'rejected_pengawas': 0, 'revoked_pengawas': 0,
            'edited_pengawas': 0, 'edited_admin': 0, 'rejected_admin': 0, 'revoked_admin': 0,
            'desa_count': 0, 'sls_count': 0
        }
    kc = kec_map[kc_code]
    kc['total'] += s['total']
    kc['belum'] += s['belum']
    kc['selesai'] += s['selesai']
    kc['open'] += s['open']
    kc['draft'] += s['draft']
    kc['submitted_pencacah'] += s['submitted_pencacah']
    kc['submitted_respondent'] += s['submitted_respondent']
    kc['approved'] += s['approved']
    kc['completed_admin'] += s['completed_admin']
    kc['rejected_pengawas'] += s['rejected_pengawas']
    kc['revoked_pengawas'] += s['revoked_pengawas']
    kc['edited_pengawas'] += s['edited_pengawas']
    kc['edited_admin'] += s['edited_admin']
    kc['rejected_admin'] += s['rejected_admin']
    kc['revoked_admin'] += s['revoked_admin']
    kc['sls_count'] += 1

    # Kab level
    if k_code not in kab_map:
        kab_map[k_code] = {
            'code': k_code,
            'name': s['nmkab'] or KAB_MAP.get(k_code, f"Kabupaten {k_code}"),
            'total': 0, 'belum': 0, 'selesai': 0,
            'open': 0, 'draft': 0, 'submitted_pencacah': 0, 'submitted_respondent': 0,
            'approved': 0, 'completed_admin': 0, 'rejected_pengawas': 0, 'revoked_pengawas': 0,
            'edited_pengawas': 0, 'edited_admin': 0, 'rejected_admin': 0, 'revoked_admin': 0,
            'kec_count': 0, 'desa_count': 0, 'sls_count': 0
        }
    kb = kab_map[k_code]
    kb['total'] += s['total']
    kb['belum'] += s['belum']
    kb['selesai'] += s['selesai']
    kb['open'] += s['open']
    kb['draft'] += s['draft']
    kb['submitted_pencacah'] += s['submitted_pencacah']
    kb['submitted_respondent'] += s['submitted_respondent']
    kb['approved'] += s['approved']
    kb['completed_admin'] += s['completed_admin']
    kb['rejected_pengawas'] += s['rejected_pengawas']
    kb['revoked_pengawas'] += s['revoked_pengawas']
    kb['edited_pengawas'] += s['edited_pengawas']
    kb['edited_admin'] += s['edited_admin']
    kb['rejected_admin'] += s['rejected_admin']
    kb['revoked_admin'] += s['revoked_admin']
    kb['sls_count'] += 1

# Calculate percentages and unique sub-entity counts
for kb in kab_map.values():
    kb['pct'] = round((kb['selesai'] / kb['total'] * 100), 1) if kb['total'] > 0 else 0.0
    kb['kec_count'] = len([kc for kc in kec_map.values() if kc['kab_code'] == kb['code']])
    kb['desa_count'] = len([d for d in desa_map.values() if d['kab_code'] == kb['code']])

for kc in kec_map.values():
    kc['pct'] = round((kc['selesai'] / kc['total'] * 100), 1) if kc['total'] > 0 else 0.0
    kc['desa_count'] = len([d for d in desa_map.values() if d['kec_code'] == kc['code']])

for d in desa_map.values():
    d['pct'] = round((d['selesai'] / d['total'] * 100), 1) if d['total'] > 0 else 0.0

# Prepare structured tree for client-side
# 1. kab list
kab_list = sorted(list(kab_map.values()), key=lambda x: x['code'])

# 2. kec grouped by kab_code
kec_by_kab = {}
for kc in kec_map.values():
    k_code = kc['kab_code']
    if k_code not in kec_by_kab:
        kec_by_kab[k_code] = []
    kec_by_kab[k_code].append(kc)
for k_code in kec_by_kab:
    kec_by_kab[k_code].sort(key=lambda x: x['code'])

# 3. desa grouped by kec_code
desa_by_kec = {}
for d in desa_map.values():
    kc_code = d['kec_code']
    if kc_code not in desa_by_kec:
        desa_by_kec[kc_code] = []
    desa_by_kec[kc_code].append(d)
for kc_code in desa_by_kec:
    desa_by_kec[kc_code].sort(key=lambda x: x['code'])

# 4. sls grouped by desa_code
sls_by_desa = {}
for s in subsls_dict.values():
    d_code = s['desa_code']
    if d_code not in sls_by_desa:
        sls_by_desa[d_code] = []
    sls_by_desa[d_code].append(s)
for d_code in sls_by_desa:
    sls_by_desa[d_code].sort(key=lambda x: x['id'])

output_data = {
    'kab': kab_list,
    'kec_by_kab': kec_by_kab,
    'desa_by_kec': desa_by_kec,
    'sls_by_desa': sls_by_desa
}

out_path = os.path.join(BASE_DIR, 'rekap_status_sls.js')
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(f"window.REKAP_STATUS_DATA = {json.dumps(output_data, ensure_ascii=False)};\n")

print(f"Generated {out_path} successfully!")
