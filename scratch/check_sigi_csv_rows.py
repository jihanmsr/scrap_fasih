import pandas as pd
import os

csv_path = "/Users/jihanmaisaroh/scrap_fasih/csv_reports/se_umum_7210.csv"
if not os.path.exists(csv_path):
    print("CSV file not found!")
    exit(1)

df = pd.read_csv(csv_path, usecols=["code_id", "petugas_username", "status"])
print("Total rows in Sigi CSV:", len(df))

# Count unassigned
unassigned = df[df["petugas_username"].isna() | (df["petugas_username"] == "-")]
print("Unassigned count in CSV:", len(unassigned))

# Value counts of Status
print("\nStatus counts in Sigi CSV:")
print(df["status"].value_counts(dropna=False))
