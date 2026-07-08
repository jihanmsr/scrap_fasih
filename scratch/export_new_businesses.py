import pandas as pd
import json
import os
import glob

def is_tambahan(code_identity):
    if pd.isna(code_identity) or not code_identity:
        return False
    cleaned = str(code_identity).strip()
    if not cleaned.startswith("72"):
        return True
    parts = [p.strip() for p in cleaned.split("-") if p.strip()]
    if len(parts) < 2:
        parts = [p.strip() for p in cleaned.split(" - ") if p.strip()]
    if len(parts) < 2:
        return False
    source = parts[1].upper()
    known_sources = {"DTSEN", "UMK", "UM", "UMB", "UMKM", "SE2026", "SE26", "PDRB", "PAPI", "CAWI", "CAPI", "UB"}
    if source not in known_sources:
        return True
    return False

def classify_tambahan_simple(code_id, name):
    code_id_upper = str(code_id or "").upper()
    name_upper = str(name or "").upper()
    if "BANGUNAN KOSONG" in name_upper or "RUMAH KOSONG" in name_upper or "KOSONG" in name_upper or "BANGUNAN KOSONG" in code_id_upper or "RUMAH KOSONG" in code_id_upper:
        return "Bangunan/Rumah Kosong", False
    if "1. YA" in code_id_upper or "1.YA" in code_id_upper or "1. YA" in name_upper or "1.YA" in name_upper:
        return "Keluarga Usaha", True
    if "2. TIDAK" in code_id_upper or "2.TIDAK" in code_id_upper or "2. TIDAK" in name_upper or "2.TIDAK" in name_upper:
        return "Keluarga (Bukan Usaha)", False
    if "KELUARGA" in name_upper:
        return "Keluarga", False
    return "Usaha Tambahan", True

def main():
    script_dir = "/Users/jihanmaisaroh/scrap_fasih"
    csv_files = glob.glob(os.path.join(script_dir, "Detail_Usaha_SE_Umum_*.csv"))
    if not csv_files:
        print("CSV Granular tidak ditemukan!")
        return
    csv_path = max(csv_files, key=os.path.getctime)
    print(f"Reading {csv_path}...")
    
    df = pd.read_csv(csv_path)
    
    tambahan_list = []
    
    for idx, row in df.iterrows():
        kode = row.get('Kode Target', '')
        nama = row.get('Nama Perusahaan / Usaha', '')
        
        if is_tambahan(kode):
            jenis_lbl, is_usaha = classify_tambahan_simple(kode, nama)
            kab = str(row.get('Kabupaten', '')).strip().upper()
            kec = str(row.get('Kecamatan', '')).strip().upper()
            
            tambahan_list.append({
                "kabupaten": kab,
                "kecamatan": kec,
                "name": str(nama),
                "code_identity": str(kode),
                "sls": str(row.get('Nama SLS', '')),
                "type": jenis_lbl,
                "is_usaha": is_usaha,
                "timestamp": str(row.get('Terakhir Diupdate', ''))
            })
            
    js_path = os.path.join(script_dir, "new_businesses_data.js")
    with open(js_path, "w", encoding="utf-8") as f:
        f.write(f"window.NEW_BUSINESSES_DATA = {json.dumps(tambahan_list)};\n")
        
    print(f"Saved {len(tambahan_list)} tambahan to {js_path}")

if __name__ == '__main__':
    main()
