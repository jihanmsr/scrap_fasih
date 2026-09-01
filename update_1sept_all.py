"""
UPDATE 1 SEPTEMBER 2026 - Master Script
================================================
Mengupdate seluruh menu dashboard secara komprehensif dari folder update_1sept/:
1. [PROGRES PETUGAS]  rekap_progress_petugas (5).xlsx
                      -> fast_petugas_progress.js + petugas_region_map.js
                      -> fast_petugas_all_2026-09-01.csv -> fast_petugas_history.js
                      -> Rekap Progress Petugas 01_09.xlsx
2. [REKON SBR/UTP]    rekap_sbr_utp_keluarga (5).xlsx
                      -> Rekap SBR, UTP, Keluarga_20260901.xlsx
                      -> Laporan_Rekap_KabKot_SBR_UTP_Keluarga_01_09.xlsx
                      -> rekon_data.js
3. [SLS OPEN]         Progress Petugas + jumlah_subsls_yang_belum_dikunjungi (5).xlsx
                      -> open_subsls_data.js + highlighted_subsls.js
4. [CACHE BUSTER]     index.html
"""

import sys
import os
import re
import json
import datetime
import glob
import base64
import gzip
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPDATE_DIR = os.path.join(BASE_DIR, 'update_1sept')

# File paths in update_1sept
F_PROGRES = os.path.join(UPDATE_DIR, 'rekap_progress_petugas (5).xlsx')
F_REKON   = os.path.join(UPDATE_DIR, 'rekap_sbr_utp_keluarga (5).xlsx')
F_SUBSLS  = os.path.join(UPDATE_DIR, 'jumlah_subsls_yang_belum_dikunjungi (5).xlsx')

# Muatan files
F_MUATAN = os.path.join(BASE_DIR, 'muatan', 'muatan_sls_72 2.xlsx')
if not os.path.exists(F_MUATAN):
    F_MUATAN = os.path.join(BASE_DIR, 'muatan_sls_72.xlsx')

KAB_MAP = {
    '7201': 'BANGGAI KEPULAUAN', '7202': 'BANGGAI', '7203': 'MOROWALI',
    '7204': 'POSO', '7205': 'DONGGALA', '7206': 'TOLI-TOLI', '7207': 'BUOL',
    '7208': 'PARIGI MOUTONG', '7209': 'TOJO UNA-UNA', '7210': 'SIGI',
    '7211': 'BANGGAI LAUT', '7212': 'MOROWALI UTARA', '7271': 'PALU'
}


