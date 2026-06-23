import json
import gzip
import base64
import os
import re

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

# Classify patterns
patterns = {}
examples = {}

for t in targets:
    code_id = t[1]
    survey_flag = t[7]
    if survey_flag != 0:
        continue
    if not code_id:
        continue
    parts = [p.strip() for p in code_id.split(" - ")]
    if len(parts) < 2:
        # Determine pattern
        if code_id.startswith("SE26") or code_id.startswith("SE2026"):
            pat_name = "Starts with SE26/SE2026"
        elif code_id.isdigit():
            if len(code_id) == 16:
                pat_name = "16-digit numeric (SLS/Building code)"
            elif len(code_id) == 13:
                pat_name = "13-digit numeric (NIB?)"
            elif len(code_id) == 14:
                pat_name = "14-digit numeric (NIB?)"
            else:
                pat_name = f"{len(code_id)}-digit numeric"
        else:
            pat_name = "Other alphanumeric"
            
        patterns[pat_name] = patterns.get(pat_name, 0) + 1
        if pat_name not in examples:
            examples[pat_name] = []
        if len(examples[pat_name]) < 5:
            examples[pat_name].append(f"{code_id} | name: {t[2]}")

print("=== PATTERNS OF NO_SOURCE RECORDS ===")
for pat, count in sorted(patterns.items(), key=lambda x: x[1], reverse=True):
    print(f"\nPattern: '{pat}' (Count: {count})")
    print("Examples:")
    for ex in examples[pat]:
        print(f"  - {ex}")

print(f"\nTotal no-source records: {sum(patterns.values())}")
