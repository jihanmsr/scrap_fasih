import os
import json
import gzip
import base64
import csv
import glob
from datetime import datetime
import pandas as pd

kab_names = {
    "7201": "BANGGAI KEPULAUAN",
    "7202": "BANGGAI",
    "7203": "MOROWALI",
    "7204": "POSO",
    "7205": "DONGGALA",
    "7206": "TOLI-TOLI",
    "7207": "BUOL",
    "7208": "PARIGI MOUTONG",
    "7209": "TOJO UNA-UNA",
    "7210": "SIGI",
    "7211": "BANGGAI LAUT",
    "7212": "MOROWALI UTARA",
    "7271": "PALU"
}

csv_dir = "/Users/jihanmaisaroh/scrap_fasih/csv_reports"
excel_dir = "/Users/jihanmaisaroh/scrap_fasih/excel_reports"

os.makedirs(csv_dir, exist_ok=True)
os.makedirs(excel_dir, exist_ok=True)

headers = [
    "target_id",
    "code_id",
    "target_name",
    "status",
    "petugas_username",
    "petugas_fullname",
    "kab_code",
    "kab_name",
    "kec_code",
    "kec_name",
    "desa_code",
    "desa_name",
    "sls_code",
    "sls_name",
    "sub_sls_code",
    "sub_sls_name",
    "epoch_mod",
    "date_modified",
    "survey_type"
]

def process_file(json_path):
    print(f"Processing {json_path}...")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    comp = data.get("compressed_data")
    if not comp:
        print(f"No compressed data found in {json_path}")
        return []

    raw = json.loads(gzip.decompress(base64.b64decode(comp)).decode('utf-8'))
    regions = raw.get("regions", [])
    petugas = raw.get("petugas", [])
    statuses = raw.get("statuses", [])
    targets = raw.get("targets", [])

    rows = []
    for t in targets:
        tid = t[0]
        code_id = t[1]
        name = t[2]
        
        stat_idx = t[3]
        status = statuses[stat_idx] if (0 <= stat_idx < len(statuses)) else ""
        
        pet_idx = t[4]
        pet_username = ""
        pet_fullname = ""
        if 0 <= pet_idx < len(petugas):
            pet_username = petugas[pet_idx][0]
            pet_fullname = petugas[pet_idx][1]
            
        reg_idx = t[5]
        reg = regions[reg_idx] if (0 <= reg_idx < len(regions)) else [""] * 10
        if len(reg) < 10:
            reg = reg + [""] * (10 - len(reg))
            
        kab_code = reg[0]
        kab_name = reg[1]
        kec_code = reg[2]
        kec_name = reg[3]
        desa_code = reg[4]
        desa_name = reg[5]
        sls_code = reg[6]
        sls_name = reg[7]
        sub_sls_code = reg[8]
        sub_sls_name = reg[9]
        
        epoch_mod = t[6]
        try:
            date_modified = datetime.fromtimestamp(epoch_mod).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            date_modified = ""
            
        survey_flag = t[7]
        survey_type = "se_ub" if survey_flag == 1 else "se_umum"
        
        rows.append([
            tid,
            code_id,
            name,
            status,
            pet_username,
            pet_fullname,
            kab_code,
            kab_name,
            kec_code,
            kec_name,
            desa_code,
            desa_name,
            sls_code,
            sls_name,
            sub_sls_code,
            sub_sls_name,
            epoch_mod,
            date_modified,
            survey_type
        ])
    return rows

files = glob.glob("/Users/jihanmaisaroh/scrap_fasih/granular_assignments_se_*.json")
for fpath in sorted(files):
    basename = os.path.basename(fpath)
    name_part = basename.replace("granular_assignments_", "").replace(".json", "")
    
    rows = process_file(fpath)
    if not rows:
        print(f"Skipping {fpath} because it is empty.")
        continue
        
    csv_path = os.path.join(csv_dir, f"{name_part}.csv")
    excel_path = os.path.join(excel_dir, f"{name_part}.xlsx")
    
    print(f"Saving CSV: {csv_path}")
    with open(csv_path, "w", encoding="utf-8", newline="") as f_out:
        writer = csv.writer(f_out)
        writer.writerow(headers)
        writer.writerows(rows)
        
    print(f"Saving Excel: {excel_path}")
    df = pd.DataFrame(rows, columns=headers)
    df.to_excel(excel_path, index=False, engine='openpyxl')

print("All partition files processed successfully!")
