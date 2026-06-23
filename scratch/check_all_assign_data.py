import re
import json
import os

script_dir = "/Users/jihanmaisaroh/scrap_fasih"
with open(os.path.join(script_dir, "assign_data.js"), "r", encoding="utf-8") as f:
    js_content = f.read()

assign_match = re.search(r'window\.ASSIGN_DATA_UMUM\s*=\s*(\[.*?\]);', js_content, re.DOTALL)
if assign_match:
    assign_data = json.loads(assign_match.group(1))
    print(f"{'KODE':<6} | {'KABUPATEN':<25} | {'TOTAL':<10} | {'ASSIGNED':<10} | {'UNASSIGNED':<10}")
    print("-" * 70)
    for item in sorted(assign_data, key=lambda x: x.get("kode_kab", "")):
        print(f"{item.get('kode_kab'):<6} | {item.get('nama_kab'):<25} | {item.get('total'):<10} | {item.get('assigned'):<10} | {item.get('have_not_assigned'):<10}")
else:
    print("Could not find window.ASSIGN_DATA_UMUM in assign_data.js")
