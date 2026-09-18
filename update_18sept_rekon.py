"""
UPDATE SBR, UTP, KELUARGA - 18 SEPTEMBER 2026
======================================================
1. Membaca Excel Rekap SBR, UTP, Keluarga dari file:
   'rekap_sbr_utp_keluarga_18 sept.xlsx'
   -> Rekap SBR, UTP, Keluarga_20260918.xlsx
   -> Rekap SBR, UTP, Keluarga_18_09.xlsx
2. Membuat Rekap Kab/Kot:
   -> Laporan_Rekap_KabKot_SBR_UTP_Keluarga_18_09.xlsx
3. Memperbarui Rekon SLS & Petugas:
   -> rekon_data.js (window.rekonSlsData & window.rekonPetugasData)
4. Memperbarui Prioritas Penyisiran Keluarga:
   -> penyisiran_keluarga_data.js
   -> Prioritas_Penyisiran_Keluarga_SE2026_18Sep.xlsx
5. Update Cache Buster di index.html
"""

import sys
import os
import re
import json
import time
import glob
import base64
import gzip
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_EXCEL = os.path.join(BASE_DIR, 'rekap_sbr_utp_keluarga_18 sept.xlsx')

# File muatan
F_MUATAN = os.path.join(BASE_DIR, 'muatan', 'muatan_sls_72 2.xlsx')
if not os.path.exists(F_MUATAN):
    F_MUATAN = os.path.join(BASE_DIR, 'muatan_sls_72.xlsx')

REGION_MAP_PATH = os.path.join(BASE_DIR, 'region_map_sulteng_full.json')


def step1_load_and_save():
    print("\n" + "=" * 60)
    print("  [1/5] MEMBACA FILE EXCEL REKAP 18 SEPTEMBER 2026")
    print("=" * 60)

    if not os.path.exists(SOURCE_EXCEL):
        raise FileNotFoundError(f"File tidak ditemukan: {SOURCE_EXCEL}")

    print(f"    Membaca: {os.path.basename(SOURCE_EXCEL)}...")
    df = pd.read_excel(SOURCE_EXCEL, dtype={'level_5_full_code': str, 'level_6_code': str})
    print(f"    Total baris dibaca: {len(df):,}")

    # Standardize types and strings
    df['level_5_full_code'] = df['level_5_full_code'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
    df['level_6_code'] = pd.to_numeric(df['level_6_code'], errors='coerce').fillna(0).astype(int).astype(str).str.zfill(2)

    for c in ['total_sbr', 'total_utp', 'total_keluarga']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0).astype(int)

    df = df.sort_values(by=['level_5_full_code', 'level_6_code'])

    # Save to standard output Excel files
    out_xlsx_1 = os.path.join(BASE_DIR, 'Rekap SBR, UTP, Keluarga_20260918.xlsx')
    out_xlsx_2 = os.path.join(BASE_DIR, 'Rekap SBR, UTP, Keluarga_18_09.xlsx')

    print(f"    Menyimpan ke {os.path.basename(out_xlsx_1)}...")
    df.to_excel(out_xlsx_1, index=False)
    print(f"    Menyimpan ke {os.path.basename(out_xlsx_2)}...")
    df.to_excel(out_xlsx_2, index=False)

    print(f"    OK File Rekap SBR, UTP, Keluarga berhasil disimpan!")
    return df


