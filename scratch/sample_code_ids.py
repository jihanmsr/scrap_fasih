import os
import json
import gzip
import base64
import glob

script_dir = "/Users/jihanmaisaroh/scrap_fasih"
partition_files = glob.glob(os.path.join(script_dir, "granular_assignments_se_umum_*.json"))

print("=== SAMPLE TARGET CODES (is_tambahan=False) ===")
count = 0
for fpath in partition_files:
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)
    comp = data.get("compressed_data")
    if comp:
        raw = json.loads(gzip.decompress(base64.b64decode(comp)).decode('utf-8'))
        for t in raw.get("targets", []):
            code_id = t[1]
            if not code_id:
                continue
            
            # check is_tambahan logic
            parts = [p.strip() for p in code_id.split(" - ")]
            if len(parts) >= 2:
                source = parts[1].upper()
                known_sources = {"DTSEN", "UMK", "UM", "UMB", "UMKM", "SE2026", "SE26", "PDRB", "PAPI", "CAWI", "CAPI", "UB"}
                is_t = True
                if source in known_sources or source.startswith("SE26") or source.startswith("SE2026"):
                    is_t = False
                
                if not is_t:
                    print(f"codeIdentity: {code_id} | source: {source}")
                    count += 1
                    if count >= 30:
                        break
        if count >= 30:
            break
