import pandas as pd
import numpy as np

def clean_code(col):
    return col.astype(str).str.replace(r'\.0$', '', regex=True).str.strip()

# ==========================================
# 1. LOAD DATA
# ==========================================
print("Loading data...")
df_muatan = pd.read_excel('/Users/jihanmaisaroh/scrap_fasih/muatan_sls_72.xlsx', sheet_name=0)
df_rekap = pd.read_excel('/Users/jihanmaisaroh/scrap_fasih/Rekap UTP dan SBR.xlsx', sheet_name=0)
df_fasih = pd.read_csv('/Users/jihanmaisaroh/scrap_fasih/fast_petugas_all_2026-07-29.csv').drop_duplicates()
df_sql5 = pd.read_csv('/Users/jihanmaisaroh/scrap_fasih/sqllab_5_monitoring_jumlah_usaha_berdasarkan_status_keberadaannya_perpetugas_20260729T070546.csv')
df_sql6 = pd.read_csv('/Users/jihanmaisaroh/scrap_fasih/sqllab_6_monitoring_jumlah_keluarga_berdasarkan_status_keberadaannya_perpetugas_7201_20260729T072437.csv')

# ==========================================
# 2. PERSIAPAN DATA SLS
# ==========================================
# Format Region Code / SLS ID
df_muatan['sls_id'] = clean_code(df_muatan['idsubsls_25_2'])
df_rekap['sls_id'] = clean_code(df_rekap['level_6_full_code'])
df_fasih['sls_id'] = clean_code(df_fasih['Region Code'])

# Hanya ambil Pencacah untuk Fasih (agar target tidak dobel dengan Pengawas)
df_fasih_pencacah = df_fasih[df_fasih['Role'].str.upper() == 'PENCACAH']
df_fasih_sls_target = df_fasih_pencacah.groupby('sls_id')['Total Target'].sum().reset_index().rename(columns={'Total Target': 'fasih_target_pencacah'})

# ==========================================
# 3. SHEET 1: ANALISIS LEVEL SLS
# ==========================================
print("Memproses Analisis Level SLS...")
# Merge Muatan dan Rekap
df_sls_level = pd.merge(
    df_muatan[['sls_id', 'nmkab', 'nmkec', 'nmdesa', 'nmsls', 'jml_utp_subsektor', 'Total_usaha_SBR', 'keluarga']],
    df_rekap[['sls_id', 'total_utp', 'total_sbr']],
    on='sls_id', how='outer'
).fillna(0)

# Merge dengan Target Fasih
df_sls_level = pd.merge(df_sls_level, df_fasih_sls_target, on='sls_id', how='left').fillna(0)

# Hitung Total Muatan (UTP + SBR + Keluarga)
df_sls_level['total_muatan'] = df_sls_level['jml_utp_subsektor'] + df_sls_level['Total_usaha_SBR'] + df_sls_level['keluarga']

# Hitung Diff Muatan vs Rekap
df_sls_level['diff_utp_rekap_vs_muatan'] = df_sls_level['total_utp'] - df_sls_level['jml_utp_subsektor']
df_sls_level['diff_sbr_rekap_vs_muatan'] = df_sls_level['total_sbr'] - df_sls_level['Total_usaha_SBR']

# Hitung Diff Fasih vs Muatan
df_sls_level['diff_fasih_vs_muatan_total'] = df_sls_level['fasih_target_pencacah'] - df_sls_level['total_muatan']

# Sortir berdasarkan kabupaten dan kecamatan
df_sls_level = df_sls_level.sort_values(['nmkab', 'nmkec'])

# ==========================================
# 4. PERSIAPAN DATA SQL LAB
# ==========================================
df_sql5['email'] = df_sql5['email'].astype(str).str.lower().str.strip()
df_sql6['email'] = df_sql6['email'].astype(str).str.lower().str.strip()

sql5_grouped = df_sql5.groupby('email')['total_usaha'].sum().reset_index()
sql6_grouped = df_sql6.groupby('email')['total_keluarga'].sum().reset_index()

df_sql_gabungan = pd.merge(sql5_grouped, sql6_grouped, on='email', how='outer').fillna(0)
df_sql_gabungan['total_sqllab'] = df_sql_gabungan['total_usaha'] + df_sql_gabungan['total_keluarga']

# ==========================================
# 5. SHEET 2: ANALISIS LEVEL PETUGAS
# ==========================================
print("Memproses Analisis Level Petugas...")
df_fasih['email'] = df_fasih['Email'].astype(str).str.lower().str.strip()
df_fasih_pencacah_only = df_fasih[df_fasih['Role'].str.upper() == 'PENCACAH']

# A. Agregasi Fasih per Petugas
df_fasih_petugas = df_fasih_pencacah_only.groupby('email')['Total Target'].sum().reset_index().rename(columns={'Total Target': 'total_fasih'})

# B. Hitung Muatan untuk masing-masing Petugas
# Karena 1 petugas bisa pegang banyak SLS, dan 1 SLS bisa dipegang >1 petugas (?), kita join berdasar Fasih
df_petugas_sls_mapping = df_fasih_pencacah_only[['email', 'sls_id']].drop_duplicates()
df_muatan_petugas = pd.merge(df_petugas_sls_mapping, df_sls_level[['sls_id', 'total_muatan']], on='sls_id', how='left')
df_muatan_petugas_grouped = df_muatan_petugas.groupby('email')['total_muatan'].sum().reset_index().rename(columns={'total_muatan': 'total_muatan_assigned'})

# C. Merge Semuanya (Fasih + Muatan + SQL Lab)
df_petugas_level = pd.merge(df_fasih_petugas, df_muatan_petugas_grouped, on='email', how='outer').fillna(0)
df_petugas_level = pd.merge(df_petugas_level, df_sql_gabungan, on='email', how='outer').fillna(0)

# D. Hitung Diff
df_petugas_level['diff_fasih_vs_muatan'] = df_petugas_level['total_fasih'] - df_petugas_level['total_muatan_assigned']
df_petugas_level['diff_fasih_vs_sqllab'] = df_petugas_level['total_fasih'] - df_petugas_level['total_sqllab']

# Filter out petugas dengan target 0 semua
df_petugas_level = df_petugas_level[(df_petugas_level['total_fasih'] > 0) | (df_petugas_level['total_muatan_assigned'] > 0) | (df_petugas_level['total_sqllab'] > 0)]

# ==========================================
# 6. EXPORT KE EXCEL
# ==========================================
output_path = '/Users/jihanmaisaroh/scrap_fasih/Analisis_Lintas_Sistem_Sulteng.xlsx'
print(f"Menyimpan ke Excel: {output_path}")

with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
    df_sls_level.to_excel(writer, sheet_name='Analisis_per_SLS', index=False)
    df_petugas_level.to_excel(writer, sheet_name='Analisis_per_Petugas', index=False)

print("Selesai! File berhasil dibuat.")
