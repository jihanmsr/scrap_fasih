import pandas as pd
import sys

# Load SQLLab
try:
    df_sql = pd.read_excel('/Users/jihanmaisaroh/scrap_fasih/sqllab_untitled_query_7_20260729T115458.xlsx')
except Exception as e:
    print(f"Error loading SQLLab: {e}")
    sys.exit(1)

# Status columns in SQLLab
sql_cols = ['open', 'draft', 'submitted_respondent', 'submitted_by_pencacah', 'edited_by_pengawas', 'rejected_by_pengawas', 'approved_by_pengawas', 'revoked_by_pengawas', 'edited_by_admin_kabupaten', 'rejected_by_admin_kabupaten', 'revoked_by_admin_kabupaten', 'completed_by_admin_kabupaten']
# Filter SQLLab to only include 7201
df_sql = df_sql[df_sql['level_6_full_code'].astype(str).str.startswith('7201')]
df_sql['total_target'] = df_sql[sql_cols].sum(axis=1)

sql_sum = {
    'total_target': df_sql['total_target'].sum(),
    'open': df_sql['open'].sum(),
    'draft': df_sql['draft'].sum(),
    'submitted_by_pencacah': df_sql['submitted_by_pencacah'].sum(),
    'submitted_respondent': df_sql['submitted_respondent'].sum(),
    'approved_by_pengawas': df_sql['approved_by_pengawas'].sum(),
    'rejected_by_pengawas': df_sql['rejected_by_pengawas'].sum() + df_sql['rejected_by_admin_kabupaten'].sum(),
    'edited_by_pengawas': df_sql['edited_by_pengawas'].sum()
}

# Load our CSV
try:
    df_csv = pd.read_csv('/Users/jihanmaisaroh/scrap_fasih/fast_petugas_all_2026-07-29.csv')
except Exception as e:
    print(f"Error loading CSV: {e}")
    sys.exit(1)

# Filter CSV for 7201
df_csv = df_csv[df_csv['Region Code'].astype(str).str.startswith('7201')]
df_csv_pencacah = df_csv[df_csv['Role'].str.upper() == 'PENCACAH']

csv_sum = {
    'total_target': df_csv_pencacah['Total Target'].sum(),
    'open': df_csv_pencacah['OPEN'].sum(),
    'draft': df_csv_pencacah['DRAFT'].sum(),
    'submitted_by_pencacah': df_csv_pencacah['SUBMITTED BY Pencacah'].sum(),
    'submitted_respondent': df_csv_pencacah['SUBMITTED RESPONDENT'].sum(),
    'approved_by_pengawas': df_csv_pencacah['APPROVED BY Pengawas'].sum(),
    'rejected_by_pengawas': df_csv_pencacah['REJECTED BY Pengawas'].sum() + df_csv_pencacah['REJECTED BY Admin Kabupaten'].sum(),
    'edited_by_pengawas': df_csv_pencacah['EDITED BY Pengawas'].sum()
}

print("="*40)
print("PERBANDINGAN TOTAL (SULAWESI TENGAH)")
print("="*40)
print(f"{'Metric':<25} | {'SQLLab':<10} | {'FASIH (Scraper)':<15} | {'Selisih'}")
print("-" * 65)

for k in sql_sum.keys():
    sql_val = sql_sum[k]
    csv_val = csv_sum[k]
    diff = sql_val - csv_val
    print(f"{k:<25} | {sql_val:<10.0f} | {csv_val:<15.0f} | {diff:+.0f}")

# Optional: Find which emails have diffs
# Aggregate by email in SQLLab
df_sql_agg = df_sql.groupby('pencacah_email')['total_target'].sum().reset_index()
df_sql_agg.rename(columns={'pencacah_email': 'Email', 'total_target': 'total_sql'}, inplace=True)
df_sql_agg['Email'] = df_sql_agg['Email'].str.strip().str.lower()

# Aggregate by email in CSV
df_csv_agg = df_csv_pencacah.groupby('Email')['Total Target'].sum().reset_index()
df_csv_agg.rename(columns={'Total Target': 'total_csv'}, inplace=True)
df_csv_agg['Email'] = df_csv_agg['Email'].str.strip().str.lower()

merged = pd.merge(df_sql_agg, df_csv_agg, on='Email', how='outer').fillna(0)
merged['diff'] = merged['total_sql'] - merged['total_csv']

diffs = merged[merged['diff'] != 0]

print("\n" + "="*40)
print(f"PETUGAS DENGAN SELISIH TARGET: {len(diffs)}")
print("="*40)
if len(diffs) > 0:
    print(diffs.sort_values(by='diff', ascending=False).head(20).to_string(index=False))
else:
    print("Semua data per petugas SAMA PERSIS! 🎉")
