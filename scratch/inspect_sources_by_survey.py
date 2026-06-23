import json
import gzip
import base64
import os
import re

script_dir = "/Users/jihanmaisaroh/scrap_fasih"
fpath = os.path.join(script_dir, "granular_assignments.json")

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

if not os.path.exists(fpath):
    print("Master granular_assignments.json not found.")
    exit(1)

print("Loading master granular_assignments.json...")
with open(fpath, "r", encoding="utf-8") as f:
    data = json.load(f)

comp = data.get("compressed_data")
if not comp:
    print("No compressed data found.")
    exit(1)

print("Decompressing data...")
raw = json.loads(gzip.decompress(base64.b64decode(comp)).decode('utf-8'))
targets = raw.get("targets", [])
print(f"Total merged targets: {len(targets)}")

# Count sources for is_tambahan=False
sources_target = {}
sources_tambahan = {}

for t in targets:
    code_id = t[1]
    survey_flag = t[7]
    if survey_flag != 0: # only SE Umum
        continue
    
    if not code_id:
        continue
        
    parts = [p.strip() for p in code_id.split(" - ")]
    source = parts[1].upper() if len(parts) >= 2 else "<NO_SOURCE>"
    
    if is_tambahan(code_id):
        sources_tambahan[source] = sources_tambahan.get(source, 0) + 1
    else:
        sources_target[source] = sources_target.get(source, 0) + 1

print("\n=== SOURCES CLASSIFIED AS TARGET (is_tambahan=False) ===")
# Group SE26xxxx separately
se26_count = 0
other_sources = {}
for src, count in sorted(sources_target.items(), key=lambda x: x[1], reverse=True):
    if src.startswith("SE26") or src.startswith("SE2026"):
        se26_count += count
    else:
        other_sources[src] = count

print(f"SE26xxxx / SE2026xxxx patterns: {se26_count} records")
for src, count in sorted(other_sources.items(), key=lambda x: x[1], reverse=True):
    print(f"  {src}: {count}")

print(f"\nTotal Target (SE Umum): {se26_count + sum(other_sources.values())}")
print(f"Total Tambahan (SE Umum): {sum(sources_tambahan.values())}")
