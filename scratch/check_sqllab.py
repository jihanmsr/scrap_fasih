import pandas as pd

# Load sqllab csv
sqllab = pd.read_csv('/Users/jihanmaisaroh/scrap_fasih/sqllab_5_monitoring_jumlah_usaha_berdasarkan_status_keberadaannya_perpetugas_20260729T070546.csv')

# Calculate sums
sqllab['sum_status'] = sqllab['ditemukan'] + sqllab['baru'] + sqllab['tutup'] + sqllab['ganda'] + sqllab['tidak_ditemukan'] + sqllab['belum_terisi']
sqllab['diff_sum'] = sqllab['total_usaha'] - sqllab['sum_status']

print("Berapa banyak row dimana total_usaha != sum(semua status)?", len(sqllab[sqllab['diff_sum'] != 0]))

diff_df = sqllab[sqllab['diff_sum'] != 0]
if not diff_df.empty:
    print("Contoh yang tidak sama:")
    print(diff_df[['email', 'total_usaha', 'sum_status', 'diff_sum']].head(10).to_string())