def step2_rekap_kabkot(df_real):
    print("\n" + "=" * 60)
    print("  [2/5] MEMBUAT LAPORAN REKAP KAB/KOTA (18 SEPTEMBER)")
    print("=" * 60)

    with open(REGION_MAP_PATH, 'r', encoding='utf-8') as f:
        region_map = json.load(f)

    def get_kab_name(kab_code):
        kab_data = region_map.get('kabupaten', {}).get(kab_code, {})
        return kab_data.get('kab_name', f'[{kab_code[-2:]}] KABUPATEN')

    df = df_real.copy()
    df['idsls_str'] = df['level_5_full_code'].astype(str).str.strip()
    df['Kode Kab'] = df['idsls_str'].str[:4]
    df['Nama Kab/Kota'] = df['Kode Kab'].apply(get_kab_name)

    agg = {'total_utp': 'sum', 'total_sbr': 'sum', 'total_keluarga': 'sum'}
    df_rekap = df.groupby(['Kode Kab', 'Nama Kab/Kota'], as_index=False).agg(agg)
    df_rekap = df_rekap.rename(columns={
        'total_utp': 'Total UTP',
        'total_sbr': 'Total SBR',
        'total_keluarga': 'Total Keluarga'
    })
    df_rekap = df_rekap[df_rekap['Kode Kab'].str.len() == 4].sort_values('Kode Kab')

    df_total = pd.DataFrame([{
        'Kode Kab': 'TOTAL',
        'Nama Kab/Kota': 'SULAWESI TENGAH',
        'Total UTP': df_rekap['Total UTP'].sum(),
        'Total SBR': df_rekap['Total SBR'].sum(),
        'Total Keluarga': df_rekap['Total Keluarga'].sum()
    }])
    df_rekap = pd.concat([df_rekap, df_total], ignore_index=True)

    out_file = os.path.join(BASE_DIR, 'Laporan_Rekap_KabKot_SBR_UTP_Keluarga_18_09.xlsx')
    df_rekap.to_excel(out_file, index=False)
    print(f"    OK Laporan Rekap Kab/Kot berhasil disimpan: {os.path.basename(out_file)}")
    print("\nRingkasan Per Kabupaten/Kota:")
    for _, r in df_rekap.iterrows():
        print(f"    {r['Kode Kab']:<6} {r['Nama Kab/Kota']:<26} | UTP: {r['Total UTP']:>7,d} | SBR: {r['Total SBR']:>7,d} | Keluarga: {r['Total Keluarga']:>7,d}")

    return df_rekap


