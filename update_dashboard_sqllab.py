import pandas as pd
import json
import sys
import os
import datetime
import sqlite3

def get_real_tambahan():
    kab_counts = {}
    kec_counts = {}
    db_path = '/Users/jihanmaisaroh/scrap_fasih/granular_data.db'
    if not os.path.exists(db_path): 
        print(" [WARNING] granular_data.db tidak ditemukan. Data tambahan 0.")
        return kab_counts, kec_counts
    try:
        import re
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT kabupaten, kecamatan, is_usaha FROM granular_records WHERE is_tambahan=1")
        rows = c.fetchall()
        for row in rows:
            kab_raw = row[0]
            kec_raw = row[1].upper().strip()
            is_usaha = row[2]
            
            kab_clean = re.sub(r'\[\d+\]', '', kab_raw).replace('[','').replace(']','').strip()
            kab_clean = " ".join([w for w in kab_clean.split() if not (w.isdigit() or w.startswith("72"))]).upper().strip()
            
            if kab_clean not in kab_counts:
                kab_counts[kab_clean] = {"usaha": 0, "rumah": 0}
            if is_usaha: kab_counts[kab_clean]["usaha"] += 1
            else: kab_counts[kab_clean]["rumah"] += 1
            
            kec_key = f"{kab_clean}_{kec_raw}"
            if kec_key not in kec_counts:
                kec_counts[kec_key] = {"usaha": 0, "rumah": 0}
            if is_usaha: kec_counts[kec_key]["usaha"] += 1
            else: kec_counts[kec_key]["rumah"] += 1
        conn.close()
    except Exception as e:
        print(f"DB Error: {e}")
    return kab_counts, kec_counts

def load_daily_summary():
    data = {}
    db_p = '/Users/jihanmaisaroh/scrap_fasih/granular_data.db'
    if os.path.exists(db_p):
        try:
            cn = sqlite3.connect(db_p)
            cr = cn.cursor()
            cr.execute("SELECT tanggal, kabupaten, total_aktivitas, total_submitted, total_approved, total_rejected, total_usaha_tambahan FROM daily_summary ORDER BY tanggal ASC, kabupaten ASC")
            rows = cr.fetchall()
            for row in rows:
                tgl = row[0]
                kab = row[1]
                if tgl not in data: data[tgl] = {}
                data[tgl][kab] = {
                    "total_aktivitas": row[2] or 0,
                    "total_submitted": row[3] or 0,
                    "total_approved": row[4] or 0,
                    "total_rejected": row[5] or 0,
                    "total_usaha_tambahan": row[6] or 0
                }
            cn.close()
        except Exception as e:
            print(f"Error loading daily summary DB: {e}")
    return data

def main():
    if len(sys.argv) < 2:
        print("Penggunaan: python update_dashboard_sqllab.py <file_excel_dari_sqllab.xlsx>")
        sys.exit(1)
    
    excel_file = sys.argv[1]
    print(f"Membaca data dari {excel_file}...")
    df = pd.read_excel(excel_file)
    
    # Get tambahan data from DB
    kab_tambahan, kec_tambahan = get_real_tambahan()
    
    # Process dataframe
    # Expected cols: kode_kab, nama_kab, kode_kec, nama_kec, total_prelist, total_open, total_draft, total_submitted, total_approved, total_rejected, total_submitted_pencacah, total_submitted_respondent
    
    kab_dict = {}
    
    for _, row in df.iterrows():
        kode_kab = str(row['kode_kab'])[-2:]
        nama_kab = str(row['nama_kab']).upper()
        kab_key = f"[{kode_kab}] {nama_kab}"
        
        kode_kec = str(row['kode_kec'])[-3:]
        nama_kec = str(row['nama_kec']).upper()
        kec_key = f"[{kode_kec}] {nama_kec}"
        
        prelist = int(row['total_prelist'])
        opn = int(row['total_open'])
        draft = int(row['total_draft'])
        submitted = int(row['total_submitted'])
        approved = int(row['total_approved'])
        rejected = int(row['total_rejected'])
        sub_pen = int(row['total_submitted_pencacah'])
        sub_res = int(row['total_submitted_respondent'])
        
        # Determine Tambahan for Kec
        kec_tambahan_key = f"{nama_kab}_{nama_kec}"
        n_usaha = 0
        n_rumah = 0
        if kec_tambahan_key in kec_tambahan:
            n_usaha = kec_tambahan[kec_tambahan_key]["usaha"]
            n_rumah = kec_tambahan[kec_tambahan_key]["rumah"]
            
        if kab_key not in kab_dict:
            kab_dict[kab_key] = {
                "kabupaten": kab_key,
                "total_prelist": 0,
                "total_draft": 0,
                "total_open": 0,
                "total_submitted": 0,
                "total_rejected": 0,
                "total_approved": 0,
                "total_submitted_pencacah": 0,
                "total_submitted_respondent": 0,
                "persentase": 0,
                "new_usaha_overall": 0,
                "new_rumah_overall": 0,
                "kecamatan_list": []
            }
            if nama_kab in kab_tambahan:
                kab_dict[kab_key]["new_usaha_overall"] = kab_tambahan[nama_kab]["usaha"]
                kab_dict[kab_key]["new_rumah_overall"] = kab_tambahan[nama_kab]["rumah"]
                
        kab_dict[kab_key]["total_prelist"] += prelist
        kab_dict[kab_key]["total_open"] += opn
        kab_dict[kab_key]["total_draft"] += draft
        kab_dict[kab_key]["total_submitted"] += submitted
        kab_dict[kab_key]["total_approved"] += approved
        kab_dict[kab_key]["total_rejected"] += rejected
        kab_dict[kab_key]["total_submitted_pencacah"] += sub_pen
        kab_dict[kab_key]["total_submitted_respondent"] += sub_res
        
        perc_kec = (submitted / prelist * 100) if prelist > 0 else 0
        
        kab_dict[kab_key]["kecamatan_list"].append({
            "kecamatan": kec_key,
            "kec_name": kec_key,
            "total_prelist": prelist,
            "total_draft": draft,
            "total_open": opn,
            "total_submitted": submitted,
            "total_rejected": rejected,
            "total_approved": approved,
            "total_submitted_pencacah": sub_pen,
            "total_submitted_respondent": sub_res,
            "persentase": round(perc_kec, 2),
            "new_usaha": n_usaha,
            "new_rumah": n_rumah
        })

    se_umum_arr = []
    for kab, data in kab_dict.items():
        if data["total_prelist"] > 0:
            data["persentase"] = round(data["total_submitted"] / data["total_prelist"] * 100, 2)
        se_umum_arr.append(data)
        
    final_js_obj = {
        "updated_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00") + " (Sync SQL Lab)",
        "se_umum": se_umum_arr
    }
    
    with open("ipas_data.js", "w", encoding="utf-8") as f:
        f.write(f"window.IPAS_DATA = {json.dumps(final_js_obj, ensure_ascii=False, indent=2)};\n")
    print(" ✅ File lokal ipas_data.js berhasil diperbarui.")
    
    daily_data = load_daily_summary()
    with open("daily_summary.js", "w", encoding="utf-8") as fw:
        fw.write(f"window.DAILY_SUMMARY = {json.dumps(daily_data, indent=2)};\n")
    print(" ✅ File lokal daily_summary.js berhasil diperbarui.")

if __name__ == '__main__':
    main()
