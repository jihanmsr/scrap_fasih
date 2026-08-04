import re

with open("scrape_dashboard_via_cdp.py", "r") as f:
    content = f.read()

replacement = """        kec_list = results_map[wilayah_code]
        
        # SAFETY CHECK: If kec_list is empty but we previously had data, KEEP the old data!
        if not kec_list and prev_kab.get("total_prelist", 0) > 0:
            print(f"  [WARNING] API return kosong untuk {kab_name}. Menggunakan data kemarin.")
            new_data.append(prev_kab)
            continue
            
        region_kab_info = region_kabupaten.get(wilayah_code, {})"""

content = content.replace("        kec_list = results_map[wilayah_code]\n        region_kab_info = region_kabupaten.get(wilayah_code, {})", replacement)

with open("scrape_dashboard_via_cdp.py", "w") as f:
    f.write(content)

print("Patched scrape_dashboard_via_cdp.py")
