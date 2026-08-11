import pandas as pd
import json

df_real = pd.read_excel('Rekap SBR, UTP, Keluarga_10_08.xlsx')
df_real['idsls_str'] = df_real['level_5_full_code'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()

with open('region_map_sulteng_full.json') as f:
    region_map = json.load(f)

def get_kab_name(kab_code):
    kab_data = region_map.get('kabupaten', {}).get(kab_code, {})
    return kab_data.get('kab_name', '-')

df_real['Kode Kab'] = df_real['idsls_str'].str[:4]
df_real['Nama Kab/Kota'] = df_real['Kode Kab'].apply(get_kab_name)

agg = {
    'total_utp': 'sum',
    'total_sbr': 'sum',
    'total_keluarga': 'sum'
}

df_rekap = df_real.groupby(['Kode Kab', 'Nama Kab/Kota'], as_index=False).agg(agg)
df_rekap = df_rekap.rename(columns={
    'total_utp': 'Total UTP',
    'total_sbr': 'Total SBR',
    'total_keluarga': 'Total Keluarga'
})
# drop empty or invalid kab codes
df_rekap = df_rekap[df_rekap['Kode Kab'].str.len() == 4]
df_rekap = df_rekap.sort_values('Kode Kab')

# Total row
df_total = pd.DataFrame([{
    'Kode Kab': 'TOTAL',
    'Nama Kab/Kota': 'SULAWESI TENGAH',
    'Total UTP': df_rekap['Total UTP'].sum(),
    'Total SBR': df_rekap['Total SBR'].sum(),
    'Total Keluarga': df_rekap['Total Keluarga'].sum()
}])
df_rekap = pd.concat([df_rekap, df_total], ignore_index=True)

out_file = 'Laporan_Rekap_KabKot_SBR_UTP_Keluarga_10_08.xlsx'
df_rekap.to_excel(out_file, index=False)
print("Berhasil dibuat:", out_file)
