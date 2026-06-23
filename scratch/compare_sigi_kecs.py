import json
import gzip
import base64
import os

script_dir = "/Users/jihanmaisaroh/scrap_fasih"

# 1. Parse ipas_data.js to get Sigi's Kecamatan stats
with open(os.path.join(script_dir, "ipas_data.js"), "r") as f:
    content = f.read()

# Strip "window.IPAS_DATA = " and anything after the final ";"
json_str = content.replace("window.IPAS_DATA = ", "").strip()
if json_str.endswith(";"):
    json_str = json_str[:-1]

ipas_data_full = json.loads(json_str)

# Find Sigi in se_umum list
sigi_info = None
for kab in ipas_data_full.get("se_umum", []):
    if "[10] SIGI" in kab.get("kabupaten", ""):
        sigi_info = kab
        break

if not sigi_info:
    print("Could not find Sigi in ipas_data.js")
    exit(1)

print("Sigi Info Keys:", list(sigi_info.keys()))

ipas_kecs = {}
if "kecamatan_list" in sigi_info:
    for k in sigi_info["kecamatan_list"]:
        name = k.get("kec_name", "").upper()
        total_p = k.get("total_prelist", 0)
        ipas_kecs[name] = total_p
else:
    print("No kecamatan_list in Sigi Info!")

# 2. Get Kecamatan list from Granular Sigi JSON
with open(os.path.join(script_dir, "granular_assignments_se_umum_7210.json"), "r") as f:
    gran_data = json.load(f)

comp = gran_data["compressed_data"]
raw = json.loads(gzip.decompress(base64.b64decode(comp)).decode('utf-8'))
targets = raw["targets"]
regions = raw["regions"]

gran_kecs = {}
for t in targets:
    reg = regions[t[5]]
    kec_name = reg[3].upper()
    gran_kecs[kec_name] = gran_kecs.get(kec_name, 0) + 1

# Print comparison
print(f"\n{'KECAMATAN':<30} | {'IPAS TARGETS':<15} | {'GRANULAR TARGETS':<18} | {'DIFF':<10}")
print("-" * 80)
all_kecs = sorted(list(set(ipas_kecs.keys()) | set(gran_kecs.keys())))
total_ipas = 0
total_gran = 0
for k in all_kecs:
    ip_val = ipas_kecs.get(k, 0)
    gr_val = gran_kecs.get(k, 0)
    diff = ip_val - gr_val
    total_ipas += ip_val
    total_gran += gr_val
    print(f"{k:<30} | {ip_val:<15} | {gr_val:<18} | {diff:<10}")

print("-" * 80)
print(f"{'TOTAL':<30} | {total_ipas:<15} | {total_gran:<18} | {total_ipas - total_gran:<10}")
