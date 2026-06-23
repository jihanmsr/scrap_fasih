import json
import gzip
import base64
import os

json_path = "/Users/jihanmaisaroh/scrap_fasih/granular_assignments_se_umum_7210.json"
with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

comp = data.get("compressed_data")
raw = json.loads(gzip.decompress(base64.b64decode(comp)).decode('utf-8'))
targets = raw.get("targets", [])
print("Number of targets in JSON:", len(targets))

rows = []
seen = set()
duplicates = 0
for t in targets:
    tid = t[0]
    if tid in seen:
        duplicates += 1
    seen.add(tid)

print("Duplicates in targets list in JSON:", duplicates)
print("Unique targets in targets list in JSON:", len(seen))
