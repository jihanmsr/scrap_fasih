import os
import json
import re

script_dir = "/Users/jihanmaisaroh/scrap_fasih"

# Load ipas_data.js
with open(os.path.join(script_dir, "ipas_data.js"), "r", encoding="utf-8") as f:
    content = f.read()

json_match = re.search(r"window\.IPAS_DATA\s*=\s*(\{.*?\});", content, re.DOTALL)
if not json_match:
    print("Could not find window.IPAS_DATA in ipas_data.js")
    exit(1)

ipas_data = json.loads(json_match.group(1))
se_umum_sls_status = ipas_data.get("se_umum_sls_status", {})

sigi_sls = {}
total_targets_in_sls = 0

for sls_code, status_data in se_umum_sls_status.items():
    if sls_code.startswith("7210"):
        sigi_sls[sls_code] = status_data
        # status_data = {"target": {"STATUS_NAME": count}, "nontarget": ...}
        targets = status_data.get("target", {})
        sls_sum = sum(targets.values())
        total_targets_in_sls += sls_sum

print(f"Total Sigi SLS codes in se_umum_sls_status: {len(sigi_sls)}")
print(f"Total targets across these SLS codes: {total_targets_in_sls}")

# Let's see a sample SLS entry
if sigi_sls:
    sample_key = list(sigi_sls.keys())[0]
    print(f"\nSample SLS entry ({sample_key}):")
    print(sigi_sls[sample_key])
