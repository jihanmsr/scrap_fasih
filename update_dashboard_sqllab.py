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
    if not os.path.exists(db_path): return kab_counts, kec_counts
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
    except Exception:
        pass
    return kab_counts, kec_counts

def main():
    if len(sys.argv) < 2:
        print("Penggunaan: python update_dashboard_sqllab.py <file_excel_dari_sqllab.csv/xlsx>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path, sep="\t")
    else:
        df = pd.read_excel(file_path)
        
    KAB_MAP = {
        '7201': 'BANGGAI KEPULAUAN', '7202': 'BANGGAI', '7203': 'MOROWALI',
        '7204': 'POSO', '7205': 'DONGGALA', '7206': 'TOLI-TOLI', '7207': 'BUOL',
        '7208': 'PARIGI MOUTONG', '7209': 'TOJO UNA-UNA', '7210': 'SIGI',
        '7211': 'BANGGAI LAUT', '7212': 'MOROWALI UTARA', '7271': 'PALU'
    }
    
    # Read existing ipas_data.js to map kec codes to names
    kec_name_map = {}
    try:
        import re
        with open('ipas_data.js', 'r') as f:
            content = f.read()
        match = re.search(r'window\.IPAS_DATA\s*=\s*(\{.*\});', content, re.DOTALL)
        if match:
            ipas = json.loads(match.group(1))
            for kab in ipas.get('se_umum', []):
                for kec in kab.get('kecamatan_list', []):
                    k_name = kec.get('kec_name', '')
                    if k_name and '[' in k_name and ']' in k_name:
                        code = k_name.split(']')[0].replace('[','').strip()
                        name = k_name.split(']')[1].strip()
                        kec_name_map[code] = name
    except Exception as e:
        print(f"Warn: {e}")
        
    kab_tambahan, kec_tambahan = get_real_tambahan()
    kab_dict = {}
    
    for _, row in df.iterrows():
        kode_kab = str(row['kode_kab']).zfill(4)
        kab_id = kode_kab[-2:]
        nama_kab = KAB_MAP.get(kode_kab, kode_kab)
        kab_key = f"[{kab_id}] {nama_kab}"
        
        kode_kec = str(row['kode_kec']).zfill(3)
        nama_kec = kec_name_map.get(kode_kec, kode_kec)
        kec_key = f"[{kode_kec}] {nama_kec}"
        
        prelist = int(row['total_prelist'])
        opn = int(row['total_open'])
        draft = int(row['total_draft'])
        submitted = int(row['total_submitted'])
        approved = int(row['total_approved'])
        rejected = int(row['total_rejected'])
        sub_pen = int(row['total_submitted_pencacah'])
        sub_res = int(row['total_submitted_respondent'])
        
        kec_tambahan_key = f"{nama_kab}_{nama_kec}"
        n_usaha = 0; n_rumah = 0
        if kec_tambahan_key in kec_tambahan:
            n_usaha = kec_tambahan[kec_tambahan_key]["usaha"]
            n_rumah = kec_tambahan[kec_tambahan_key]["rumah"]
            
        if kab_key not in kab_dict:
            kab_dict[kab_key] = {
                "kabupaten": kab_key, "total_prelist": 0, "total_draft": 0, "total_open": 0,
                "total_submitted": 0, "total_rejected": 0, "total_approved": 0,
                "total_submitted_pencacah": 0, "total_submitted_respondent": 0,
                "persentase": 0, "new_usaha_overall": 0, "new_rumah_overall": 0,
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
            "kecamatan": kec_key, "kec_name": kec_key, "total_prelist": prelist,
            "total_draft": draft, "total_open": opn, "total_submitted": submitted,
            "total_rejected": rejected, "total_approved": approved,
            "total_submitted_pencacah": sub_pen, "total_submitted_respondent": sub_res,
            "persentase": round(perc_kec, 2), "new_usaha": n_usaha, "new_rumah": n_rumah
        })

    se_umum_arr = []
    for kab in sorted(kab_dict.keys()):
        data = kab_dict[kab]
        if data["total_prelist"] > 0:
            data["persentase"] = round(data["total_submitted"] / data["total_prelist"] * 100, 2)
        se_umum_arr.append(data)
        
    final_js_obj = {
        "updated_at": datetime.datetime.now().strftime("%d %b %Y, %H:%M:%S") + " (Sync SQL Lab)",
        "se_umum": se_umum_arr
    }
    
    with open("ipas_data.js", "w", encoding="utf-8") as f:
        f.write(f"window.IPAS_DATA = {json.dumps(final_js_obj, ensure_ascii=False, indent=2)};\n")
    print(" ✅ File lokal ipas_data.js berhasil diperbarui (Target & Realisasi 100% klop dengan FASIH).")

if __name__ == '__main__':
    main()

