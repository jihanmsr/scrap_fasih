import pandas as pd

file_03 = 'Rekap Progress Petugas 03_08.xlsx'
file_04 = 'Rekap Progress Petugas 04_08.xlsx'

print(f"Loading {file_03}...")
df3 = pd.read_excel(file_03)
print(f"Loading {file_04}...")
df4 = pd.read_excel(file_04)

df3_p = df3[df3['pencacah_email'].notna() & (df3['pencacah_email'] != '')]
df4_p = df4[df4['pencacah_email'].notna() & (df4['pencacah_email'] != '')]

print("\n--- COMPARISON ---")
print(f"Total Rows (Raw): 03_08 = {len(df3)}, 04_08 = {len(df4)}")
print(f"Total Rows (Valid Email): 03_08 = {len(df3_p)}, 04_08 = {len(df4_p)}")

emails3 = set(df3_p['pencacah_email'].str.strip().str.lower())
emails4 = set(df4_p['pencacah_email'].str.strip().str.lower())

print(f"Unique Enumerators: 03_08 = {len(emails3)}, 04_08 = {len(emails4)}")

missing_in_4 = emails3 - emails4
new_in_4 = emails4 - emails3

print(f"Enumerators in 03_08 but missing in 04_08 ({len(missing_in_4)}):")
for e in list(missing_in_4)[:5]:
    print(f"  - {e}")
if len(missing_in_4) > 5: print("  ...")

print(f"New Enumerators in 04_08 ({len(new_in_4)}):")
for e in list(new_in_4)[:5]:
    print(f"  - {e}")
if len(new_in_4) > 5: print("  ...")
