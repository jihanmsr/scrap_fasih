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
    print("Could not parse IPAS_DATA from js")
    exit(1)

ipas_data = json.loads(json_match.group(1))
se_umum = ipas_data.get("se_umum", [])

print(f"{'Kabupaten':<30} | {'Total':<10} | {'Usaha Baru':<10} | {'Rumah Baru':<10} | {'Net Prelist':<12}")
print("-" * 80)
sum_total = 0
sum_usaha = 0
sum_rumah = 0
sum_net = 0

for item in se_umum:
    kab = item.get("kabupaten", "")
    total = item.get("total_prelist", 0)
    usaha = item.get("new_usaha_overall", 0)
    rumah = item.get("new_rumah_overall", 0)
    net = total - usaha - rumah
    print(f"{kab:<30} | {total:<10} | {usaha:<10} | {rumah:<10} | {net:<12}")
    sum_total += total
    sum_usaha += usaha
    sum_rumah += rumah
    sum_net += net

print("-" * 80)
print(f"{'TOTAL':<30} | {sum_total:<10} | {sum_usaha:<10} | {sum_rumah:<10} | {sum_net:<12}")
