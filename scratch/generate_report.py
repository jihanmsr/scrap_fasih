import pandas as pd
import os

csv_path = "/Users/jihanmaisaroh/scrap_fasih/all_email_history.csv"
if not os.path.exists(csv_path):
    print("CSV file not found!")
    exit()

df = pd.read_csv(csv_path)
df_unique = df[df["Kode Identitas"] != "-"].drop_duplicates(subset=["Kode Identitas"])

# CORRECT BPS Codes for Central Sulawesi (Province 72)
kabkot_mapping = {
    "7201": "Banggai Kepulauan",
    "7202": "Banggai",
    "7203": "Morowali",
    "7204": "Poso",
    "7205": "Donggala",
    "7206": "Toli-Toli",
    "7207": "Buol",
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

# Generate Crosstab/Pivot Table
pivot_df = pd.crosstab(df_unique["KabKot"], df_unique["Status Dokumen"], margins=True)

report_content = "=== REKAP STATUS DOKUMEN PER KABUPATEN/KOTA (KODE BENAR) ===\n\n"
report_content += pivot_df.to_string()
report_content += "\n\n"
report_content += f"Total Unique Companies: {len(df_unique)}\n"
report_content += f"Total Rows in CSV (including history): {len(df)}\n"

output_txt = "/Users/jihanmaisaroh/scrap_fasih/rekap_kabkot.txt"
with open(output_txt, "w") as f:
    f.write(report_content)

print(report_content)
print(f"Laporan disimpan di: {output_txt}")
