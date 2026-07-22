import json
import re
from datetime import datetime, timedelta

# Read daily_summary.js
with open("daily_summary.js", "r") as f:
    content = f.read()
match = re.search(r'window\.DAILY_SUMMARY\s*=\s*(\[.*?\]);', content, re.DOTALL)
if not match:
    print("Could not parse daily_summary.js")
    exit(1)
daily_summary = json.loads(match.group(1))

# Read ipas_data.js
with open("ipas_data.js", "r") as f:
    ipas_content = f.read()
match = re.search(r'window\.IPAS_DATA\s*=\s*(\{.*?\});', ipas_content, re.DOTALL)
if not match:
    print("Could not parse ipas_data.js")
    exit(1)
ipas_data = json.loads(match.group(1))

# We want H-1 (yesterday) and H-2 (lusa)
today = datetime.now()
h1_date_str = (today - timedelta(days=1)).strftime("%Y-%m-%d")
h2_date_str = (today - timedelta(days=2)).strftime("%Y-%m-%d")
h3_date_str = (today - timedelta(days=3)).strftime("%Y-%m-%d")

# Process se_umum
if "se_umum" in ipas_data:
    for kab in ipas_data["se_umum"]:
        kab_name = kab.get("kabupaten", "")
        # Clean kab name: "[01] BANGGAI KEPULAUAN" -> "BANGGAI KEPULAUAN"
        kab_clean = re.sub(r'\[\d+\]', '', kab_name).strip().upper()
        
        # Get total_submitted for h1, h2, h3
        def get_sub(date_str):
            for row in daily_summary:
                if row.get("tanggal") == date_str and row.get("kabupaten", "").upper() == kab_clean:
                    return row.get("total_submitted", 0)
            return None
            
        sub_h1 = get_sub(h1_date_str)
        sub_h2 = get_sub(h2_date_str)
        sub_h3 = get_sub(h3_date_str)
        
        prelist = kab.get("total_prelist", 0)
        
        if prelist > 0:
            if sub_h1 is not None and sub_h2 is not None:
                tc1 = sub_h1 - sub_h2
                kab["delta_kemarin_persen"] = round((tc1 / prelist) * 100, 2)
            else:
                kab["delta_kemarin_persen"] = 0.0
                
            if sub_h2 is not None and sub_h3 is not None:
                tc2 = sub_h2 - sub_h3
                kab["delta_lusa_persen"] = round((tc2 / prelist) * 100, 2)
            else:
                kab["delta_lusa_persen"] = 0.0
        else:
            kab["delta_kemarin_persen"] = 0.0
            kab["delta_lusa_persen"] = 0.0

# Process se_ub (do same)
if "se_ub" in ipas_data:
    for kab in ipas_data["se_ub"]:
        kab["delta_kemarin_persen"] = 0.0
        kab["delta_lusa_persen"] = 0.0

new_json = json.dumps(ipas_data, indent=2)
new_content = f"window.IPAS_DATA = {new_json};\n"

with open("ipas_data.js", "w") as f:
    f.write(new_content)

print("Injected delta_kemarin_persen and delta_lusa_persen into ipas_data.js")
