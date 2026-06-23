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

print(f"{'Kabupaten':<30} | {'Report API Total':<18} | {'Datatable Net':<18} | {'Diff':<10}")
print("-" * 85)

total_report_api = 0
total_datatable_net = 0

for item in se_umum:
    kab = item.get("kabupaten", "")
    datatable_total = item.get("total_prelist", 0)
    datatable_usaha = item.get("new_usaha_overall", 0)
    datatable_rumah = item.get("new_rumah_overall", 0)
    datatable_net = datatable_total - datatable_usaha - datatable_rumah
    
    kab_report_sum = 0
    for kec in item.get("kecamatan_list", []):
        k_total = kec.get("total_prelist", 0)
        k_usaha = kec.get("new_usaha_overall", 0)
        k_rumah = kec.get("new_rumah_overall", 0)
        k_report_baseline = k_total - k_usaha - k_rumah
        kab_report_sum += k_report_baseline
        
    diff = datatable_net - kab_report_sum
    print(f"{kab:<30} | {kab_report_sum:<18} | {datatable_net:<18} | {diff:<10}")
    total_report_api += kab_report_sum
    total_datatable_net += datatable_net

print("-" * 85)
print(f"{'TOTAL':<30} | {total_report_api:<18} | {total_datatable_net:<18} | {total_datatable_net - total_report_api:<10}")