# ============================================================
# 1. UPDATE PROGRES PETUGAS & HISTORY
# ============================================================
def update_progres_petugas():
    print("\n" + "="*60)
    print("  [1/3] UPDATE MENU PROGRES PETUGAS & HISTORY (1 SEPTEMBER)")
    print("="*60)

    df = pd.read_excel(F_PROGRES, dtype=str)
    print(f"    -> {len(df):,} baris data progres petugas dibaca")

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

    # Save to Excel
    out_xlsx = os.path.join(BASE_DIR, 'Rekap Progress Petugas 01_09.xlsx')
    try:
        df.to_excel(out_xlsx, index=False)
        print(f"    OK {os.path.basename(out_xlsx)} berhasil disimpan")
    except Exception as e:
        print(f"    WARN: simpan excel gagal: {e}")

    # ── A. fast_petugas_progress.js & petugas_region_map.js ───────────────────
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
        print(f"    OK fast_petugas_progress.js: +{added} baru, ~{updated} diupdate")

    reg_path = os.path.join(BASE_DIR, 'petugas_region_map.js')
    with open(reg_path, 'r', encoding='utf-8') as f:
        content_reg = f.read()

    match_r = re.search(r'window\.PETUGAS_REGION_MAP\s*=\s*(\{.*?\});', content_reg, re.DOTALL)
    if match_r:
        reg_map = json.loads(match_r.group(1))
        added_r = 0
        for email, regs in region_patch.items():
            if email not in reg_map:
                reg_map[email] = regs
                added_r += 1
            else:
                for r in regs:
                    if r not in reg_map[email]:
                        reg_map[email].append(r)

        new_json = json.dumps(reg_map, indent=4, ensure_ascii=False)
        content_reg = content_reg[:match_r.start(1)] + new_json + content_reg[match_r.end(1):]
        with open(reg_path, 'w', encoding='utf-8') as f:
            f.write(content_reg)
        print(f"    OK petugas_region_map.js: +{added_r} email baru ditambahkan")

    # ── B. fast_petugas_all_2026-09-01.csv & fast_petugas_history.js ────────────
    df_p_agg = df_p.groupby('pencacah_email').agg({c: 'sum' for c in numeric_cols}).reset_index()
    df_p_agg = df_p_agg.rename(columns={'pencacah_email': 'Email'})
    df_p_agg['Role'] = 'Pencacah'

    df_w = df[df['pengawas_email'].notna() & (df['pengawas_email'].str.strip() != '')]
    df_w_agg = df_w.groupby('pengawas_email').agg({c: 'sum' for c in numeric_cols}).reset_index()
    df_w_agg = df_w_agg.rename(columns={'pengawas_email': 'Email'})
    df_w_agg['Role'] = 'Pengawas'

    combined = pd.concat([df_p_agg, df_w_agg], ignore_index=True)
    combined['Total Target'] = combined[numeric_cols].sum(axis=1)
    combined = combined.rename(columns={
        'open': 'OPEN', 'draft': 'DRAFT',
        'submitted_by_pencacah': 'SUBMITTED BY Pencacah',
        'submitted_respondent': 'SUBMITTED RESPONDENT',
        'approved_by_pengawas': 'APPROVED BY Pengawas',
        'rejected_by_pengawas': 'REJECTED BY Pengawas',
        'revoked_by_pengawas': 'REVOKED BY Pengawas',
        'edited_by_pengawas': 'EDITED BY Pengawas',
        'edited_by_admin_kabupaten': 'EDITED BY Admin Kabupaten',
        'rejected_by_admin_kabupaten': 'REJECTED BY Admin Kabupaten',
        'completed_by_admin_kabupaten': 'COMPLETED BY Admin Kabupaten'
    })
    cols_order = ['Email', 'Role', 'Total Target', 'OPEN', 'DRAFT', 'SUBMITTED BY Pencacah',
                  'SUBMITTED RESPONDENT', 'APPROVED BY Pengawas', 'REJECTED BY Pengawas',
                  'REVOKED BY Pengawas', 'EDITED BY Pengawas', 'EDITED BY Admin Kabupaten',
                  'REJECTED BY Admin Kabupaten', 'COMPLETED BY Admin Kabupaten']
    combined = combined[cols_order]
    
    csv_01 = os.path.join(BASE_DIR, 'fast_petugas_all_2026-09-01.csv')
    combined.to_csv(csv_01, index=False)
    combined.to_csv(os.path.join(BASE_DIR, 'fast_petugas_all.csv'), index=False)
    print(f"    OK fast_petugas_all_2026-09-01.csv dibuat ({len(combined):,} baris)")

    # Rebuild history
    import subprocess
    subprocess.run([sys.executable, os.path.join(BASE_DIR, 'rebuild_history.py')], check=True)
    print("    OK fast_petugas_history.js diperbarui (sampai 1 SEPTEMBER)")

    return df


