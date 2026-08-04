import pandas as pd
import json
import base64
import gzip
import glob

print("1. Membaca muatan_sls_72 2.xlsx (Target Awal)...")
df_awal = pd.read_excel('muatan/muatan_sls_72 2.xlsx', dtype={'idsubsls_25_2': str})
df_awal['sls_id'] = df_awal['idsubsls_25_2'].str.strip()
df_awal['target_awal'] = df_awal['jml_utp_subsektor'].fillna(0) + df_awal['Total_usaha_SBR'].fillna(0) + df_awal['keluarga'].fillna(0)

print("2. Membaca Rekap SBR, UTP, Keluarga_*.xlsx (Realisasi)...")
df_real = pd.read_excel(max(glob.glob('Rekap SBR, UTP, Keluarga_*.xlsx')))
df_real['idsls_str'] = df_real['level_5_full_code'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
df_real['kdsubsls_str'] = pd.to_numeric(df_real['level_6_code'], errors='coerce').fillna(0).astype(int).astype(str).str.zfill(2)
df_real['sls_id'] = df_real['idsls_str'] + df_real['kdsubsls_str']
df_real['realisasi'] = df_real['total_utp'].fillna(0) + df_real['total_sbr'].fillna(0) + df_real['total_keluarga'].fillna(0)

print("3. Membaca pemetaan SLS ke Petugas dari granular_assignments_se_umum_*.json...")
sql_assignments = []
sql_specific_targets = []
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
        email = str(email).lower().strip()
        
        if len(sls_id) == 16:
            sql_assignments.append({'sls_id': sls_id, 'email': email})
        else:
            sql_specific_targets.append({'email': email, 'tugas_spesifik': 1})

df_sql = pd.DataFrame(sql_assignments).drop_duplicates()
df_specific = pd.DataFrame(sql_specific_targets)

# Menghitung weight (bobot) per petugas di suatu SLS untuk mencegah double counting
if not df_sql.empty:
    df_sql['weight'] = 1.0 / df_sql.groupby('sls_id')['email'].transform('count')
else:
    df_sql['weight'] = 1.0

print("4. Menggabungkan data level SLS...")
# Merge awal dan real
df_sls = pd.merge(df_awal[['sls_id', 'target_awal', 'jml_utp_subsektor', 'Total_usaha_SBR', 'keluarga', 'nmkab', 'nmkec', 'nmdesa', 'nmsls']], 
                  df_real[['sls_id', 'realisasi', 'total_utp', 'total_sbr', 'total_keluarga']], on='sls_id', how='outer').fillna(0)

# Fill missing region names for those that only exist in realisasi
with open('region_map_sulteng_full.json') as f:
    region_map = json.load(f)

def fill_names(row):
    sls = str(row['sls_id'])
    if sls == '0' or sls == 'nan' or len(sls) < 10 or row['nmkab'] != 0: 
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

# Apply weights to prevent double counting
metrics_cols = ['target_awal', 'realisasi', 'jml_utp_subsektor', 'Total_usaha_SBR', 'keluarga', 'total_utp', 'total_sbr', 'total_keluarga']
for col in metrics_cols:
    df_petugas_map[col] = df_petugas_map[col] * df_petugas_map['weight']

df_petugas = df_petugas_map.groupby('email').agg({col: 'sum' for col in metrics_cols}).reset_index()

# Tambahkan tugas spesifik yang bukan 16 digit
if not df_specific.empty:
    df_specific_agg = df_specific.groupby('email').agg({'tugas_spesifik': 'sum'}).reset_index()
    df_petugas = pd.merge(df_petugas, df_specific_agg, on='email', how='outer').fillna(0)
else:
    df_petugas['tugas_spesifik'] = 0

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
