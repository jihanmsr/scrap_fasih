import json
import gzip
import base64
import os

script_dir = "/Users/jihanmaisaroh/scrap_fasih"
fpath = os.path.join(script_dir, "granular_assignments.json")

if not os.path.exists(fpath):
    print("Master granular_assignments.json not found.")
    exit(1)

with open(fpath, "r", encoding="utf-8") as f:
    data = json.load(f)

comp = data.get("compressed_data")
raw = json.loads(gzip.decompress(base64.b64decode(comp)).decode('utf-8'))
targets = raw.get("targets", [])

print("=== SE UB TARGET CODES NOT STARTING WITH 72 ===")
count = 0
for t in targets:
    code_id = t[1]
    survey_flag = t[7]
    if survey_flag != 1: # only SE UB
        continue
    if not code_id:
        continue
    if not code_id.strip().startswith("72"):
        print(f"ID: {t[0]} | codeIdentity: {code_id} | name: {t[2]}")
        count += 1
        if count >= 30:
            break
print(f"Total found: {count}")
