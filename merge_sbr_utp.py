import pandas as pd
import glob
import os
from datetime import datetime

csv_files = glob.glob('/Users/jihanmaisaroh/scrap_fasih/sbr utp keluarga/*.csv')
dfs = [pd.read_csv(f) for f in csv_files]
df_combined = pd.concat(dfs, ignore_index=True)

# Remove duplicates just in case
df_combined = df_combined.drop_duplicates()

# Sort
df_combined = df_combined.sort_values(by=['level_2_full_code', 'level_5_full_code', 'level_6_code'])

# Format columns
df_combined['level_5_full_code'] = df_combined['level_5_full_code'].astype(str)
df_combined['level_6_code'] = df_combined['level_6_code'].astype(str).str.zfill(2)

print(f"Total baris setelah digabung: {len(df_combined)}")

today_str = datetime.now().strftime("%d_%m")
out_file = f"/Users/jihanmaisaroh/scrap_fasih/Rekap SBR, UTP, Keluarga_{today_str}.xlsx"

df_combined.to_excel(out_file, index=False)
print(f"Berhasil menyimpan ke: {out_file}")

