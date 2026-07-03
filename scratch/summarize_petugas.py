import pandas as pd

excel_path = "/Users/jihanmaisaroh/scrap_fasih/Data_Mikro_Anomali_keluarga_5321_20260701_111359.xlsx"
df = pd.read_excel(excel_path, header=3)

# Print unique Kecamatan and Desa with their ID Petugas and Email Petugas count
summary = df.groupby(["Nama Kecamatan", "Nama Desa/Kel"]).agg(
    total_targets=("Assignment ID", "count"),
    unique_petugas=("Email Petugas", "nunique"),
    sample_petugas_email=("Email Petugas", lambda x: list(x.dropna().unique())[:2])
).reset_index()

print("Summary of Kecamatan and Desa in Excel:")
print(summary.to_string())
