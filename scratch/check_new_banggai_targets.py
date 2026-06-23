import json
import gzip
import base64
import os

script_dir = "/Users/jihanmaisaroh/scrap_fasih"
fpath = os.path.join(script_dir, "granular_assignments_se_umum_7202.json")

with open(fpath, "r") as f:
    data = json.load(f)

comp = data.get("compressed_data")
raw = json.loads(gzip.decompress(base64.b64decode(comp)).decode('utf-8'))
targets = raw.get("targets", [])

print("New target count in Banggai (7202):", len(targets))
print("Updated at:", data.get("updated_at"))
