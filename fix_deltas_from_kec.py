import json
import re

# Read ipas_data.js
with open("ipas_data.js", "r") as f:
    ipas_content = f.read()
match = re.search(r'window\.IPAS_DATA\s*=\s*(\{.*?\});', ipas_content, re.DOTALL)
if not match:
    print("Could not parse ipas_data.js")
    exit(1)
ipas_data = json.loads(match.group(1))

# Process se_umum
for kab in ipas_data.get("se_umum", []):
    prelist = kab.get("total_prelist", 0)
    
    # Sum up from kecamatan
    sum_yesterday = 0
    sum_two_days = 0
    for kec in kab.get("kecamatan_list", []):
        sum_yesterday += kec.get("yesterday_completed", 0)
        sum_two_days += kec.get("two_days_ago_completed", 0)
        
    print(f"Kabupaten {kab['kabupaten']}: sum_yc={sum_yesterday}, sum_2c={sum_two_days}")
    
    if prelist > 0:
        kab["delta_kemarin_persen"] = round((sum_yesterday / prelist) * 100, 2)
        kab["delta_lusa_persen"] = round((sum_two_days / prelist) * 100, 2)
    else:
        kab["delta_kemarin_persen"] = 0.0
        kab["delta_lusa_persen"] = 0.0

# Same for se_ub
for kab in ipas_data.get("se_ub", []):
    prelist = kab.get("total_prelist", 0)
    sum_yesterday = sum(kec.get("yesterday_completed", 0) for kec in kab.get("kecamatan_list", []))
    sum_two_days = sum(kec.get("two_days_ago_completed", 0) for kec in kab.get("kecamatan_list", []))
    if prelist > 0:
        kab["delta_kemarin_persen"] = round((sum_yesterday / prelist) * 100, 2)
        kab["delta_lusa_persen"] = round((sum_two_days / prelist) * 100, 2)
    else:
        kab["delta_kemarin_persen"] = 0.0
        kab["delta_lusa_persen"] = 0.0

new_json = json.dumps(ipas_data, indent=2)
new_content = f"window.IPAS_DATA = {new_json};\n"

with open("ipas_data.js", "w") as f:
    f.write(new_content)

print("Fixed deltas using kecamatan_list data")
