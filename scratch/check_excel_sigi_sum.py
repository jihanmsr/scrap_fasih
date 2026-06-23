import pandas as pd
import glob
import os

script_dir = "/Users/jihanmaisaroh/scrap_fasih"
files = glob.glob(os.path.join(script_dir, "Laporan_Progres_Petugas_*.xlsx"))
if not files:
    print("No Excel reports found!")
    exit(1)

latest_excel = max(files, key=os.path.getmtime)
print("Reading Excel:", latest_excel)

xl = pd.ExcelFile(latest_excel)
print("Sheets in Excel:", xl.sheet_names)

# Read general officers summary
df = xl.parse("Ringkasan Petugas SE Umum")
print("Total rows in general summary sheet:", len(df))
print("Sum of Total_Target in general summary sheet:", df["Total_Target"].sum())

# Let's inspect some rows
print("\nSample rows:")
print(df.head(10))
