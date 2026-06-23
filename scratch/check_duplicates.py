import pandas as pd

csv_path = "/Users/jihanmaisaroh/scrap_fasih/csv_reports/se_umum_7210.csv"
df = pd.read_csv(csv_path, usecols=["target_id", "code_id", "status"])

print("Total rows:", len(df))
print("Unique target_id:", df["target_id"].nunique())
print("Unique code_id:", df["code_id"].nunique())

# Print value counts of duplicate target_ids
dups = df[df.duplicated(subset=["target_id"], keep=False)]
print("\nNumber of rows with duplicate target_id:", len(dups))
if len(dups) > 0:
    print("\nSample duplicate rows:")
    print(dups.sort_values("target_id").head(10))
