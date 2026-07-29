import pandas as pd
import json
import os

print("Membaca file Excel...")
excel_path = '/Users/jihanmaisaroh/scrap_fasih/Analisis_Lintas_Sistem_Sulteng.xlsx'

if not os.path.exists(excel_path):
    print("File Excel belum ada. Pastikan jalankan compare_lintas_sistem.py dulu.")
    exit(1)

# Baca sheet SLS
df_sls = pd.read_excel(excel_path, sheet_name='Analisis_per_SLS')
# Baca sheet Petugas
df_petugas = pd.read_excel(excel_path, sheet_name='Analisis_per_Petugas')

# Export to JSON format suitable for Javascript arrays
df_sls.to_json('/Users/jihanmaisaroh/scrap_fasih/rekon_sls.json', orient='records', force_ascii=False)
df_petugas.to_json('/Users/jihanmaisaroh/scrap_fasih/rekon_petugas.json', orient='records', force_ascii=False)

print("Export ke JSON berhasil!")
