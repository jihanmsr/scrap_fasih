import json
import os

script_dir = "/Users/jihanmaisaroh/scrap_fasih"
with open(os.path.join(script_dir, "ipas_data.js"), "r") as f:
    content = f.read()

json_str = content.replace("window.IPAS_DATA = ", "").strip()
if json_str.endswith(";"):
    json_str = json_str[:-1]

ipas_data_full = json.loads(json_str)

for kab in ipas_data_full.get("se_umum", []):
    if "[10] SIGI" in kab.get("kabupaten", ""):
        kecs = kab.get("kecamatan_list", [])
        if kecs:
            print("Kecamatan Keys:", list(kecs[0].keys()))
            print("\nSample Kecamatan Item:")
            # print it cleanly but truncate any long arrays
            sample = dict(kecs[0])
            for k, v in sample.items():
                if isinstance(v, list):
                    print(f"  {k}: list of length {len(v)} (sample: {v[:2]})")
                else:
                    print(f"  {k}: {v}")
        break
