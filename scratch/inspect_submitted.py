import os
import json
import re

script_dir = "/Users/jihanmaisaroh/scrap_fasih"
ipas_path = os.path.join(script_dir, "ipas_data.js")

if not os.path.exists(ipas_path):
    print("ipas_data.js not found")
    exit(1)

with open(ipas_path, "r", encoding="utf-8") as f:
    content = f.read()

json_match = re.search(r"window\.IPAS_DATA\s*=\s*(\{.*?\});", content, re.DOTALL)
if not json_match:
    print("Could not parse IPAS_DATA")
    exit(1)

ipas_data = json.loads(json_match.group(1))
se_umum = ipas_data.get("se_umum", [])

print("PASSED DATA IN ipas_data.js FOR EACH KABUPATEN:")
print(f"{'Kabupaten':<30} | {'Prelist':<8} | {'Draft':<8} | {'Open':<8} | {'Submitted':<10} | {'Approved':<8} | {'Rejected':<8}")
print("-" * 90)

total_prelist = 0
total_draft = 0
total_open = 0
total_submitted = 0
total_approved = 0
total_rejected = 0

for item in se_umum:
    kab = item.get("kabupaten", "")
    prelist = item.get("total_prelist", 0)
    draft = item.get("total_draft", 0)
    open_val = item.get("total_open", 0)
    sub = item.get("total_submitted", 0)
    app = item.get("total_approved", 0)
    rej = item.get("total_rejected", 0)
    
    print(f"{kab:<30} | {prelist:<8} | {draft:<8} | {open_val:<8} | {sub:<10} | {app:<8} | {rej:<8}")
    
    total_prelist += prelist
    total_draft += draft
    total_open += open_val
    total_submitted += sub
    total_approved += app
    total_rejected += rej

print("-" * 90)
print(f"{'TOTAL':<30} | {total_prelist:<8} | {total_draft:<8} | {total_open:<8} | {total_submitted:<10} | {total_approved:<8} | {total_rejected:<8}")

# Calculate the derived "SUBMITTED BY Pencacah"
unprocessed = total_submitted - total_approved - total_rejected
print(f"\nDerived 'SUBMITTED BY Pencacah' (Total Submitted - Approved - Rejected) = {unprocessed}")
