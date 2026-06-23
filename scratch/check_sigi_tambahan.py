import json
import gzip
import base64
import os

script_dir = "/Users/jihanmaisaroh/scrap_fasih"

def is_tambahan(code_identity):
    if not code_identity:
        return False
    parts = [p.strip() for p in code_identity.split(" - ")]
    if len(parts) < 2:
        return False
    source = parts[1].upper()
    known_sources = {"DTSEN", "UMK", "UM", "UMB", "UMKM", "SE2026", "SE26", "PDRB", "PAPI", "CAWI", "CAPI", "UB"}
    if source in known_sources:
        return False
    if source.startswith("SE26") or source.startswith("SE2026"):
        return False
    return True

granular_file = os.path.join(script_dir, "granular_assignments_se_umum_7210.json")
if not os.path.exists(granular_file):
    print("Granular file for Sigi not found!")
    exit(1)

with open(granular_file, "r") as f:
    gran_data = json.load(f)

comp = gran_data["compressed_data"]
raw = json.loads(gzip.decompress(base64.b64decode(comp)).decode('utf-8'))

targets = raw["targets"]
print(f"Total targets: {len(targets)}")

tambahan_count = 0
target_count = 0
for t in targets:
    # t = [id, codeIdentity, name, statIdx, petIdx, regIdx, dateModified, surveyType]
    code_id = t[1]
    if is_tambahan(code_id):
        tambahan_count += 1
    else:
        target_count += 1

print(f"Targets (is_tambahan=False): {target_count}")
print(f"Tambahan (is_tambahan=True): {tambahan_count}")
