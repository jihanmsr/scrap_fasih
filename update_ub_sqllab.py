import pandas as pd
import json
import sys
import os

def main():
    if len(sys.argv) < 2:
        print("Penggunaan: python update_ub_sqllab.py <file_csv>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    df = pd.read_csv(file_path, sep=",") if file_path.endswith(".csv") else pd.read_excel(file_path)
        
    KAB_MAP = {
        '7201': 'BANGGAI KEPULAUAN', '7202': 'BANGGAI', '7203': 'MOROWALI',
        '7204': 'POSO', '7205': 'DONGGALA', '7206': 'TOLI-TOLI', '7207': 'BUOL',
        '7208': 'PARIGI MOUTONG', '7209': 'TOJO UNA-UNA', '7210': 'SIGI',
        '7211': 'BANGGAI LAUT', '7212': 'MOROWALI UTARA', '7271': 'PALU'
    }
    
    import re
    with open('ipas_data.js', 'r', encoding="utf-8") as f:
        content = f.read()
    match = re.search(r'window\.IPAS_DATA\s*=\s*(\{.*\});', content, re.DOTALL)
    if not match:
        print("Could not parse ipas_data.js")
        sys.exit(1)
    ipas_data = json.loads(match.group(1))

    # Read existing ipas_data.js to map kec codes to names
    kec_name_map = {}
    for survey in ['se_umum', 'se_ub']:
        for kab in ipas_data.get(survey, []):
            for kec in kab.get('kecamatan_list', []):
                k_name = kec.get('kec_name', '')
                if k_name and '[' in k_name and ']' in k_name:
                    code = k_name.split(']')[0].replace('[','').strip()
                    name = k_name.split(']')[1].strip()
                    kec_name_map[code] = name
                    
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
        
        if kab_key not in kab_dict:
            kab_dict[kab_key] = {
                "kabupaten": kab_key, "total_prelist": 0, "total_draft": 0, "total_open": 0,
                "total_submitted": 0, "total_rejected": 0, "total_approved": 0,
                "total_submitted_pencacah": 0, "total_submitted_respondent": 0,
                "persentase": 0, "new_usaha_overall": 0, "new_rumah_overall": 0,
                "kecamatan_list": []
            }
                
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
            "persentase": round(perc_kec, 2), "new_usaha": 0, "new_rumah": 0
        })

    se_ub_arr = []
    for kab in sorted(kab_dict.keys()):
        data = kab_dict[kab]
        if data["total_prelist"] > 0:
            data["persentase"] = round(data["total_submitted"] / data["total_prelist"] * 100, 2)
        se_ub_arr.append(data)
        
    ipas_data['se_ub'] = se_ub_arr
    
    new_json = json.dumps(ipas_data, ensure_ascii=False, indent=2)
    new_content = content[:match.start(1)] + new_json + content[match.end(1):]
    
    with open("ipas_data.js", "w", encoding="utf-8") as f:
        f.write(new_content)
    print(" ✅ File lokal ipas_data.js (khusus SE UB) berhasil diperbarui!")

if __name__ == '__main__':
    main()

