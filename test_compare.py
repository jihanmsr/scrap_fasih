import pandas as pd
import json
import base64
import gzip
import glob

# 1. Load Rekap UTP dan SBR
df_rekap = pd.read_excel('muatan/Rekap UTP dan SBR.xlsx')
df_rekap['sls_id'] = df_rekap['level_6_full_code'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
df_rekap['total_muatan'] = df_rekap['total_sbr'] + df_rekap['total_utp']

# 2. Count assignments per SLS in granular_assignments_se_umum
sls_counts = {}
for file in glob.glob('granular_assignments_se_umum_*.json'):
    with open(file) as f:
        d = json.load(f)
    if 'compressed_data' not in d: continue
    
    data = json.loads(gzip.decompress(base64.b64decode(d['compressed_data'])))
    targets = data.get('targets', [])
    for t in targets:
        target_str = str(t[1])
        sls_id = target_str.split(' - ')[0].strip()
        sls_counts[sls_id] = sls_counts.get(sls_id, 0) + 1

df_assign = pd.DataFrame(list(sls_counts.items()), columns=['sls_id', 'total_assigned'])

# 3. Merge
df_merged = pd.merge(df_rekap[['sls_id', 'total_muatan']], df_assign, on='sls_id', how='outer').fillna(0)
df_merged['diff'] = df_merged['total_muatan'] - df_merged['total_assigned']

diff_count = len(df_merged[df_merged['diff'] != 0])
print(f"Total SLS with diff != 0: {diff_count} out of {len(df_merged)}")
print(df_merged[df_merged['diff'] != 0].head(10))

