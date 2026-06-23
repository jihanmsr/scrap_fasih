import json
import gzip
import base64
import os

script_dir = "/Users/jihanmaisaroh/scrap_fasih"
local_file = os.path.join(script_dir, "granular_assignments_se_umum_7210.json")

with open(local_file, "r") as f:
    data = json.load(f)

comp = data.get("compressed_data")
raw = json.loads(gzip.decompress(base64.b64decode(comp)).decode('utf-8'))
targets = raw.get("targets", [])
regions = raw.get("regions", [])

kab_names = {}
for t in targets:
    reg_idx = t[5]
    reg = regions[reg_idx]
    kab_name = reg[1]
    kab_names[kab_name] = kab_names.get(kab_name, 0) + 1

print("Unique kab_name values in Sigi partition targets:")
for k, v in kab_names.items():
    print(f"  '{k}': {v} targets")
