import json
import gzip
import base64
import os

script_dir = "/Users/jihanmaisaroh/scrap_fasih"
with open(os.path.join(script_dir, "granular_assignments_se_umum_7210.json"), "r") as f:
    gran_data = json.load(f)

comp = gran_data["compressed_data"]
raw = json.loads(gzip.decompress(base64.b64decode(comp)).decode('utf-8'))
targets = raw["targets"]
regions = raw["regions"]

biromaru_desas = {}
for t in targets:
    reg = regions[t[5]]
    kec_name = reg[3].upper()
    if "BIROMARU" in kec_name:
        desa_name = reg[5].upper()
        desa_code = reg[4]
        if desa_code not in biromaru_desas:
            biromaru_desas[desa_code] = {"name": desa_name, "count": 0}
        biromaru_desas[desa_code]["count"] += 1

print("Desas in Sigi Biromaru in Granular JSON:")
total_c = 0
for d_code, d_info in sorted(biromaru_desas.items(), key=lambda x: x[1]["name"]):
    print(f"  {d_info['name']} ({d_code}): {d_info['count']}")
    total_c += d_info['count']
print(f"Total Sigi Biromaru in Granular JSON: {total_c}")
