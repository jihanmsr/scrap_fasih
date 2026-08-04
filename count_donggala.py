import pandas as pd
import glob
import os

excel_files = glob.glob('/Users/jihanmaisaroh/scrap_fasih/Rekap Progress Petugas*.xlsx')
latest_excel = max(excel_files, key=os.path.getctime)
df = pd.read_excel(latest_excel)
df_donggala = df[df['level_5_full_code'].astype(str).str.startswith('7205')]
df_donggala_p = df_donggala[df_donggala['pencacah_email'].notna() & (df_donggala['pencacah_email'] != '')]
pencacah_emails = df_donggala_p['pencacah_email'].unique()
print(f"Total Pencacah di Donggala: {len(pencacah_emails)}")
