import os
import json
import gzip
import base64
import glob

script_dir = "/Users/jihanmaisaroh/scrap_fasih"
partition_files = glob.glob(os.path.join(script_dir, "granular_assignments_se_umum_*.json"))

sources = {}

for fpath in partition_files:
    basename = os.path.basename(fpath)
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)
    comp = data.get("compressed_data")
    if comp:
        raw = json.loads(gzip.decompress(base64.b64decode(comp)).decode('utf-8'))
        for t in raw.get("targets", []):
            code_id = t[1]
            if not code_id:
                continue
            parts = [p.strip() for p in code_id.split(" - ")]
            if len(parts) >= 2:
                source = parts[1].upper()
                sources[source] = sources.get(source, 0) + 1
            else:
                sources["<NO_SOURCE_PART>"] = sources.get("<NO_SOURCE_PART>", 0) + 1

print("All sources found in partition files:")
for src, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
    print(f"  {src}: {count}")
