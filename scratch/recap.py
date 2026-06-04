import pandas as pd
import os

csv_path = "/Users/jihanmaisaroh/scrap_fasih/all_email_history.csv"
if not os.path.exists(csv_path):
    print("CSV file not found!")
    exit()

df = pd.read_csv(csv_path)

# Drop duplicates by company code to get unique companies
df_unique = df[df["Kode Identitas"] != "-"].drop_duplicates(subset=["Kode Identitas"])

# Mapping code prefix
kabkot_mapping = {
    "7201": "Banggai",
    "7202": "Poso",
    "7203": "Donggala",
    "7204": "Toli-Toli",
    "7205": "Buol",
    "7206": "Morowali",
    "7207": "Banggai Kepulauan",
    "7208": "Parigi Moutong",
    "7209": "Tojo Una-Una",
    "7210": "Sigi",
    "7211": "Banggai Laut",
    "7212": "Morowali Utara",
    "7271": "Palu"
}

def get_kabkot(code):
    if not isinstance(code, str) or len(code) < 4:
        return "Unknown"
    return kabkot_mapping.get(code[:4], f"Unknown ({code[:4]})")

df_unique["KabKot"] = df_unique["Kode Identitas"].apply(get_kabkot)

# Group by KabKot and Status
pivot_df = pd.crosstab(df_unique["KabKot"], df_unique["Status Dokumen"], margins=True)
print("=== DISTRIBUSI STATUS DOKUMEN PER KABUPATEN/KOTA ===")
print(pivot_df.to_string())
