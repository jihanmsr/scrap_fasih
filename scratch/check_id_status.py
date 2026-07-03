import pandas as pd

excel_path = "/Users/jihanmaisaroh/scrap_fasih/Data_Mikro_Anomali_keluarga_5321_20260701_111359.xlsx"
df = pd.read_excel(excel_path, header=3)

target_ids = [
    "1031ce1b-21e8-46c9-89c3-297a99896c4b", # Progress 1 (failed)
    "3208777a-d127-4787-b9ca-edbdaf5dddc1", # Progress 2 (failed)
    "57f5ffbe-a76a-4c50-9785-4da0a813ed31", # Progress 3 (failed)
    "e1682c11-9c77-4f92-8550-38d0dccad36f", # Progress 12 (succeeded!)
    "007a6993-1fbe-47b6-8df8-9ac53e184017", # Progress 13 (failed)
]

for tid in target_ids:
    row = df[df["Assignment ID"] == tid]
    if not row.empty:
        print(f"\nTarget ID: {tid}")
        print(f"  Nama KRT: {row.iloc[0]['Nama KRT']}")
        print(f"  Kecamatan: {row.iloc[0]['Nama Kecamatan']}")
        print(f"  Desa: {row.iloc[0]['Nama Desa/Kel']}")
        print(f"  Tindak Lanjut: {row.iloc[0]['Tindak Lanjut']}")
        print(f"  ID Petugas: {row.iloc[0]['ID Petugas']}")
    else:
        print(f"\nTarget ID: {tid} NOT FOUND in Excel")
