import json
import gzip
import base64
import os

script_dir = "/Users/jihanmaisaroh/scrap_fasih"
local_file = os.path.join(script_dir, "granular_assignments_se_umum_7210.json")

if os.path.exists(local_file):
    with open(local_file, "r") as f:
        data = json.load(f)
    comp = data.get("compressed_data")
    if comp:
        raw = json.loads(gzip.decompress(base64.b64decode(comp)).decode('utf-8'))
        print("Local file targets count:", len(raw.get("targets", [])))
        print("Local file updated_at:", data.get("updated_at"))
    else:
        print("compressed_data not found in local file.")
else:
    print("Local file not found!")