# ============================================================
# 2. UPDATE REKON SBR/UTP (TABULASI)
# ============================================================
def update_rekon_sbr():
    print("\n" + "="*60)
    print("  [2/3] UPDATE MENU REKON / SBR-UTP-KELUARGA (TABULASI 1 SEPTEMBER)")
    print("="*60)

    df_real = pd.read_excel(F_REKON, dtype={'level_5_full_code': str, 'level_6_code': str})
    print(f"    -> {len(df_real):,} baris realisasi SBR/UTP dibaca")

    # Save to Excel
    out_rekon_xlsx = os.path.join(BASE_DIR, 'Rekap SBR, UTP, Keluarga_20260901.xlsx')
    df_real.to_excel(out_rekon_xlsx, index=False)
    out_rekon_xlsx_alt = os.path.join(BASE_DIR, 'Rekap SBR, UTP, Keluarga_01_09.xlsx')
    df_real.to_excel(out_rekon_xlsx_alt, index=False)
    print(f"    OK {os.path.basename(out_rekon_xlsx)} dibuat")

    df_real['idsls_str']    = df_real['level_5_full_code'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
    df_real['kdsubsls_str'] = pd.to_numeric(df_real['level_6_code'], errors='coerce').fillna(0).astype(int).astype(str).str.zfill(2)
    df_real['sls_id']       = df_real['idsls_str'] + df_real['kdsubsls_str']
    df_real['realisasi']    = df_real['total_utp'].fillna(0) + df_real['total_sbr'].fillna(0) + df_real['total_keluarga'].fillna(0)

    # Generate Laporan_Rekap_KabKot
    region_map_path = os.path.join(BASE_DIR, 'region_map_sulteng_full.json')
    with open(region_map_path) as f:
        region_map = json.load(f)

    def get_kab_name(kab_code):
        kab_data = region_map.get('kabupaten', {}).get(kab_code, {})
        return kab_data.get('kab_name', '-')

    df_real['Kode Kab'] = df_real['idsls_str'].str[:4]
    df_real['Nama Kab/Kota'] = df_real['Kode Kab'].apply(get_kab_name)

    agg = {'total_utp': 'sum', 'total_sbr': 'sum', 'total_keluarga': 'sum'}
    df_rekap = df_real.groupby(['Kode Kab', 'Nama Kab/Kota'], as_index=False).agg(agg)
    df_rekap = df_rekap.rename(columns={
        'total_utp': 'Total UTP', 'total_sbr': 'Total SBR', 'total_keluarga': 'Total Keluarga'
    })
    df_rekap = df_rekap[df_rekap['Kode Kab'].str.len() == 4].sort_values('Kode Kab')

    df_total = pd.DataFrame([{
        'Kode Kab': 'TOTAL', 'Nama Kab/Kota': 'SULAWESI TENGAH',
        'Total UTP': df_rekap['Total UTP'].sum(),
        'Total SBR': df_rekap['Total SBR'].sum(),
        'Total Keluarga': df_rekap['Total Keluarga'].sum()
    }])
    df_rekap = pd.concat([df_rekap, df_total], ignore_index=True)
    out_kabkot = os.path.join(BASE_DIR, 'Laporan_Rekap_KabKot_SBR_UTP_Keluarga_01_09.xlsx')
    df_rekap.to_excel(out_kabkot, index=False)
    print(f"    OK {os.path.basename(out_kabkot)} dibuat")

    # Read muatan awal
    if os.path.exists(F_MUATAN):
        df_awal = pd.read_excel(F_MUATAN, dtype={'idsubsls_25_2': str})
        df_awal['sls_id'] = df_awal['idsubsls_25_2'].str.strip()
        df_awal['target_awal'] = df_awal['jml_utp_subsektor'].fillna(0) + df_awal['Total_usaha_SBR'].fillna(0) + df_awal['keluarga'].fillna(0)
    else:
        df_awal = pd.DataFrame(columns=['sls_id', 'target_awal', 'jml_utp_subsektor', 'Total_usaha_SBR', 'keluarga', 'nmkab', 'nmkec', 'nmdesa', 'nmsls'])

    # Parse SQL assignments for Petugas Mapping
    sql_assignments = []
    all_emails = set()
    for file in glob.glob(os.path.join(BASE_DIR, 'granular_assignments_se_umum_*.json')):
        try:
            with open(file) as f:
                d = json.load(f)
            if 'compressed_data' not in d: continue
            data = json.loads(gzip.decompress(base64.b64decode(d['compressed_data'])))
            petugas_list = data.get('petugas', [])
            for p in petugas_list:
                try:
                    email = p[0] if isinstance(p, list) else p
                    email = str(email).lower().strip()
                    if email != '-': all_emails.add(email)
                except: pass
            for t in data.get('targets', []):
                target_str = str(t[1])
                sls_id = target_str.split(' - ')[0].strip()
                pid = t[-1]
                try:
                    email = petugas_list[pid][0] if isinstance(petugas_list[pid], list) else petugas_list[pid]
                except: email = '-'
                email = str(email).lower().strip()
                if len(sls_id) == 16:
                    sql_assignments.append({'sls_id': sls_id, 'email': email})
        except Exception as e:
            pass

    df_sql = pd.DataFrame(sql_assignments).drop_duplicates() if sql_assignments else pd.DataFrame(columns=['sls_id', 'email'])
    df_sql['weight'] = 1.0

    awal_cols = [c for c in ['sls_id', 'target_awal', 'jml_utp_subsektor', 'Total_usaha_SBR', 'keluarga', 'nmkab', 'nmkec', 'nmdesa', 'nmsls'] if c in df_awal.columns]
    df_sls = pd.merge(
        df_awal[awal_cols] if awal_cols else df_awal,
        df_real[['sls_id', 'realisasi', 'total_utp', 'total_sbr', 'total_keluarga']],
        on='sls_id', how='outer'
    ).fillna(0)

    def fill_names(row):
        sls = str(row['sls_id'])
        if sls in ('0', 'nan') or len(sls) < 10:
            return row
        if 'nmkab' in row.index and row['nmkab'] != 0:
            return row
        kab = sls[:4]; kec = sls[:7]; desa = sls[:10]
        kab_data = region_map.get('kabupaten', {}).get(kab, {})
        if 'nmkab' in row.index:  row['nmkab']  = kab_data.get('kab_name', '-')
        kec_data  = kab_data.get('kecamatan', {}).get(kec, {})
        if 'nmkec' in row.index:  row['nmkec']  = kec_data.get('kec_name', '-')
        desa_data = kec_data.get('desa', {}).get(desa, {})
        if 'nmdesa' in row.index: row['nmdesa'] = desa_data.get('desa_name', '-')
        return row

    df_sls = df_sls.apply(fill_names, axis=1)

    if 'nmsls' in df_sls.columns:
        df_sls['nmsls'] = df_sls['nmsls'].replace(0, '-')
    df_sls['diff'] = df_sls['realisasi'] - df_sls.get('target_awal', 0)

    metrics_cols = [c for c in ['target_awal', 'realisasi', 'jml_utp_subsektor', 'Total_usaha_SBR', 'keluarga', 'total_utp', 'total_sbr', 'total_keluarga'] if c in df_sls.columns]
    if not df_sql.empty and metrics_cols:
        df_pm = pd.merge(df_sql, df_sls[['sls_id'] + metrics_cols], on='sls_id', how='left').fillna(0)
        for col in metrics_cols:
            df_pm[col] = df_pm[col] * df_pm['weight']
        df_petugas = df_pm.groupby('email').agg({col: 'sum' for col in metrics_cols}).reset_index()
    else:
        df_petugas = pd.DataFrame(columns=['email'])

    if all_emails:
        all_emails_df = pd.DataFrame([{'email': e} for e in all_emails])
        df_petugas = pd.merge(all_emails_df, df_petugas, on='email', how='outer').fillna(0)

    if 'jml_utp_subsektor' in df_petugas.columns:
        df_petugas = df_petugas.rename(columns={'jml_utp_subsektor': 'total_muatan_assigned', 'total_utp': 'total_usaha'})
    if 'target_awal' in df_petugas.columns and 'realisasi' in df_petugas.columns:
        df_petugas['diff'] = df_petugas['realisasi'] - df_petugas['target_awal']

    out_path = os.path.join(BASE_DIR, 'rekon_data.js')
    js_content  = "window.rekonSlsData = "     + df_sls.to_json(orient='records') + ";\n"
    js_content += "window.rekonPetugasData = " + df_petugas.to_json(orient='records') + ";\n"
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(js_content)

    print(f"    OK rekon_data.js diperbarui: {len(df_sls):,} SLS, {len(df_petugas):,} petugas")


# ============================================================
# 3. UPDATE SLS OPEN (PEMANTAUAN SLS STATUS FULL OPEN)
# ============================================================
def update_sls_open(df_prog=None):
    print("\n" + "="*60)
    print("  [3/3] UPDATE MENU SLS OPEN (OPEN_SUBSLS_DATA & HIGHLIGHTED)")
    print("="*60)

    if df_prog is None:
        df_prog = pd.read_excel(F_PROGRES, dtype=str)

    cols = ['open', 'draft', 'submitted_respondent', 'submitted_by_pencacah',
            'edited_by_pengawas', 'rejected_by_pengawas', 'approved_by_pengawas',
            'revoked_by_pengawas', 'edited_by_admin_kabupaten', 'rejected_by_admin_kabupaten',
            'revoked_by_admin_kabupaten', 'completed_by_admin_kabupaten']
    for c in cols:
        if c in df_prog.columns:
            df_prog[c] = pd.to_numeric(df_prog[c], errors='coerce').fillna(0)

    non_open = ['draft', 'submitted_respondent', 'submitted_by_pencacah',
                'edited_by_pengawas', 'rejected_by_pengawas', 'approved_by_pengawas',
                'revoked_by_pengawas', 'edited_by_admin_kabupaten', 'rejected_by_admin_kabupaten',
                'revoked_by_admin_kabupaten', 'completed_by_admin_kabupaten']

    df_prog['non_open_sum'] = df_prog[non_open].sum(axis=1)
    full_open_df = df_prog[(df_prog['open'] > 0) & (df_prog['non_open_sum'] == 0)].copy()

    df_m = pd.read_excel(F_MUATAN, dtype={'idsubsls_25_2': str})
    df_m['sls_16'] = df_m['idsubsls_25_2'].str.strip()
    df_m = df_m.drop_duplicates('sls_16')
    muatan_map = df_m.set_index('sls_16').to_dict(orient='index')

    data_list = []
    highlighted_map = {}

    for _, row in full_open_df.iterrows():
        sls_14 = str(row['level_5_full_code']).replace('.0', '').zfill(14)
        kd_sub = str(int(float(row['level_6_code']))).zfill(2)
        sls_16 = sls_14 + kd_sub

        m_info = muatan_map.get(sls_16, {})

        kab_code = int(sls_14[:4])
        kec_code = int(sls_14[:7])
        desa_code = int(sls_14[:10])
        sls_code = int(sls_14)
        sub_sls_code = int(sls_16)

        kab_str = str(sls_14[:4])
        kab_name = m_info.get('nmkab') or (str(row.get('kabupaten', '')) if str(row.get('kabupaten', '')) not in ('', 'nan') else '') or KAB_MAP.get(kab_str, '')
        kec_name = m_info.get('nmkec') or (str(row.get('kecamatan', '')) if str(row.get('kecamatan', '')) not in ('', 'nan') else '') or '-'
        desa_name = m_info.get('nmdesa') or (str(row.get('desa', '')) if str(row.get('desa', '')) not in ('', 'nan') else '') or '-'
        sls_name = m_info.get('nmsls', '-')
        subsls_name = m_info.get('nmsls', '-')

        email = str(row.get('pencacah_email', '')).strip()
        petugas_name = email if email else None

        item = {
            'kode_kab': kab_code,
            'kabupaten': str(kab_name),
            'kode_kecamatan': kec_code,
            'kecamatan': str(kec_name),
            'kode_desa': desa_code,
            'desa': str(desa_name),
            'kode_sls': sls_code,
            'sls': str(sls_name),
            'kode_sub_sls': sub_sls_code,
            'nama_sub_sls': str(subsls_name),
            'nama_petugas': petugas_name,
            'jumlah_prelist': int(row['open'])
        }
        data_list.append(item)

        highlighted_map[sls_16] = {
            'kode_kab': str(kab_code),
            'kabupaten': str(kab_name),
            'kode_kecamatan': str(kec_code),
            'kecamatan': str(kec_name),
            'kode_desa': str(desa_code),
            'desa': str(desa_name),
            'kode_sls': str(sls_code),
            'sls': str(sls_name),
            'kode_sub_sls': str(sub_sls_code),
            'nama_sub_sls': str(subsls_name),
            'nama_petugas': petugas_name or '',
            'jumlah_prelist': str(int(row['open']))
        }

    with open(os.path.join(BASE_DIR, 'open_subsls_data.js'), 'w', encoding='utf-8') as f:
        f.write('window.OPEN_SUBSLS_DATA = ' + json.dumps(data_list, ensure_ascii=False) + ';')

    with open(os.path.join(BASE_DIR, 'highlighted_subsls.js'), 'w', encoding='utf-8') as f:
        f.write('window.HIGHLIGHTED_SUBSLS = ' + json.dumps(highlighted_map, ensure_ascii=False) + ';')

    with open(os.path.join(BASE_DIR, 'highlighted_subsls.json'), 'w', encoding='utf-8') as f:
        f.write(json.dumps(highlighted_map, ensure_ascii=False, indent=2))

    print(f"    OK open_subsls_data.js & highlighted_subsls.js diperbarui ({len(data_list)} SubSLS full open, total prelist: {sum(x['jumlah_prelist'] for x in data_list)})")


# ============================================================
# 4. UPDATE CACHE BUSTER
# ============================================================
def update_cache_buster():
    import time
    idx_path = os.path.join(BASE_DIR, 'index.html')
    if os.path.exists(idx_path):
        with open(idx_path, 'r', encoding='utf-8') as f:
            html = f.read()
        ts = str(int(time.time()))
        html = re.sub(r'v=\d+(_v\d+)?', f'v={ts}_v0109', html)
        with open(idx_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"\n    OK Cache buster index.html diperbarui ke: v={ts}_v0109")


# ============================================================
# MAIN
# ============================================================
def main():
    print("\n" + "=" * 60)
    print("  UPDATE DASHBOARD 1 SEPTEMBER 2026")
    print("=" * 60)

    df_prog = update_progres_petugas()
    update_rekon_sbr()
    update_sls_open(df_prog)
    update_cache_buster()

    print("\n" + "=" * 60)
    print("  SEMUA DATA BERHASIL DIUPDATE PER 1 SEPTEMBER 2026!")
    print("=" * 60 + "\n")


if __name__ == '__main__':
    main()
