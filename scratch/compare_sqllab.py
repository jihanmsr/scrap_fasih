import pandas as pd

# Load sqllab csv
sqllab = pd.read_csv('/Users/jihanmaisaroh/scrap_fasih/sqllab_5_monitoring_jumlah_usaha_berdasarkan_status_keberadaannya_perpetugas_20260729T070546.csv')

# Load fast_petugas_all
fast = pd.read_csv('/Users/jihanmaisaroh/scrap_fasih/fast_petugas_all_2026-07-28.csv')

# Group fast by email and sum Total Target and progress
fast['Email'] = fast['Email'].astype(str).str.lower().str.strip()
sqllab['email'] = sqllab['email'].astype(str).str.lower().str.strip()

fast_grouped = fast.groupby('Email').agg({
    'Total Target': 'sum',
    'SUBMITTED BY Pencacah': 'sum',
    'APPROVED BY Pengawas': 'sum',
    'OPEN': 'sum',
    'DRAFT': 'sum'
}).reset_index()

merged = pd.merge(sqllab, fast_grouped, left_on='email', right_on='Email', how='left')

# Calculate differences
merged['diff_total'] = merged['total_usaha'] - merged['Total Target']

# Filter only Banggai Kepulauan
print(f"Total baris sqllab: {len(sqllab)}")
print(f"Total baris yang bisa dimapping dengan email: {merged['Email'].notna().sum()}")
print(f"Beda total_usaha != Total Target: {len(merged[merged['diff_total'] != 0])}")

diff_df = merged[merged['diff_total'] != 0][['email', 'total_usaha', 'Total Target', 'diff_total', 'ditemukan', 'baru']]
if not diff_df.empty:
    print("\nSample perbedaan total usaha:")
    print(diff_df.head(10).to_string())

# Also maybe sqllab 'baru' refers to 'New Usaha' from somewhere else?
# Does the difference relate to anything specific?
merged['sum_semua'] = merged['ditemukan'] + merged['baru'] + merged['tutup'] + merged['ganda'] + merged['tidak_ditemukan'] + merged['belum_terisi']
print("\nApakah total_usaha = sum kolom status?", (merged['sum_semua'] == merged['total_usaha']).all())

# Check total sum for kab 7201
print("\nTotal usaha di SQL Lab untuk Banggai Kep:", merged['total_usaha'].sum())
print("Total Target di tarikan kita (dari yang matched aja):", merged['Total Target'].sum())
