import os
import pandas as pd
import glob

# Direktori target
target_dir = "/Users/jihanmaisaroh/scrap_fasih/Usaha Hilang"

# Cari semua file CSV di dalam folder tersebut
csv_files = glob.glob(os.path.join(target_dir, "*.csv"))

for file_path in csv_files:
    print(f"Memproses: {os.path.basename(file_path)}")
    try:
        # Baca CSV
        df = pd.read_csv(file_path)
        
        # Tambahkan kolom baru
        if 'link_usaha' in df.columns:
            df['html_link_usaha'] = df['link_usaha'].apply(
                lambda x: f'<a href="{x}" target="_blank">Buka Link Usaha</a>' if pd.notna(x) and str(x).strip() != '' else ''
            )
            
        if 'link_keluarga_pemilik' in df.columns:
            df['html_link_keluarga'] = df['link_keluarga_pemilik'].apply(
                lambda x: f'<a href="{x}" target="_blank">Buka Link Keluarga</a>' if pd.notna(x) and str(x).strip() != '' else ''
            )
        
        # Simpan kembali (overwrite)
        df.to_csv(file_path, index=False)
        print(f" -> Selesai diproses.")
        
    except Exception as e:
        print(f" -> Error memproses {os.path.basename(file_path)}: {e}")

print("\nSelesai! Semua file CSV di 'Usaha Hilang' telah ditambahkan 2 kolom baru.")
