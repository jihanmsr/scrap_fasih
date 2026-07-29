import pandas as pd

# Load sqllab 5 (Usaha)
sqllab5 = pd.read_csv('/Users/jihanmaisaroh/scrap_fasih/sqllab_5_monitoring_jumlah_usaha_berdasarkan_status_keberadaannya_perpetugas_20260729T070546.csv')
sqllab5['email'] = sqllab5['email'].astype(str).str.lower().str.strip()
sqllab5_grouped = sqllab5.groupby('email').agg({'total_usaha': 'sum'}).reset_index()

# Load sqllab 6 (Keluarga)
sqllab6 = pd.read_csv('/Users/jihanmaisaroh/scrap_fasih/sqllab_6_monitoring_jumlah_keluarga_berdasarkan_status_keberadaannya_perpetugas_7201_20260729T072437.csv')
sqllab6['email'] = sqllab6['email'].astype(str).str.lower().str.strip()
sqllab6_grouped = sqllab6.groupby('email').agg({'total_keluarga': 'sum'}).reset_index()

# Merge sqllab5 & 6
sqllab_combined = pd.merge(sqllab5_grouped, sqllab6_grouped, on='email', how='outer').fillna(0)
sqllab_combined['total_gabungan'] = sqllab_combined['total_usaha'] + sqllab_combined['total_keluarga']

# Load fast_petugas_all_2026-07-28.csv (Restored)
fast = pd.read_csv('/Users/jihanmaisaroh/scrap_fasih/fast_petugas_all_2026-07-28.csv')
fast['Email'] = fast['Email'].astype(str).str.lower().str.strip()

# Group fast by email and sum Total Target
fast_grouped = fast.groupby('Email').agg({'Total Target': 'sum'}).reset_index()

# Merge with sqllab combined
merged = pd.merge(sqllab_combined, fast_grouped, left_on='email', right_on='Email', how='left')

# Calculate diff
merged['diff'] = merged['total_gabungan'] - merged['Total Target']

print("=== HASIL PERBANDINGAN ===")
print(f"Total petugas unik di SQL Lab (Usaha/Keluarga): {len(sqllab_combined)}")
print(f"Total petugas yang bisa dimapping dengan data tarikan: {merged['Email'].notna().sum()}")

# filter only matched
matched = merged[merged['Email'].notna()]
print(f"\nTotal Usaha (SQL Lab) untuk petugas matched: {matched['total_usaha'].sum()}")
print(f"Total Keluarga (SQL Lab) untuk petugas matched: {matched['total_keluarga'].sum()}")
print(f"Total Gabungan (Usaha + Keluarga) SQL Lab: {matched['total_gabungan'].sum()}")
print(f"Total Target di tarikan kita: {matched['Total Target'].sum()}")

diff_df = matched[abs(matched['diff']) > 0]
print(f"\nBerapa banyak petugas matched yang (Usaha + Keluarga) != Total Target kita? {len(diff_df)}")

if not diff_df.empty:
    print("\nSample perbedaan:")
    print(diff_df[['email', 'total_usaha', 'total_keluarga', 'total_gabungan', 'Total Target', 'diff']].head(15).to_string())

