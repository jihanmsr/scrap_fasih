import pandas as pd

# Load sqllab csv
sqllab = pd.read_csv('/Users/jihanmaisaroh/scrap_fasih/sqllab_5_monitoring_jumlah_usaha_berdasarkan_status_keberadaannya_perpetugas_20260729T070546.csv')

# Load fast_petugas_all from the 27th which is complete
fast = pd.read_csv('/Users/jihanmaisaroh/scrap_fasih/fast_petugas_all_2026-07-27.csv')

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
print(f"Menggunakan data tanggal 27 Juli (karena 28 Juli tidak lengkap)")
print(f"Total baris sqllab: {len(sqllab)}")
print(f"Total baris yang bisa dimapping dengan email: {merged['Email'].notna().sum()}")

# Check total sum for kab 7201
print("\nTotal usaha di SQL Lab untuk Banggai Kep:", merged['total_usaha'].sum())
print("Total Target di tarikan kita (Tgl 27):", merged['Total Target'].sum())
