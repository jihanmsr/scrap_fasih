import pandas as pd

# Load SQLLab
df_sql = pd.read_excel('/Users/jihanmaisaroh/scrap_fasih/sqllab_untitled_query_7_20260729T115458.xlsx')
df_sql = df_sql[df_sql['level_6_full_code'].astype(str).str.startswith('7201')]

# Load FASIH
df_csv = pd.read_csv('/Users/jihanmaisaroh/scrap_fasih/fast_petugas_all_2026-07-29.csv')
df_csv = df_csv[df_csv['Region Code'].astype(str).str.startswith('7201')]

# Get list of unique emails from FASIH
fasih_emails = df_csv[['Email', 'Role']].drop_duplicates()
fasih_emails['Email'] = fasih_emails['Email'].str.strip().str.lower()

# Get list of unique emails from SQLLab
sql_pencacah = set(df_sql['pencacah_email'].dropna().str.strip().str.lower())
sql_pengawas = set(df_sql['pengawas_email'].dropna().str.strip().str.lower())

# Identify missing emails in SQLLab
missing_in_sql = fasih_emails[~fasih_emails['Email'].isin(sql_pencacah)]

print("Total unique emails in FASIH (7201):", len(fasih_emails))
print("Total unique pencacah emails in SQLLab:", len(sql_pencacah))
print("Total unique pengawas emails in SQLLab:", len(sql_pengawas))

print("\nOrang-orang di FASIH yang TIDAK ADA di kolom pencacah_email SQLLab:")
role_counts = missing_in_sql['Role'].value_counts()
print(role_counts)

# Are they in the pengawas column instead?
missing_but_in_pengawas = missing_in_sql[missing_in_sql['Email'].isin(sql_pengawas)]
print(f"\nDari yang tidak ada di pencacah_email, berapa yang ternyata ada di pengawas_email? {len(missing_but_in_pengawas)}")

if len(missing_but_in_pengawas) > 0:
    print("Contoh yang ada di pengawas_email tapi tidak di pencacah_email:")
    print(missing_but_in_pengawas.head())

# What about the ones completely missing from SQLLab (neither pencacah nor pengawas)?
completely_missing = missing_in_sql[~missing_in_sql['Email'].isin(sql_pengawas)]
print(f"\nYang SAMA SEKALI tidak ada di SQLLab (7201): {len(completely_missing)}")
print(completely_missing['Role'].value_counts())
