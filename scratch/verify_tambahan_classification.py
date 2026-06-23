import json
import gzip
import base64
import os
import re

script_dir = "/Users/jihanmaisaroh/scrap_fasih"
fpath = os.path.join(script_dir, "granular_assignments.json")

def is_tambahan_old(code_identity):
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

def is_tambahan_new(code_identity):
    if not code_identity:
        return False
    cleaned = code_identity.strip()
    if not cleaned.startswith("72"):
        return True
    parts = [p.strip() for p in cleaned.split(" - ")]
    if len(parts) < 2:
        return False
    source = parts[1].upper()
    known_sources = {"DTSEN", "UMK", "UM", "UMB", "UMKM", "SE2026", "SE26", "PDRB", "PAPI", "CAWI", "CAPI", "UB"}
    if source in known_sources:
        return False
    if source.startswith("SE26") or source.startswith("SE2026"):
        return False
    return True

if not os.path.exists(fpath):
    print("Master granular_assignments.json not found.")
    exit(1)

with open(fpath, "r", encoding="utf-8") as f:
    data = json.load(f)

comp = data.get("compressed_data")
raw = json.loads(gzip.decompress(base64.b64decode(comp)).decode('utf-8'))
targets = raw.get("targets", [])
regions = raw.get("regions", [])

kab_counts = {}

for t in targets:
    code_id = t[1]
    survey_flag = t[7]
    if survey_flag != 0:
        continue
    
    was_target = not is_tambahan_old(code_id)
    is_target = not is_tambahan_new(code_id)
    
    if was_target and not is_target:
        # Get kabupaten name/code from region index
        reg_idx = t[5]
        kab_name = "Unknown"
        kab_code = "Unknown"
        if reg_idx >= 0 and reg_idx < len(regions):
            kab_code = regions[reg_idx][0]
            kab_name = regions[reg_idx][1]
            
        key = (kab_code, kab_name)
        kab_counts[key] = kab_counts.get(key, 0) + 1

print("=== CONVERTED RECORDS BY KABUPATEN ===")
for (code, name), count in sorted(kab_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"  {code} | {name:<25}: {count} records")
print(f"Total: {sum(kab_counts.values())}")
