"""
UPDATE 28 AGUSTUS 2026 - Script Master Lengkap
================================================
Mengupdate seluruh menu dashboard secara komprehensif dari folder update_28/:
1. [PROGRES PETUGAS]  rekap_progress_petugas (4).xlsx
                      -> fast_petugas_progress.js + petugas_region_map.js
                      -> fast_petugas_all_2026-08-28.csv -> fast_petugas_history.js
                      -> ipas_data.js
2. [REKON SBR/UTP]    rekap_sbr_utp_keluarga (4).xlsx
                      -> rekon_data.js
3. [SLS OPEN]         rekap_progress_petugas (4).xlsx
                      -> open_subsls_data.js + highlighted_subsls.js
4. [NEW BUSINESSES]   jumlah_subsls_yang_belum_dikunjungi (4).xlsx
                      -> new_businesses_data.js
5. [CACHE BUSTER]     index.html
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
UPDATE_DIR = os.path.join(BASE_DIR, 'update_28')

F_PROGRES  = os.path.join(UPDATE_DIR, 'rekap_progress_petugas (4).xlsx')
F_REKON    = os.path.join(UPDATE_DIR, 'rekap_sbr_utp_keluarga (4).xlsx')
F_SUBSLS   = os.path.join(UPDATE_DIR, 'jumlah_subsls_yang_belum_dikunjungi (4).xlsx')
F_MUATAN   = os.path.join(BASE_DIR, 'muatan', 'muatan_sls_72 2.xlsx')

KAB_MAP = {
    '7201': 'BANGGAI KEPULAUAN', '7202': 'BANGGAI', '7203': 'MOROWALI',
    '7204': 'POSO', '7205': 'DONGGALA', '7206': 'TOLI-TOLI', '7207': 'BUOL',
    '7208': 'PARIGI MOUTONG', '7209': 'TOJO UNA-UNA', '7210': 'SIGI',
    '7211': 'BANGGAI LAUT', '7212': 'MOROWALI UTARA', '7271': 'PALU'
}


# ============================================================
# 1. UPDATE PROGRES PETUGAS & IPAS_DATA & HISTORY
# ============================================================
def update_progres_petugas():
    print("\n" + "="*60)
    print("  [1/4] UPDATE MENU PROGRES PETUGAS & HISTORY & IPAS_DATA")
    print("="*60)
    print(f"    Sumber: {os.path.basename(F_PROGRES)}")

    df = pd.read_excel(F_PROGRES, dtype=str)

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

    # ── B. fast_petugas_all_2026-08-28.csv & fast_petugas_history.js ────────────
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
    csv_28 = os.path.join(BASE_DIR, 'fast_petugas_all_2026-08-28.csv')
    combined.to_csv(csv_28, index=False)
    print(f"    OK fast_petugas_all_2026-08-28.csv dibuat ({len(combined):,} baris)")

    # Rebuild history
    import rebuild_history
    print("    OK fast_petugas_history.js diperbarui (sampai 28 AGU TERAKHIR)")

    # ── C. ipas_data.js (Target & Realisasi SE Umum) ────────────────────────────
    kec_name_map = {}
    ipas_path = os.path.join(BASE_DIR, 'ipas_data.js')
    with open(ipas_path, 'r', encoding='utf-8') as f:
        content_ipas = f.read()
    match_ipas = re.search(r'window\.IPAS_DATA\s*=\s*(\{.*\});', content_ipas, re.DOTALL)
    if match_ipas:
        ipas = json.loads(match_ipas.group(1))
        for kab in ipas.get('se_umum', []):
            for kec in kab.get('kecamatan_list', []):
                k_name = kec.get('kec_name', '')
                if k_name and '[' in k_name and ']' in k_name:
                    code = k_name.split(']')[0].replace('[','').strip()
                    name = k_name.split(']')[1].strip()
                    kec_name_map[code] = name

    df['kode_kab'] = df['level_5_full_code'].astype(str).str.zfill(14).str[:4]
    df['kode_kec'] = df['level_5_full_code'].astype(str).str.zfill(14).str[4:7]

    df['total_prelist'] = df[numeric_cols].sum(axis=1)
    df['total_open'] = df['open']
    df['total_draft'] = df['draft']
    df['total_submitted'] = (df['submitted_by_pencacah'] + df['submitted_respondent'] +
                            df['approved_by_pengawas'] + df['edited_by_pengawas'] +
                            df['edited_by_admin_kabupaten'] + df['completed_by_admin_kabupaten'])
    df['total_approved'] = df['approved_by_pengawas'] + df['completed_by_admin_kabupaten']
    df['total_rejected'] = df['rejected_by_pengawas'] + df['rejected_by_admin_kabupaten']
    df['total_submitted_pencacah'] = df['submitted_by_pencacah']
    df['total_submitted_respondent'] = df['submitted_respondent']

    group_cols = ['kode_kab', 'kode_kec']
    agg_cols = ['total_prelist', 'total_open', 'total_draft', 'total_submitted',
                'total_approved', 'total_rejected', 'total_submitted_pencacah', 'total_submitted_respondent']

    grouped = df.groupby(group_cols)[agg_cols].sum().reset_index()

    kab_dict = {}
    for _, row in grouped.iterrows():
        kode_kab = str(row['kode_kab']).zfill(4)
        kab_id = kode_kab[-2:]
        nama_kab = KAB_MAP.get(kode_kab, kode_kab)
        kab_key = f'[{kab_id}] {nama_kab}'

        kode_kec = str(row['kode_kec']).zfill(3)
        nama_kec = kec_name_map.get(kode_kec, kode_kec)
        kec_key = f'[{kode_kec}] {nama_kec}'

        prelist   = int(row['total_prelist'])
        opn       = int(row['total_open'])
        draft     = int(row['total_draft'])
        submitted = int(row['total_submitted'])
        approved  = int(row['total_approved'])
        rejected  = int(row['total_rejected'])
        sub_pen   = int(row['total_submitted_pencacah'])
        sub_res   = int(row['total_submitted_respondent'])

        if kab_key not in kab_dict:
            kab_dict[kab_key] = {
                'kabupaten': kab_key, 'total_prelist': 0, 'total_draft': 0, 'total_open': 0,
                'total_submitted': 0, 'total_rejected': 0, 'total_approved': 0,
                'total_submitted_pencacah': 0, 'total_submitted_respondent': 0,
                'persentase': 0, 'new_usaha_overall': 0, 'new_rumah_overall': 0,
                'kecamatan_list': []
            }

        kab_dict[kab_key]['total_prelist'] += prelist
        kab_dict[kab_key]['total_open'] += opn
        kab_dict[kab_key]['total_draft'] += draft
        kab_dict[kab_key]['total_submitted'] += submitted
        kab_dict[kab_key]['total_approved'] += approved
        kab_dict[kab_key]['total_rejected'] += rejected
        kab_dict[kab_key]['total_submitted_pencacah'] += sub_pen
        kab_dict[kab_key]['total_submitted_respondent'] += sub_res

        perc_kec = (submitted / prelist * 100) if prelist > 0 else 0

        kab_dict[kab_key]['kecamatan_list'].append({
            'kecamatan': kec_key, 'kec_name': kec_key, 'total_prelist': prelist,
            'total_draft': draft, 'total_open': opn, 'total_submitted': submitted,
            'total_rejected': rejected, 'total_approved': approved,
            'total_submitted_pencacah': sub_pen, 'total_submitted_respondent': sub_res,
            'persentase': round(perc_kec, 2), 'new_usaha': 0, 'new_rumah': 0
        })

    se_umum_arr = []
    for kab in sorted(kab_dict.keys()):
        data = kab_dict[kab]
        if data['total_prelist'] > 0:
            data['persentase'] = round(data['total_submitted'] / data['total_prelist'] * 100, 2)
        se_umum_arr.append(data)

    final_js_obj = {
        'updated_at': '28 Aug 2026, 11:00:00 (Sync 28 Agustus)',
        'se_umum': se_umum_arr
    }

    with open(ipas_path, 'w', encoding='utf-8') as f:
        f.write(f'window.IPAS_DATA = {json.dumps(final_js_obj, ensure_ascii=False, indent=2)};\n')

    print("    OK ipas_data.js diperbarui (Ringkasan SE Umum 28 Agustus)")


# ============================================================
# 2. UPDATE REKON SBR/UTP/KELUARGA
# ============================================================
def update_rekon_sbr():
    print("\n" + "="*60)
    print("  [2/4] UPDATE MENU REKON / SBR-UTP-KELUARGA (TABULASI)")
    print("="*60)
    print(f"    Sumber: {os.path.basename(F_REKON)}")

    df_real = pd.read_excel(F_REKON, dtype={'level_5_full_code': str, 'level_6_code': str})
    df_real['idsls_str']    = df_real['level_5_full_code'].str.replace(r'\.0$', '', regex=True).str.strip()
    df_real['kdsubsls_str'] = pd.to_numeric(df_real['level_6_code'], errors='coerce').fillna(0).astype(int).astype(str).str.zfill(2)
    df_real['sls_id']       = df_real['idsls_str'] + df_real['kdsubsls_str']
    df_real['realisasi']    = df_real['total_utp'].fillna(0) + df_real['total_sbr'].fillna(0) + df_real['total_keluarga'].fillna(0)
    print(f"    -> {len(df_real):,} baris realisasi dibaca")

    if os.path.exists(F_MUATAN):
        df_awal = pd.read_excel(F_MUATAN, dtype={'idsubsls_25_2': str})
        df_awal['sls_id'] = df_awal['idsubsls_25_2'].str.strip()
        df_awal['target_awal'] = df_awal['jml_utp_subsektor'].fillna(0) + df_awal['Total_usaha_SBR'].fillna(0) + df_awal['keluarga'].fillna(0)
        print(f"    -> {len(df_awal):,} baris muatan awal dibaca")
    else:
        df_awal = pd.DataFrame(columns=['sls_id', 'target_awal', 'jml_utp_subsektor', 'Total_usaha_SBR', 'keluarga', 'nmkab', 'nmkec', 'nmdesa', 'nmsls'])

    sql_assignments = []
    all_emails = set()
    for file in glob.glob(os.path.join(BASE_DIR, 'granular_assignments_se_umum_*.json')):
        try:
            with open(file) as f:
                d = json.load(f)
            if 'compressed_data' not in d:
                continue
            data = json.loads(gzip.decompress(base64.b64decode(d['compressed_data'])))
            petugas_list = data.get('petugas', [])
            for p in petugas_list:
                try:
                    email = p[0] if isinstance(p, list) else p
                    email = str(email).lower().strip()
                    if email != '-':
                        all_emails.add(email)
                except:
                    pass
            for t in data.get('targets', []):
                target_str = str(t[1])
                sls_id = target_str.split(' - ')[0].strip()
                pid = t[-1]
                try:
                    email = petugas_list[pid][0] if isinstance(petugas_list[pid], list) else petugas_list[pid]
                except:
                    email = '-'
                email = str(email).lower().strip()
                if len(sls_id) == 16:
                    sql_assignments.append({'sls_id': sls_id, 'email': email})
        except Exception as e:
            print(f"    WARN: {file}: {e}")

    df_sql = pd.DataFrame(sql_assignments).drop_duplicates() if sql_assignments else pd.DataFrame(columns=['sls_id', 'email'])
    df_sql['weight'] = 1.0

    awal_cols = [c for c in ['sls_id', 'target_awal', 'jml_utp_subsektor', 'Total_usaha_SBR', 'keluarga', 'nmkab', 'nmkec', 'nmdesa', 'nmsls'] if c in df_awal.columns]
    df_sls = pd.merge(
        df_awal[awal_cols] if awal_cols else df_awal,
        df_real[['sls_id', 'realisasi', 'total_utp', 'total_sbr', 'total_keluarga']],
        on='sls_id', how='outer'
    ).fillna(0)

    region_map_path = os.path.join(BASE_DIR, 'region_map_sulteng_full.json')
    if os.path.exists(region_map_path):
        with open(region_map_path) as f:
            region_map = json.load(f)

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
def update_sls_open():
    print("\n" + "="*60)
    print("  [3/4] UPDATE MENU SLS OPEN (OPEN_SUBSLS_DATA)")
    print("="*60)
    print(f"    Sumber: {os.path.basename(F_PROGRES)}")

    df = pd.read_excel(F_PROGRES)
    cols = ['open', 'draft', 'submitted_respondent', 'submitted_by_pencacah',
            'edited_by_pengawas', 'rejected_by_pengawas', 'approved_by_pengawas',
            'revoked_by_pengawas', 'edited_by_admin_kabupaten', 'rejected_by_admin_kabupaten',
            'revoked_by_admin_kabupaten', 'completed_by_admin_kabupaten']
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

    non_open = ['draft', 'submitted_respondent', 'submitted_by_pencacah',
                'edited_by_pengawas', 'rejected_by_pengawas', 'approved_by_pengawas',
                'revoked_by_pengawas', 'edited_by_admin_kabupaten', 'rejected_by_admin_kabupaten',
                'revoked_by_admin_kabupaten', 'completed_by_admin_kabupaten']

    df['non_open_sum'] = df[non_open].sum(axis=1)
    full_open_df = df[(df['open'] > 0) & (df['non_open_sum'] == 0)].copy()

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

        kab_name = m_info.get('nmkab', row.get('kabupaten', ''))
        kec_name = m_info.get('nmkec', row.get('kecamatan', ''))
        desa_name = m_info.get('nmdesa', row.get('desa', ''))
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
# 4. UPDATE NEW BUSINESSES (SUBSLS BELUM DIKUNJUNGI)
# ============================================================
def update_subsls_belum_dikunjungi():
    print("\n" + "="*60)
    print("  [4/4] UPDATE DATA SUBSLS BELUM DIKUNJUNGI (NEW BUSINESSES)")
    print("="*60)
    print(f"    Sumber: {os.path.basename(F_SUBSLS)}")

    df = pd.read_excel(F_SUBSLS)
    df = df.fillna('')
    print(f"    -> {len(df):,} baris data dibaca")

    records = []
    for _, row in df.iterrows():
        code_identity = str(row.get('code_identity', ''))
        sls_code = code_identity.split(' - ')[0].strip() if ' - ' in code_identity else code_identity

        def safe_float(v):
            try:
                return float(str(v).replace(',', '') or 0)
            except:
                return 0.0

        rec = {
            'kab_code'      : str(row.get('kab', '')),
            'kab_name'      : str(row.get('level_2_name', '')),
            'kec_name'      : str(row.get('level_3_name', '')),
            'desa_name'     : str(row.get('level_4_name', '')),
            'sls_name'      : str(row.get('level_5_name', '')),
            'subsls_name'   : str(row.get('level_6_name', '')),
            'code_identity' : code_identity,
            'sls_code'      : sls_code,
            'nama_usaha'    : str(row.get('data1', '')),
            'alamat'        : str(row.get('alamat_usaha', '')),
            'keberadaan'    : str(row.get('keberadaan_label', '')),
            'latitude'      : safe_float(row.get('latitude', 0)),
            'longitude'     : safe_float(row.get('longitude', 0)),
            'pendapatan'    : safe_float(row.get('pendapatan', 0)),
            'pengeluaran'   : safe_float(row.get('pengeluaran', 0)),
            'aset'          : safe_float(row.get('aset', 0)),
            'biaya_produksi': safe_float(row.get('biaya_produksi', 0)),
            'nilai_tambah'  : safe_float(row.get('nilai_tambah', 0)),
            'link_assignment': str(row.get('link_assignment', '')),
        }
        records.append(rec)

    out_path = os.path.join(BASE_DIR, 'new_businesses_data.js')
    timestamp = datetime.datetime.now().strftime('%d %b %Y, %H:%M WIB')
    js_content  = f"// Data SubSLS Belum Dikunjungi - Update {timestamp}\n"
    js_content += f"window.NEW_BUSINESSES_DATA = {json.dumps(records, ensure_ascii=False, indent=2)};\n"
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(js_content)

    print(f"    OK new_businesses_data.js diperbarui: {len(records):,} usaha")


# ============================================================
# 5. CACHE BUSTER UPDATE
# ============================================================
def update_cache_buster():
    import time
    idx_path = os.path.join(BASE_DIR, 'index.html')
    if os.path.exists(idx_path):
        with open(idx_path, 'r', encoding='utf-8') as f:
            html = f.read()
        ts = str(int(time.time()))
        html = re.sub(r'v=\d+(_v\d+)?', f'v={ts}_v2', html)
        with open(idx_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"\n    OK Cache buster index.html diperbarui ke: v={ts}_v2")


# ============================================================
# MAIN
# ============================================================
def main():
    args = sys.argv[1:]
    run_all = len(args) == 0

    print("\n" + "=" * 60)
    print("  UPDATE DASHBOARD LENGKAP - 28 AGUSTUS 2026")
    print("  Dir: " + UPDATE_DIR)
    print("=" * 60)

    if run_all or '--progres' in args:
        if os.path.exists(F_PROGRES):
            update_progres_petugas()
        else:
            print(f"\nERROR File tidak ditemukan: {F_PROGRES}")

    if run_all or '--rekon' in args:
        if os.path.exists(F_REKON):
            update_rekon_sbr()
        else:
            print(f"\nERROR File tidak ditemukan: {F_REKON}")

    if run_all or '--sls' in args or '--open' in args:
        if os.path.exists(F_PROGRES):
            update_sls_open()
        else:
            print(f"\nERROR File tidak ditemukan: {F_PROGRES}")

    if run_all or '--subsls' in args:
        if os.path.exists(F_SUBSLS):
            update_subsls_belum_dikunjungi()
        else:
            print(f"\nERROR File tidak ditemukan: {F_SUBSLS}")

    update_cache_buster()

    print("\n" + "=" * 60)
    print("  SELESAI! " + datetime.datetime.now().strftime('%d %b %Y, %H:%M:%S WIB'))
    print("=" * 60 + "\n")


if __name__ == '__main__':
    main()
