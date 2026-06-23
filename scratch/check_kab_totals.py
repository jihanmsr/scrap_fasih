import os
import json
import gzip
import base64
import glob
import re

script_dir = "/Users/jihanmaisaroh/scrap_fasih"

# 1. Load ipas_data.js
with open(os.path.join(script_dir, "ipas_data.js"), "r", encoding="utf-8") as f:
    content = f.read()

json_match = re.search(r"window\.IPAS_DATA\s*=\s*(\{.*?\});", content, re.DOTALL)
ipas_data = json.loads(json_match.group(1)) if json_match else {}
se_umum_ipas = ipas_data.get("se_umum", [])

ipas_totals = {}
for item in se_umum_ipas:
    # item['kabupaten'] is e.g. "[10] SIGI"
    match = re.search(r"\[(\d+)\]\s*(.*)", item.get("kabupaten", ""))
    if match:
        kab_code = "72" + match.group(1)
        kab_name = match.group(2).strip()
        ipas_totals[kab_code] = {
            "name": kab_name,
            "total": item.get("total_prelist", 0)
        }

# 2. Read all partition files
partition_totals = {}
partition_files = glob.glob(os.path.join(script_dir, "granular_assignments_se_umum_*.json"))
for fpath in partition_files:
    basename = os.path.basename(fpath)
    # format is granular_assignments_se_umum_7210.json
    match = re.search(r"se_umum_(\d+)\.json", basename)
    if match:
        kab_code = match.group(1)
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
        comp = data.get("compressed_data")
        if comp:
            raw = json.loads(gzip.decompress(base64.b64decode(comp)).decode('utf-8'))
            targets = raw.get("targets", [])
            partition_totals[kab_code] = len(targets)

# Print comparison
print(f"{'KAB_CODE':<10} | {'KAB_NAME':<25} | {'IPAS_DATA':<12} | {'PARTITION':<12} | {'DIFF':<10}")
print("-" * 75)
total_ipas = 0
total_part = 0
for code in sorted(ipas_totals.keys()):
    name = ipas_totals[code]["name"]
    ip_val = ipas_totals[code]["total"]
    part_val = partition_totals.get(code, 0)
    diff = ip_val - part_val
    total_ipas += ip_val
    total_part += part_val
    print(f"{code:<10} | {name:<25} | {ip_val:<12} | {part_val:<12} | {diff:<10}")

print("-" * 75)
print(f"{'TOTAL':<10} | {'':<25} | {total_ipas:<12} | {total_part:<12} | {total_ipas - total_part:<10}")
