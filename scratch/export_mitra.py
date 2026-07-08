import pandas as pd
import json
import os

def main():
    script_dir = "/Users/jihanmaisaroh/scrap_fasih"
    excel_path = os.path.join(script_dir, "Rekap Mitra SE2026.xlsx")
    
    if not os.path.exists(excel_path):
        print(f"File {excel_path} tidak ditemukan!")
        return
        
    print(f"Membaca sheet 'Pakai' dari {excel_path}...")
    df = pd.read_excel(excel_path, sheet_name="Pakai")
    
    # Clean the data
    df = df.fillna("")
    
    mitra_list = []
    
    for idx, row in df.iterrows():
        nama = str(row.get('Nama Lengkap', '')).strip()
        posisi = str(row.get('Posisi', '')).strip()
        asal = str(row.get('Alamat Kab/Kota', '')).strip()
        email = str(row.get('Email', '')).strip().lower()
        
        if not email and not nama:
            continue
            
        mitra_list.append({
            "nama": nama,
            "posisi": posisi,
            "asal": asal,
            "email": email
        })
        
    js_path = os.path.join(script_dir, "mitra_data.js")
    with open(js_path, "w", encoding="utf-8") as f:
        f.write(f"window.MITRA_DATA = {json.dumps(mitra_list)};\n")
        
    print(f"Berhasil menyimpan {len(mitra_list)} data mitra ke {js_path}")

if __name__ == '__main__':
    main()
