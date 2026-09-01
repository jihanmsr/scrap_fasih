import re

with open('update_1sept_all.py', 'r') as f:
    content = f.read()

target = """    if df_prog is None:
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
        }"""

replacement = """    df_subsls = pd.read_excel(F_SUBSLS)
    df_subsls = df_subsls.fillna('')

    data_list = []
    highlighted_map = {}

    for _, row in df_subsls.iterrows():
        sls_16 = str(row['kode_sub_sls']).replace('.0', '').zfill(16)
        
        item = {
            'kode_kab': int(row['kode_kab']) if str(row['kode_kab']).isdigit() else row['kode_kab'],
            'kabupaten': str(row['kabupaten']),
            'kode_kecamatan': int(row['kode_kecamatan']) if str(row['kode_kecamatan']).isdigit() else row['kode_kecamatan'],
            'kecamatan': str(row['kecamatan']),
            'kode_desa': int(row['kode_desa']) if str(row['kode_desa']).isdigit() else row['kode_desa'],
            'desa': str(row['desa']),
            'kode_sls': int(row['kode_sls']) if str(row['kode_sls']).isdigit() else row['kode_sls'],
            'sls': str(row['sls']),
            'kode_sub_sls': int(row['kode_sub_sls']) if str(row['kode_sub_sls']).isdigit() else row['kode_sub_sls'],
            'nama_sub_sls': str(row['nama_sub_sls']),
            'nama_petugas': str(row['nama_petugas']) if row['nama_petugas'] else None,
            'jumlah_prelist': int(row['jumlah_prelist']) if str(row['jumlah_prelist']).isdigit() else 0
        }
        data_list.append(item)

        highlighted_map[sls_16] = {
            'kode_kab': str(item['kode_kab']),
            'kabupaten': item['kabupaten'],
            'kode_kecamatan': str(item['kode_kecamatan']),
            'kecamatan': item['kecamatan'],
            'kode_desa': str(item['kode_desa']),
            'desa': item['desa'],
            'kode_sls': str(item['kode_sls']),
            'sls': item['sls'],
            'kode_sub_sls': str(item['kode_sub_sls']),
            'nama_sub_sls': item['nama_sub_sls'],
            'nama_petugas': item['nama_petugas'] or '',
            'jumlah_prelist': str(item['jumlah_prelist'])
        }"""

new_content = content.replace(target, replacement)
with open('update_1sept_all.py', 'w') as f:
    f.write(new_content)
