import json
import gzip
import base64
import re
import os

script_dir = "/Users/jihanmaisaroh/scrap_fasih"

# Load granular assignments for Sigi
granular_file = os.path.join(script_dir, "granular_assignments_se_umum_7210.json")
with open(granular_file, "r") as f:
    gran_data = json.load(f)

comp = gran_data["compressed_data"]
raw = json.loads(gzip.decompress(base64.b64decode(comp)).decode('utf-8'))
targets = raw["targets"]
regions = raw["regions"]
petugas = raw["petugas"]

# Total targets in granular file
print(f"Total targets in Sigi granular: {len(targets)}")

# Count by assignment
assigned_count = 0
unassigned_count = 0
pet_assigned_set = set()

for t in targets:
    pet_idx = t[4]
    if pet_idx != -1:
        assigned_count += 1
        pet_assigned_set.add(petugas[pet_idx][0]) # username
    else:
        unassigned_count += 1

print(f"Assigned count in granular: {assigned_count}")
print(f"Unassigned count in granular: {unassigned_count}")
print(f"Unique assigned officers in granular: {len(pet_assigned_set)}")

# Now look at assign_data.js
with open(os.path.join(script_dir, "assign_data.js"), "r", encoding="utf-8") as f:
    js_content = f.read()

# Find window.ASSIGN_DATA_UMUM
assign_data_umum_match = re.search(r'window\.ASSIGN_DATA_UMUM\s*=\s*(\[.*?\]);', js_content, re.DOTALL)
if assign_data_umum_match:
    assign_data_umum = json.loads(assign_data_umum_match.group(1))
    sigi_assign = next((x for x in assign_data_umum if x.get("kode_kab") == "7210"), None)
    print("\nSigi entry in window.ASSIGN_DATA_UMUM:")
    print(sigi_assign)
else:
    print("\nCould not find window.ASSIGN_DATA_UMUM in assign_data.js")

# Find window.PETUGAS_DATA_UMUM
petugas_data_umum_match = re.search(r'window\.PETUGAS_DATA_UMUM\s*=\s*(\[.*?\]);', js_content, re.DOTALL)
if petugas_data_umum_match:
    petugas_data_umum = json.loads(petugas_data_umum_match.group(1))
    print(f"\nTotal officers in PETUGAS_DATA_UMUM: {len(petugas_data_umum)}")
    
    # Let's count targets for Sigi officers from PETUGAS_DATA_UMUM
    # How? Let's check how many officers have regions starting with 7210
    sigi_officers = []
    total_regions_sigi = 0
    for p in petugas_data_umum:
        is_sigi = False
        sigi_regions = []
        for reg in p.get("regions", []):
            if reg.get("regionCode", "").startswith("7210"):
                is_sigi = True
                sigi_regions.append(reg)
        if is_sigi:
            sigi_officers.append((p.get("username"), len(p.get("regions")), len(sigi_regions)))
            total_regions_sigi += len(sigi_regions)
            
    print(f"Total Sigi officers in PETUGAS_DATA_UMUM: {len(sigi_officers)}")
    print(f"Total Sigi SLSs assigned to them: {total_regions_sigi}")
else:
    print("\nCould not find window.PETUGAS_DATA_UMUM in assign_data.js")
