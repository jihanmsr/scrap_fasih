import pandas as pd
import json
import base64
import gzip
import glob

print("1. Membaca muatan_sls_72 2.xlsx (Target Awal)...")
df_awal = pd.read_excel('muatan/muatan_sls_72 2.xlsx')
df_awal['sls_id'] = df_awal['idsubsls_25_2'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
df_awal['target_awal'] = df_awal['jml_utp_subsektor'].fillna(0) + df_awal['Total_usaha_SBR'].fillna(0)

print("2. Membaca Rekap SBR, UTP, Keluarga.xlsx (Realisasi)...")
df_real = pd.read_excel('Rekap SBR, UTP, Keluarga.xlsx')
df_real['sls_id'] = df_real['idsls'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
df_real['realisasi'] = df_real['total_utp'].fillna(0) + df_real['total_sbr'].fillna(0)

print("3. Membaca pemetaan SLS ke Petugas dari granular_assignments_se_umum_*.json...")
sql_assignments = []
for file in glob.glob('granular_assignments_se_umum_*.json'):
    with open(file) as f:
        d = json.load(f)
    if 'compressed_data' not in d: continue
    
    data = json.loads(gzip.decompress(base64.b64decode(d['compressed_data'])))
    petugas_list = data.get('petugas', [])
    
    for t in data.get('targets', []):
        target_str = str(t[1])
        sls_id = target_str.split(' - ')[0].strip()
        pid = t[-1]
        try:
            email = petugas_list[pid][0] if isinstance(petugas_list[pid], list) else petugas_list[pid]
        except:
            email = '-'
        sql_assignments.append({'sls_id': sls_id, 'email': email})

df_sql = pd.DataFrame(sql_assignments).drop_duplicates()
df_sql['email'] = df_sql['email'].astype(str).str.lower().str.strip()

print("4. Menggabungkan data level SLS...")
# Merge awal dan real
df_sls = pd.merge(df_awal[['sls_id', 'target_awal', 'jml_utp_subsektor', 'Total_usaha_SBR', 'keluarga', 'nmkab', 'nmkec', 'nmdesa', 'nmsls']], 
                  df_real[['sls_id', 'realisasi', 'total_utp', 'total_sbr', 'total_keluarga']], on='sls_id', how='outer').fillna(0)

# Fill missing region names for those that only exist in realisasi
with open('region_map_sulteng_full.json') as f:
    region_map = json.load(f)

def fill_names(row):
    sls = row['sls_id']
    if len(sls) < 10 or row['nmkab'] != 0: 
        return row
    
    kab, kec, desa = sls[:4], sls[:7], sls[:10]
    kab_data = region_map.get('kabupaten', {}).get(kab, {})
    row['nmkab'] = kab_data.get('kab_name', '-')
    kec_data = kab_data.get('kecamatan', {}).get(kec, {})
    row['nmkec'] = kec_data.get('kec_name', '-')
    desa_data = kec_data.get('desa', {}).get(desa, {})
    row['nmdesa'] = desa_data.get('desa_name', '-')
    return row

df_sls = df_sls.apply(fill_names, axis=1)
df_sls['nmsls'] = df_sls['nmsls'].replace(0, '-')
df_sls['diff'] = df_sls['realisasi'] - df_sls['target_awal']

print("5. Menggabungkan data level Petugas...")
df_petugas_map = pd.merge(df_sql, df_sls[['sls_id', 'target_awal', 'realisasi', 'jml_utp_subsektor', 'Total_usaha_SBR', 'keluarga', 'total_utp', 'total_sbr', 'total_keluarga']], on='sls_id', how='left').fillna(0)
df_petugas = df_petugas_map.groupby('email').agg({
    'target_awal': 'sum',
    'realisasi': 'sum',
    'jml_utp_subsektor': 'sum',
    'Total_usaha_SBR': 'sum',
    'keluarga': 'sum',
    'total_utp': 'sum',
    'total_sbr': 'sum',
    'total_keluarga': 'sum'
}).reset_index()

# Rename columns to match what rekon.js Petugas table expects for sorting
df_petugas = df_petugas.rename(columns={
    'jml_utp_subsektor': 'total_muatan_assigned',
    'total_utp': 'total_usaha'
})
df_petugas['diff'] = df_petugas['realisasi'] - df_petugas['target_awal']

print("6. Menyimpan ke rekon_data.js...")
js_content = "window.rekonSlsData = " + df_sls.to_json(orient='records') + ";\n"
js_content += "window.rekonPetugasData = " + df_petugas.to_json(orient='records') + ";\n"

with open('rekon_data.js', 'w') as f:
    f.write(js_content)

print("✅ Selesai!")
