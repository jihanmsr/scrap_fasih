import re

with open('compare_awal_realisasi.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Make it dynamic
content = content.replace("pd.read_excel('Rekap SBR, UTP, Keluarga_03_08.xlsx')", 
                          "pd.read_excel(max(glob.glob('Rekap SBR, UTP, Keluarga_*.xlsx')))")
content = content.replace("Membaca Rekap SBR, UTP, Keluarga_03_08.xlsx", 
                          "Membaca Rekap SBR, UTP, Keluarga_*.xlsx")

with open('compare_awal_realisasi.py', 'w', encoding='utf-8') as f:
    f.write(content)

