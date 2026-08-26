import os
import pandas as pd
import re
import glob

base_dir = '/Users/jihanmaisaroh/scrap_fasih'
new_data_dir = os.path.join(base_dir, 'New 25 Agustus')
master_file = os.path.join(base_dir, 'fast_petugas_all.csv')

print("Loading master data...")
# Read as string to avoid precision issues
master_df = pd.read_csv(master_file, dtype={'Region Code': str})

# Map Region Code to Pencacah and Pengawas
pencacah_map = master_df[master_df['Role'] == 'Pencacah'].set_index('Region Code')['Email'].to_dict()
pengawas_map = master_df[master_df['Role'] == 'Pengawas'].set_index('Region Code')['Email'].to_dict()

def extract_code(text):
    if pd.isna(text):
        return ""
    match = re.search(r'\[(\d+)\]', str(text))
    return match.group(1) if match else ""

# Keywords to detect if they moved or mentioned another SLS/RT
pindah_pattern = re.compile(r'(?i)\b(pindah|rt\s*\d+|rw\s*\d+|sls|desa|kecamatan|kabupaten|luar)\b')

csv_files = glob.glob(os.path.join(new_data_dir, '*.csv'))

output_dir = os.path.join(new_data_dir, 'Processed')
os.makedirs(output_dir, exist_ok=True)

print(f"Found {len(csv_files)} CSV files. Processing...")

processed_count = 0
for file in csv_files:
    try:
        df = pd.read_csv(file)
    except Exception as e:
        print(f"Error reading {file}: {e}")
        continue
    
    # Construct Region Code: 72 + kab + kec + desa + kode_sls
    region_codes = []
    for _, row in df.iterrows():
        kab = extract_code(row.get('kab', ''))
        kec = extract_code(row.get('kec', ''))
        desa = extract_code(row.get('desa', ''))
        sls = str(row.get('kode_sls', '')).zfill(6) if pd.notna(row.get('kode_sls')) else "000000"
        
        if kab and kec and desa:
            rc = f"72{kab}{kec}{desa}{sls}"
        else:
            rc = None
        region_codes.append(rc)
        
    df['Region_Code'] = region_codes
    
    # Map PPL and PML
    df['PPL (Master)'] = df['Region_Code'].map(pencacah_map)
    df['PML (Master)'] = df['Region_Code'].map(pengawas_map)
    
    # Highlight
    if 'Info_Penulusuran' in df.columns:
        df['Indikasi_Pindah_SLS'] = df['Info_Penulusuran'].apply(lambda x: "Ya" if pd.notna(x) and pindah_pattern.search(str(x)) else "Tidak")
    else:
        df['Indikasi_Pindah_SLS'] = "Tidak (Kolom Info Tidak Ada)"
        
    out_name = os.path.basename(file)
    df.to_csv(os.path.join(output_dir, out_name), index=False)
    processed_count += 1
    
print(f"Done! Processed {processed_count} files into {output_dir}")
