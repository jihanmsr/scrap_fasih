import csv
import json
import glob
import os

csv_files = glob.glob("fast_petugas_all_*.csv")
if not csv_files:
    print("No CSV found")
    exit(1)
latest_csv = max(csv_files, key=os.path.getmtime)
print(f"Using {latest_csv}")

region_map = {}
with open(latest_csv, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        email = row.get("Email", "").strip().lower()
        reg = row.get("Region Code", "").strip()
        if email and reg:
            if email not in region_map:
                region_map[email] = []
            if reg not in region_map[email]:
                region_map[email].append(reg)

with open("petugas_region_map.js", "w", encoding='utf-8') as f:
    f.write(f"window.PETUGAS_REGION_MAP = {json.dumps(region_map)};\n")
print("Updated petugas_region_map.js")
