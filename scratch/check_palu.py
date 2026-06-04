import pandas as pd

df = pd.read_csv("/Users/jihanmaisaroh/scrap_fasih/all_email_history.csv")
df_unique = df[df["Kode Identitas"] != "-"].drop_duplicates(subset=["Kode Identitas"])

palu_missing = df_unique[(df_unique["Kode Identitas"].str.startswith("7271")) & (df_unique["Status Dokumen"] == "-")]
print(f"Total Palu companies with '-' status: {len(palu_missing)}")
print("Sample:")
print(palu_missing[["Kode Identitas", "Nama Perusahaan"]].head(15))
