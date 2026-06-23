import pandas as pd
import glob
import os

script_dir = "/Users/jihanmaisaroh/scrap_fasih"
files = glob.glob(os.path.join(script_dir, "Detail_Usaha_SE_Umum_*.csv"))
if not files:
    print("No CSV files found matching pattern!")
    exit(1)

# Pick the latest one
latest_csv = max(files, key=os.path.getmtime)
print("Reading CSV:", latest_csv)

df = pd.read_csv(latest_csv, usecols=["Kabupaten"])
print("Total rows in CSV:", len(df))

sigi_rows = df[df["Kabupaten"].str.upper().str.contains("SIGI", na=False)]
print("Total Sigi rows in CSV:", len(sigi_rows))

print("\nRow counts by Kabupaten in CSV:")
print(df["Kabupaten"].value_counts())
