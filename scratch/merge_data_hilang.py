import os
import pandas as pd
import json
import glob

base_dir = '/Users/jihanmaisaroh/scrap_fasih'
processed_dir = os.path.join(base_dir, 'New 25 Agustus', 'Processed')
output_js = os.path.join(base_dir, 'data_hilang_keluarga.js')

print("Reading processed CSV files...")
csv_files = glob.glob(os.path.join(processed_dir, '*.csv'))
all_data = []

for f in csv_files:
    try:
        df = pd.read_csv(f)
        # Rename columns to avoid issues in JS if necessary, but we can keep as is
        df.rename(columns={
            'PPL (Master)': 'ppl_master',
            'PML (Master)': 'pml_master',
            'Indikasi_Pindah_SLS': 'indikasi_pindah_sls'
        }, inplace=True)
        # Convert NaN to None so it becomes null in JSON
        df = df.where(pd.notnull(df), None)
        
        # Override indikasi_pindah_sls based on Info_Penulusuran
        for idx, row in df.iterrows():
            if row.get('indikasi_pindah_sls') == 'Tidak' and row.get('Info_Penulusuran'):
                info = str(row['Info_Penulusuran']).lower()
                if info and info not in ['-', 'nan', "'-"]:
                    # If it contains any of these keywords, assume they moved
                    if any(kw in info for kw in ['warga dusun', 'pindah', 'dusun', 'rt', 'rw', 'beda sls', 'desa']):
                        df.at[idx, 'indikasi_pindah_sls'] = 'Ya'
        
        all_data.extend(df.to_dict(orient='records'))
    except Exception as e:
        print(f"Error reading {f}: {e}")

print(f"Total rows: {len(all_data)}")

# Write to JS file
print(f"Writing to {output_js}...")
with open(output_js, 'w', encoding='utf-8') as f:
    f.write('window.dataHilangKeluarga = ')
    json.dump(all_data, f, ensure_ascii=False)
    f.write(';\n')
    
print("Done!")
