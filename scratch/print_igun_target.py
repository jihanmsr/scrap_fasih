import json
import gzip
import base64

with open("granular_assignments_se_umum_7210.json", "r", encoding="utf-8") as f:
    data = json.load(f)

raw = json.loads(gzip.decompress(base64.b64decode(data["compressed_data"])).decode('utf-8'))
targets = raw.get("targets", [])
petugas = raw.get("petugas", [])

# Find igun
igun_idx = -1
for i, p in enumerate(petugas):
    if "igun" in p[0].lower():
        igun_idx = i
        break

print(f"igun index: {igun_idx}")

for t in targets:
    if t[4] == igun_idx or t[8] == igun_idx:
        print("Found target with igun:", t)

