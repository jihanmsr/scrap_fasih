import pandas as pd
import os

# --- 1. Load and process SQL Lab 5 (Usaha) ---
df_usaha = pd.read_csv('/Users/jihanmaisaroh/scrap_fasih/sqllab_5_monitoring_jumlah_usaha_berdasarkan_status_keberadaannya_perpetugas_20260729T070546.csv')
df_usaha['email'] = df_usaha['email'].astype(str).str.lower().str.strip()

usaha_cols = ['ditemukan', 'baru', 'tutup', 'ganda', 'tidak_ditemukan', 'belum_terisi', 'total_usaha']
agg_usaha = {col: 'sum' for col in usaha_cols}
agg_usaha['kecamatan'] = 'first'
df_usaha_grouped = df_usaha.groupby('email').agg(agg_usaha).reset_index()

rename_usaha = {col: f"usaha_{col}" for col in usaha_cols}
df_usaha_grouped = df_usaha_grouped.rename(columns=rename_usaha)

# --- 2. Load and process SQL Lab 6 (Keluarga) ---
df_kel = pd.read_csv('/Users/jihanmaisaroh/scrap_fasih/sqllab_6_monitoring_jumlah_keluarga_berdasarkan_status_keberadaannya_perpetugas_7201_20260729T072437.csv')
df_kel['email'] = df_kel['email'].astype(str).str.lower().str.strip()

kel_cols = ['ditemukan', 'tidak_ditemukan', 'baru', 'meninggal', 'tidak_eligible', 'keluarga_khusus', 'belum_terisi', 'total_keluarga']
agg_kel = {col: 'sum' for col in kel_cols}
df_kel_grouped = df_kel.groupby('email').agg(agg_kel).reset_index()

rename_kel = {col: f"keluarga_{col}" for col in kel_cols}
df_kel_grouped = df_kel_grouped.rename(columns=rename_kel)

# --- 3. Merge SQL Lab Usaha & Keluarga ---
df_sql_combined = pd.merge(df_usaha_grouped, df_kel_grouped, on='email', how='outer').fillna(0)
df_sql_combined['total_gabungan_sql'] = df_sql_combined['usaha_total_usaha'] + df_sql_combined['keluarga_total_keluarga']

# --- 4. Load and process Tarikan Fast (Only 7201) ---
df_fast = pd.read_csv('/Users/jihanmaisaroh/scrap_fasih/fast_petugas_all_2026-07-29.csv')

# !! INI KUNCINYA: DROP DUPLICATES SEBELUM DIJUMLAHKAN !!
df_fast = df_fast.drop_duplicates()

df_fast['email'] = df_fast['Email'].astype(str).str.lower().str.strip()
df_fast['Region Code'] = df_fast['Region Code'].astype(str)

# Filter 7201
df_fast = df_fast[df_fast['Region Code'].str.startswith('7201')]

fast_cols_to_sum = [
    'Total Target', 'OPEN', 'DRAFT', 'SUBMITTED BY Pencacah', 
    'SUBMITTED RESPONDENT', 'APPROVED BY Pengawas', 'REJECTED BY Pengawas',
    'REVOKED BY Pengawas', 'EDITED BY Pengawas', 'EDITED BY Admin Kabupaten',
    'REJECTED BY Admin Kabupaten', 'COMPLETED BY Admin Kabupaten'
]

df_fast_grouped = df_fast.groupby('email').agg({col: 'sum' for col in fast_cols_to_sum}).reset_index()

# --- 5. Buat Sheet Perbandingan / Selisih ---
df_selisih = pd.merge(df_sql_combined[['email', 'kecamatan', 'usaha_total_usaha', 'keluarga_total_keluarga', 'total_gabungan_sql']], 
                      df_fast_grouped[['email', 'Total Target']], 
                      on='email', how='outer').fillna(0)

df_selisih = df_selisih.rename(columns={'Total Target': 'total_target_fasih'})
df_selisih['selisih (SQL - Fasih)'] = df_selisih['total_gabungan_sql'] - df_selisih['total_target_fasih']

# Cek hasil:
print("Total Usaha + Keluarga (SQL):", df_selisih['total_gabungan_sql'].sum())
print("Total Target (Fasih) SETELAH drop duplicates:", df_selisih['total_target_fasih'].sum())

# --- 6. Export ke Excel ---
output_path = '/Users/jihanmaisaroh/scrap_fasih/Perbandingan_SQLLab_vs_Tarikan.xlsx'
with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
    df_selisih.to_excel(writer, sheet_name='Perbandingan_Selisih', index=False)
    df_sql_combined.to_excel(writer, sheet_name='SQL_Lab_Combined', index=False)
    df_fast_grouped.to_excel(writer, sheet_name='Tarikan_Fasih', index=False)
