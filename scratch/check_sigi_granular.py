import json
import gzip
import base64
import os

script_dir = "/Users/jihanmaisaroh/scrap_fasih"

# Load region map
with open(os.path.join(script_dir, "region_map_sulteng_full.json"), "r") as f:
    region_map = json.load(f)

sigi_map = region_map["kabupaten"].get("7210", {})
print("=== SIGI IN REGION MAP ===")
print(f"Kab ID: {sigi_map.get('kab_id')}")
print(f"Kab Name: {sigi_map.get('kab_name')}")
kecamatans_map = sigi_map.get("kecamatan", {})
print(f"Total Kecamatan: {len(kecamatans_map)}")
map_desas = {}
for kec_code, kec in kecamatans_map.items():
    for desa_code, desa in kec.get("desa", {}).items():
        map_desas[desa_code] = {
            "kec_code": kec_code,
            "kec_name": kec.get("kec_name"),
            "desa_name": desa.get("desa_name"),
            "desa_id": desa.get("desa_id")
        }
print(f"Total Desa in region map: {len(map_desas)}")

# Load granular assignments for Sigi
granular_file = os.path.join(script_dir, "granular_assignments_se_umum_7210.json")
if not os.path.exists(granular_file):
    print("Granular file for Sigi not found!")
    exit(1)

with open(granular_file, "r") as f:
    gran_data = json.load(f)

comp = gran_data["compressed_data"]
raw = json.loads(gzip.decompress(base64.b64decode(comp)).decode('utf-8'))

targets = raw["targets"]
regions = raw["regions"]
print(f"\nTotal targets in Sigi granular assignments: {len(targets)}")

# Count targets per desa/kec in granular data
gran_desas = {}
for t in targets:
    # reg = [kab_code, kab_name, kec_code, kec_name, desa_code, desa_name, sls_code, sls_name]
    reg = regions[t[5]]
    desa_code = reg[4]
    desa_name = reg[5]
    kec_code = reg[2]
    kec_name = reg[3]
    
    if desa_code not in gran_desas:
        gran_desas[desa_code] = {
            "kec_code": kec_code,
            "kec_name": kec_name,
            "desa_name": desa_name,
            "count": 0
        }
    gran_desas[desa_code]["count"] += 1

print(f"Total unique Desa found in Sigi granular assignments: {len(gran_desas)}")

# Check if any desa in region map is missing from granular data
missing_desas = []
for d_code, d_info in map_desas.items():
    if d_code not in gran_desas:
        missing_desas.append(d_info)

print(f"\nDesas in region map but missing from Sigi granular data (Count: {len(missing_desas)}):")
for m in sorted(missing_desas, key=lambda x: (x["kec_name"], x["desa_name"])):
    print(f"  Kec: {m['kec_name']} ({m['kec_code']}) | Desa: {m['desa_name']} ({m['desa_id']})")
