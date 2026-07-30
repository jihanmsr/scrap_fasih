import pandas as pd
import json
import base64
import gzip
import glob
import os

print("1. Membaca Rekap UTP dan SBR.xlsx...")
df_rekap = pd.read_excel('muatan/Rekap UTP dan SBR.xlsx')
df_rekap['sls_id'] = df_rekap['level_6_full_code'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
df_rekap['total_muatan'] = df_rekap['total_sbr'] + df_rekap['total_utp']

print("2. Membaca granular_assignments_se_umum_*.json...")
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

df_sql = pd.DataFrame(sql_assignments)
df_sql['email'] = df_sql['email'].astype(str).str.lower().str.strip()

print("3. Agregasi Level SLS...")
sls_sql = df_sql.groupby('sls_id').size().reset_index(name='total_sqllab')
df_sls = pd.merge(df_rekap[['sls_id', 'total_muatan', 'total_utp', 'total_sbr']], sls_sql, on='sls_id', how='outer').fillna(0)
df_sls['diff_muatan_vs_sqllab'] = df_sls['total_muatan'] - df_sls['total_sqllab']

# Ambil region name dari region_map
with open('region_map_sulteng_full.json') as f:
    region_map = json.load(f)

# Lookup
def get_region_names(sls):
    kab, kec, desa = sls[:4], sls[:7], sls[:10]
    res = {'nmkab': '-', 'nmkec': '-', 'nmdesa': '-'}
    kab_data = region_map.get('kabupaten', {}).get(kab, {})
    res['nmkab'] = kab_data.get('kab_name', '-')
    kec_data = kab_data.get('kecamatan', {}).get(kec, {})
    res['nmkec'] = kec_data.get('kec_name', '-')
    desa_data = kec_data.get('desa', {}).get(desa, {})
    res['nmdesa'] = desa_data.get('desa_name', '-')
    return pd.Series(res)

print("4. Menambahkan nama wilayah...")
df_sls[['nmkab', 'nmkec', 'nmdesa']] = df_sls['sls_id'].apply(get_region_names)
df_sls['nmsls'] = '-' # Kita skip nmsls untuk kecepatan, atau bisa diisi dari rekap jika ada
df_sls = df_sls.sort_values(['nmkab', 'nmkec', 'nmdesa', 'sls_id'])

print("5. Agregasi Level Petugas...")
petugas_sql = df_sql.groupby('email').size().reset_index(name='total_sqllab')

# Cari assigned muatan per petugas
# Jika petugas pegang SLS A dan SLS B, muatannya = muatan SLS A + muatan SLS B
sls_petugas_mapping = df_sql[['email', 'sls_id']].drop_duplicates()
petugas_muatan = pd.merge(sls_petugas_mapping, df_rekap[['sls_id', 'total_muatan']], on='sls_id', how='left').fillna(0)
petugas_muatan_grouped = petugas_muatan.groupby('email')['total_muatan'].sum().reset_index().rename(columns={'total_muatan': 'total_muatan_assigned'})

df_petugas = pd.merge(petugas_sql, petugas_muatan_grouped, on='email', how='outer').fillna(0)
df_petugas['diff_muatan_vs_sqllab'] = df_petugas['total_muatan_assigned'] - df_petugas['total_sqllab']

print("6. Menyimpan ke rekon_data.js...")
js_content = "window.rekonSlsData = " + df_sls.to_json(orient='records') + ";\n"
js_content += "window.rekonPetugasData = " + df_petugas.to_json(orient='records') + ";\n"

with open('rekon_data.js', 'w') as f:
    f.write(js_content)

print("✅ Selesai!")
