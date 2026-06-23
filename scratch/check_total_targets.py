import os
import json
import gzip
import base64
import glob

script_dir = "/Users/jihanmaisaroh/scrap_fasih"
fpath = os.path.join(script_dir, "granular_assignments.json")

if os.path.exists(fpath):
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)
    comp = data.get("compressed_data")
    if comp:
        raw = json.loads(gzip.decompress(base64.b64decode(comp)).decode('utf-8'))
        targets = raw.get("targets", [])
        statuses = raw.get("statuses", [])
        print(f"Total targets in master: {len(targets)}")
        
        status_counts = {}
        for t in targets:
            status = statuses[t[3]]
            status_counts[status] = status_counts.get(status, 0) + 1
            
        print("Status counts:")
        for s, count in sorted(status_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {s}: {count}")
else:
    print("Master granular_assignments.json not found.")
