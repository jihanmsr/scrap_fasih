import json
import gzip
import base64
import os
import glob

script_dir = "/Users/jihanmaisaroh/scrap_fasih"
files = glob.glob(os.path.join(script_dir, "granular_assignments_se_umum_*.json"))
files.sort()

print(f"{'Filename':<40} | {'Desa Capped at 1000':<50}")
print("-" * 100)

for f in files:
    with open(f, "r") as fh:
        gran_data = json.load(fh)
    
    comp = gran_data["compressed_data"]
    raw = json.loads(gzip.decompress(base64.b64decode(comp)).decode('utf-8'))
    targets = raw["targets"]
    regions = raw["regions"]
    
    desa_counts = {}
    for t in targets:
        reg = regions[t[5]]
        desa_code = reg[4]
        desa_name = reg[5]
        kec_name = reg[3]
        if desa_code not in desa_counts:
            desa_counts[desa_code] = {"name": f"{kec_name} - {desa_name}", "count": 0}
        desa_counts[desa_code]["count"] += 1
        
    capped = []
    for d_code, d_info in desa_counts.items():
        if d_info["count"] == 1000:
            capped.append(f"{d_info['name']} ({d_info['count']})")
            
    if capped:
        print(f"{os.path.basename(f):<40} | {', '.join(capped[:3])} ({len(capped)} total)")
    else:
        print(f"{os.path.basename(f):<40} | None")