def step3_update_rekon_js(df_real):
    print("\n" + "=" * 60)
    print("  [3/5] MEMPERBARUI rekon_data.js (SLS & PETUGAS)")
    print("=" * 60)

    with open(REGION_MAP_PATH, 'r', encoding='utf-8') as f:
        region_map = json.load(f)

    # 1. SLS ID realisasi
    df_real['idsls_str'] = df_real['level_5_full_code'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
    df_real['kdsubsls_str'] = pd.to_numeric(df_real['level_6_code'], errors='coerce').fillna(0).astype(int).astype(str).str.zfill(2)
    df_real['sls_id'] = df_real['idsls_str'] + df_real['kdsubsls_str']
    df_real['realisasi'] = df_real['total_utp'].fillna(0) + df_real['total_sbr'].fillna(0) + df_real['total_keluarga'].fillna(0)

    # 2. Muatan awal
    print(f"    Membaca target awal dari: {os.path.basename(F_MUATAN)}...")
    if os.path.exists(F_MUATAN):
        df_awal = pd.read_excel(F_MUATAN, dtype={'idsubsls_25_2': str})
        df_awal['sls_id'] = df_awal['idsubsls_25_2'].astype(str).str.strip()
        df_awal['target_awal'] = df_awal['jml_utp_subsektor'].fillna(0) + df_awal['Total_usaha_SBR'].fillna(0) + df_awal['keluarga'].fillna(0)
    else:
        df_awal = pd.DataFrame(columns=['sls_id', 'target_awal', 'jml_utp_subsektor', 'Total_usaha_SBR', 'keluarga', 'nmkab', 'nmkec', 'nmdesa', 'nmsls'])

    # 3. SQL Assignments mapping (PPL)
    print("    Membaca pemetaan penugasan petugas dari granular_assignments_se_umum_*.json...")
    sql_assignments = []
    all_emails = set()
    for file in glob.glob(os.path.join(BASE_DIR, 'granular_assignments_se_umum_*.json')):
        try:
            with open(file, 'r', encoding='utf-8') as f:
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
            pass

    df_sql = pd.DataFrame(sql_assignments).drop_duplicates() if sql_assignments else pd.DataFrame(columns=['sls_id', 'email'])
    df_sql['weight'] = 1.0

    # 4. Merge awal dan realisasi
    awal_cols = [c for c in ['sls_id', 'target_awal', 'jml_utp_subsektor', 'Total_usaha_SBR', 'keluarga', 'nmkab', 'nmkec', 'nmdesa', 'nmsls'] if c in df_awal.columns]
    df_sls = pd.merge(
        df_awal[awal_cols] if awal_cols else df_awal,
        df_real[['sls_id', 'realisasi', 'total_utp', 'total_sbr', 'total_keluarga']],
        on='sls_id',
        how='outer'
    ).fillna(0)

    def fill_names(row):
        sls = str(row['sls_id'])
        if sls in ('0', 'nan') or len(sls) < 10:
            return row
        if 'nmkab' in row.index and row['nmkab'] != 0 and row['nmkab'] != '-':
            return row
        kab = sls[:4]
        kec = sls[:7]
        desa = sls[:10]
        kab_data = region_map.get('kabupaten', {}).get(kab, {})
        if 'nmkab' in row.index:
            row['nmkab'] = kab_data.get('kab_name', '-')
        kec_data = kab_data.get('kecamatan', {}).get(kec, {})
        if 'nmkec' in row.index:
            row['nmkec'] = kec_data.get('kec_name', '-')
        desa_data = kec_data.get('desa', {}).get(desa, {})
        if 'nmdesa' in row.index:
            row['nmdesa'] = desa_data.get('desa_name', '-')
        return row

    df_sls = df_sls.apply(fill_names, axis=1)
    if 'nmsls' in df_sls.columns:
        df_sls['nmsls'] = df_sls['nmsls'].replace(0, '-')
    df_sls['diff'] = df_sls['realisasi'] - df_sls.get('target_awal', 0)

    # 5. Petugas aggregations
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
    js_content = "window.rekonSlsData = " + df_sls.to_json(orient='records') + ";\n"
    js_content += "window.rekonPetugasData = " + df_petugas.to_json(orient='records') + ";\n"
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(js_content)

    print(f"    OK rekon_data.js diperbarui: {len(df_sls):,} SLS, {len(df_petugas):,} Petugas")


def step4_update_penyisiran_keluarga():
    print("\n" + "=" * 60)
    print("  [4/5] MEMPERBARUI PRIORITAS PENYISIRAN KELUARGA")
    print("=" * 60)

    # Update generate_penyisiran_keluarga.py to reference latest rekap file
    py_path = os.path.join(BASE_DIR, 'generate_penyisiran_keluarga.py')
    with open(py_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Update to 20260918
    content = re.sub(
        r'rekap_file\s*=\s*os\.path\.join\(base_dir,\s*["\']Rekap SBR, UTP, Keluarga_[^"\']+\.xlsx["\']\)',
        'rekap_file = os.path.join(base_dir, "Rekap SBR, UTP, Keluarga_20260918.xlsx")',
        content
    )
    content = re.sub(
        r'output_excel\s*=\s*os\.path\.join\(base_dir,\s*["\']Prioritas_Penyisiran_Keluarga_SE2026_[^"\']+\.xlsx["\']\)',
        'output_excel = os.path.join(base_dir, "Prioritas_Penyisiran_Keluarga_SE2026_18Sep.xlsx")',
        content
    )
    content = re.sub(
        r'Update \d+ September 2026',
        'Update 18 September 2026',
        content
    )

    with open(py_path, 'w', encoding='utf-8') as f:
        f.write(content)

    import subprocess
    subprocess.run([sys.executable, py_path], check=True)
    print("    OK Prioritas Penyisiran Keluarga berhasil diperbarui!")


def step5_update_cache_buster():
    print("\n" + "=" * 60)
    print("  [5/5] MEMPERBARUI CACHE BUSTER INDEX.HTML")
    print("=" * 60)

    idx_path = os.path.join(BASE_DIR, 'index.html')
    with open(idx_path, 'r', encoding='utf-8') as f:
        html = f.read()

    ts = str(int(time.time()))
    # Update script query versions
    html = re.sub(r'rekon_data\.js\?v=[^"\'\s>]+', f'rekon_data.js?v={ts}_v1809', html)
    html = re.sub(r'penyisiran_keluarga_data\.js\?v=[^"\'\s>]+', f'penyisiran_keluarga_data.js?v={ts}_v1809', html)
    html = re.sub(r'penyisiran_keluarga\.js\?v=[^"\'\s>]+', f'penyisiran_keluarga.js?v={ts}_v1809', html)

    with open(idx_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"    OK Cache buster index.html diperbarui ke versi v={ts}_v1809")


def main():
    start_time = time.time()
    print("\n" + "#" * 65)
    print("  MEMULAI PEMBARUAN DATA SBR, UTP, KELUARGA (18 SEPTEMBER 2026)")
    print("#" * 65)

    df_real = step1_load_and_save()
    step2_rekap_kabkot(df_real)
    step3_update_rekon_js(df_real)
    step4_update_penyisiran_keluarga()
    step5_update_cache_buster()

    elapsed = time.time() - start_time
    print("\n" + "=" * 65)
    print(f"  SEMUA DATA TABULASI BERHASIL DIUPDATE DALAM {elapsed:.2f} DETIK!")
    print("=" * 65 + "\n")


if __name__ == '__main__':
    main()
