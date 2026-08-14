import pandas as pd
import json

df = pd.read_excel('/Users/jihanmaisaroh/scrap_fasih/SubSLS_Open.xlsx')

# Calculate total prelists per Sub-SLS
total_per_subsls = df.groupby(['kode_kab', 'kabupaten', 'kode_kecamatan', 'kecamatan', 'kode_desa', 'desa', 'kode_sls', 'sls', 'kode_sub_sls', 'sub_sls']).size().reset_index(name='total_prelist')

# Calculate unassigned per Sub-SLS
df['is_unassigned'] = df['nama_petugas'].isna()
unassigned_per_subsls = df[df['is_unassigned']].groupby('kode_sub_sls').size().reset_index(name='unassigned_prelist')

# Merge
merged = pd.merge(total_per_subsls, unassigned_per_subsls, on='kode_sub_sls', how='left')
merged['unassigned_prelist'] = merged['unassigned_prelist'].fillna(0).astype(int)

# Convert to dict format
data_list = merged.to_dict('records')

with open('/Users/jihanmaisaroh/scrap_fasih/open_subsls_data.js', 'w', encoding='utf-8') as f:
    f.write('window.OPEN_SUBSLS_DATA = ' + json.dumps(data_list) + ';')

print("Generated open_subsls_data.js successfully!")
