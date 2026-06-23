import json
import re
import os

script_dir = "/Users/jihanmaisaroh/scrap_fasih"

# Load assign_data.js
with open(os.path.join(script_dir, "assign_data.js"), "r", encoding="utf-8") as f:
    js_content = f.read()

# Load window.ASSIGN_SLS_DATA_UMUM
sls_match = re.search(r'window\.ASSIGN_SLS_DATA_UMUM\s*=\s*(\[.*?\]);', js_content, re.DOTALL)
if not sls_match:
    print("Could not find window.ASSIGN_SLS_DATA_UMUM in assign_data.js")
    exit(1)
assign_sls_data_umum = json.loads(sls_match.group(1))

# Load window.PETUGAS_DATA_UMUM
pet_match = re.search(r'window\.PETUGAS_DATA_UMUM\s*=\s*(\[.*?\]);', js_content, re.DOTALL)
if not pet_match:
    print("Could not find window.PETUGAS_DATA_UMUM in assign_data.js")
    exit(1)
petugas_data_umum = json.loads(pet_match.group(1))

# Build slsTotalMap
sls_total_map = {}
for sls in assign_sls_data_umum:
    code = sls.get("sls_code")
    if code:
        sls_total_map[code] = sls.get("total", 0)

# Calculate totalHH for Sigi officers
sigi_officers_total_target = 0
sigi_officers_count = 0

for p in petugas_data_umum:
    # Check if this officer has any region in Sigi (starting with 7210)
    is_sigi = False
    for r in p.get("regions", []):
        if r.get("regionCode", "").startswith("7210"):
            is_sigi = True
            break
            
    if is_sigi:
        sigi_officers_count += 1
        officer_total = 0
        for reg in p.get("regions", []):
            code = reg.get("regionCode", "")
            # mimic app.js logic:
            sls_code = code[:14] if len(code) == 16 else code
            officer_total += sls_total_map.get(sls_code, 0)
        sigi_officers_total_target += officer_total

print(f"Number of Sigi officers: {sigi_officers_count}")
print(f"Sum of totalHH for Sigi officers: {sigi_officers_total_target}")
