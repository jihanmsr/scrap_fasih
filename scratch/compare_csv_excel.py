import pandas as pd

excel_path = "/Users/jihanmaisaroh/scrap_fasih/Progres Sulteng Fasih SM SE2026.xlsx"
csv1_path = "/Users/jihanmaisaroh/scrap_fasih/progress-assignment-fd68e454-ba45-4b85-8205-f3bf777ded24.csv"
csv2_path = "/Users/jihanmaisaroh/scrap_fasih/progress-assignment-fd68e454-ba45-4b85-8205-f3bf777ded24 (2).csv"
csv3_path = "/Users/jihanmaisaroh/scrap_fasih/progress-assignment-fd68e454-ba45-4b85-8205-f3bf777ded24 (3).csv"

print("--- EXCEL 6 JULI ---")
df_6 = pd.read_excel(excel_path, sheet_name="6 Juli")
print(df_6[['Wilayah', 'OPEN', 'APPROVED BY Pengawas', 'SUBMITTED BY Pencacah', 'DRAFT', 'Total', 'Persentase']])

print("\n--- EXCEL 7 JULI ---")
df_7 = pd.read_excel(excel_path, sheet_name="7 Juli")
print(df_7[['Wilayah', 'OPEN', 'APPROVED BY Pengawas', 'SUBMITTED BY Pencacah', 'DRAFT', 'Total', 'Persentase']])

print("\n--- CSV 1 (progress-assignment...) ---")
try:
    df_c1 = pd.read_csv(csv1_path)
    print(df_c1)
except Exception as e:
    print(e)

print("\n--- CSV 2 (progress-assignment... (2)) ---")
try:
    df_c2 = pd.read_csv(csv2_path, sep=";")
    print(df_c2[['Wilayah', 'OPEN', 'SUBMITTED BY Pencacah', 'APPROVED BY Pengawas', 'DRAFT', 'Column1', 'Column2', 'Column3']])
except Exception as e:
    print(e)

print("\n--- CSV 3 (progress-assignment... (3)) ---")
try:
    df_c3 = pd.read_csv(csv3_path)
    print(df_c3[['Wilayah', 'OPEN', 'SUBMITTED BY Pencacah', 'APPROVED BY Pengawas', 'DRAFT']])
except Exception as e:
    print(e)
