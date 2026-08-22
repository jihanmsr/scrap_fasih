import os
import pandas as pd
import glob
import json

target_dir = "/Users/jihanmaisaroh/scrap_fasih/Usaha Hilang"
csv_files = glob.glob(os.path.join(target_dir, "*.csv"))

data = []

for file_path in csv_files:
    print(f"Reading: {os.path.basename(file_path)}")
    try:
        df = pd.read_csv(file_path)
        for _, row in df.iterrows():
            raw_nik = str(row['nik']).split('.')[0] if pd.notna(row['nik']) else ""
            if len(raw_nik) > 8:
                masked_nik = raw_nik[:4] + "*" * (len(raw_nik) - 8) + raw_nik[-4:]
            else:
                masked_nik = raw_nik
                
            item = {
                "kab": str(row['kab']) if pd.notna(row['kab']) else "",
                "kec": str(row['kec']) if pd.notna(row['kec']) else "",
                "desa": str(row['desa']) if pd.notna(row['desa']) else "",
                "subsls": str(row['subsls']).split('.')[0] if pd.notna(row['subsls']) else "",
                "nama_usaha": str(row['nama_usaha']) if pd.notna(row['nama_usaha']) else "",
                "nama_pemilik": str(row['nama_pemilik']) if pd.notna(row['nama_pemilik']) else "",
                "nik": masked_nik,
                "lokasi_pemilik": str(row['lokasi_pemilik']) if pd.notna(row['lokasi_pemilik']) else "",
                "link_keluarga": str(row['link_keluarga_pemilik']) if 'link_keluarga_pemilik' in row and pd.notna(row['link_keluarga_pemilik']) else "",
                "link_usaha": str(row['link_usaha']) if 'link_usaha' in row and pd.notna(row['link_usaha']) else ""
            }
            data.append(item)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")

js_content = f"window.dataHilangUsaha = {json.dumps(data)};\n"

with open("/Users/jihanmaisaroh/scrap_fasih/data_hilang_usaha.js", "w") as f:
    f.write(js_content)

print(f"Selesai! {len(data)} data usaha hilang berhasil diekstrak ke data_hilang_usaha.js")
