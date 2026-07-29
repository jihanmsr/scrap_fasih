import pandas as pd
import sys

# Load SQLLab (7201 only)
df_sql = pd.read_excel('/Users/jihanmaisaroh/scrap_fasih/sqllab_untitled_query_7_20260729T135455.xlsx')
df_sql = df_sql[df_sql['level_6_full_code'].astype(str).str.startswith('7201')]

sql_cols = ['open', 'draft', 'submitted_respondent', 'submitted_by_pencacah', 'edited_by_pengawas', 'rejected_by_pengawas', 'approved_by_pengawas', 'revoked_by_pengawas', 'edited_by_admin_kabupaten', 'rejected_by_admin_kabupaten', 'revoked_by_admin_kabupaten', 'completed_by_admin_kabupaten']
df_sql['total_target'] = df_sql[sql_cols].sum(axis=1)

# Aggregate SQLLab Pencacah
sql_pencacah = df_sql.groupby('pencacah_email')['total_target'].sum().reset_index()
sql_pencacah.rename(columns={'pencacah_email': 'Email', 'total_target': 'Target_SQLLab'}, inplace=True)
sql_pencacah['Email'] = sql_pencacah['Email'].astype(str).str.strip().str.lower()
sql_pencacah = sql_pencacah[sql_pencacah['Email'] != 'nan']

# Aggregate SQLLab Pengawas
sql_pengawas = df_sql.groupby('pengawas_email')['total_target'].sum().reset_index()
sql_pengawas.rename(columns={'pengawas_email': 'Email', 'total_target': 'Target_SQLLab'}, inplace=True)
sql_pengawas['Email'] = sql_pengawas['Email'].astype(str).str.strip().str.lower()
sql_pengawas = sql_pengawas[sql_pengawas['Email'] != 'nan']

# Load FASIH (7201 only)
df_csv = pd.read_csv('/Users/jihanmaisaroh/scrap_fasih/fast_petugas_all_2026-07-29.csv')
df_csv = df_csv[df_csv['Region Code'].astype(str).str.startswith('7201')]
df_csv['Email'] = df_csv['Email'].astype(str).str.strip().str.lower()

# Aggregate FASIH Pencacah
df_csv_pencacah = df_csv[df_csv['Role'].str.upper() == 'PENCACAH']
fasih_pencacah = df_csv_pencacah.groupby('Email')['Total Target'].sum().reset_index()
fasih_pencacah.rename(columns={'Total Target': 'Target_FASIH'}, inplace=True)

# Aggregate FASIH Pengawas
df_csv_pengawas = df_csv[df_csv['Role'].str.upper() == 'PENGAWAS']
fasih_pengawas = df_csv_pengawas.groupby('Email')['Total Target'].sum().reset_index()
fasih_pengawas.rename(columns={'Total Target': 'Target_FASIH'}, inplace=True)

# Merge Pencacah
merge_pencacah = pd.merge(fasih_pencacah, sql_pencacah, on='Email', how='outer').fillna(0)
merge_pencacah['Selisih'] = merge_pencacah['Target_FASIH'] - merge_pencacah['Target_SQLLab']
merge_pencacah = merge_pencacah.sort_values(by='Selisih', ascending=False)

# Merge Pengawas
merge_pengawas = pd.merge(fasih_pengawas, sql_pengawas, on='Email', how='outer').fillna(0)
merge_pengawas['Selisih'] = merge_pengawas['Target_FASIH'] - merge_pengawas['Target_SQLLab']
merge_pengawas = merge_pengawas.sort_values(by='Selisih', ascending=False)

output_file = '/Users/jihanmaisaroh/scrap_fasih/Perbandingan_Per_Petugas_7201.xlsx'
with pd.ExcelWriter(output_file) as writer:
    merge_pencacah.to_excel(writer, sheet_name='Pencacah', index=False)
    merge_pengawas.to_excel(writer, sheet_name='Pengawas', index=False)

print(f"File perbandingan berhasil dibuat: {output_file}")
print(f"Total Pencacah dengan selisih: {len(merge_pencacah[merge_pencacah['Selisih'] != 0])}")
print(f"Total Pengawas dengan selisih: {len(merge_pengawas[merge_pengawas['Selisih'] != 0])}")
print("\nTop 5 Selisih Pencacah:")
print(merge_pencacah.head(5).to_string(index=False))
print("\nTop 5 Selisih Pengawas:")
print(merge_pengawas.head(5).to_string(index=False))
