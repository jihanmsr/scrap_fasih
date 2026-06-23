import json
import gzip
import base64
import csv
from datetime import datetime

input_file = "/Users/jihanmaisaroh/scrap_fasih/granular_assignments.json"
output_file = "/Users/jihanmaisaroh/scrap_fasih/granular_assignments.csv"

print(f"Reading {input_file}...")
with open(input_file, "r", encoding="utf-8") as f:
    data = json.load(f)

comp = data.get("compressed_data")
if not comp:
    print("Error: No compressed data found in json.")
    exit(1)

print("Decompressing data...")
raw = json.loads(gzip.decompress(base64.b64decode(comp)).decode('utf-8'))

regions = raw.get("regions", [])
petugas = raw.get("petugas", [])
statuses = raw.get("statuses", [])
targets = raw.get("targets", [])

print(f"Loaded {len(targets)} targets. Writing to {output_file}...")

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

with open(output_file, "w", encoding="utf-8", newline="") as f_out:
    writer = csv.writer(f_out)
    writer.writerow(headers)
    
    for i, t in enumerate(targets):
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
        
        writer.writerow([
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
        
        if (i + 1) % 100000 == 0:
            print(f"Processed {i + 1} rows...")

print("Successfully written all rows to CSV!")
