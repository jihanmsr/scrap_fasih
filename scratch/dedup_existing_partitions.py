import os
import glob
import json
import base64
import gzip
from datetime import datetime
import subprocess
import sys

def main():
    workspace_dir = "/Users/jihanmaisaroh/scrap_fasih"
    print("Starting de-duplication of existing granular partitions...")
    
    # 1. Find all granular JSON files
    json_files = glob.glob(os.path.join(workspace_dir, "granular_assignments_*.json"))
    if not json_files:
        print("No partition files found.")
        return
        
    for filepath in json_files:
        basename = os.path.basename(filepath)
        print(f"\nProcessing {basename}...")
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            comp = data.get("compressed_data")
            if not comp:
                print(f"Skipping {basename} - no compressed_data key found.")
                continue
                
            # Decompress
            raw_payload_bytes = gzip.decompress(base64.b64decode(comp))
            raw_payload = json.loads(raw_payload_bytes.decode('utf-8'))
            
            regions = raw_payload.get("regions", [])
            petugas = raw_payload.get("petugas", [])
            statuses = raw_payload.get("statuses", [])
            targets = raw_payload.get("targets", [])
            remarks = raw_payload.get("remarks", {})
            
            print(f"  Original targets count: {len(targets)}")
            
            # De-duplicate
            seen_tids = {}
            for t in targets:
                tid = t[0]
                if tid not in seen_tids:
                    seen_tids[tid] = t
                else:
                    old_t = seen_tids[tid]
                    # Prefer non-OPEN status
                    old_status = statuses[old_t[3]].upper() if old_t[3] < len(statuses) else ""
                    new_status = statuses[t[3]].upper() if t[3] < len(statuses) else ""
                    
                    if new_status != "OPEN" and old_status == "OPEN":
                        seen_tids[tid] = t
                    elif old_status != "OPEN" and new_status == "OPEN":
                        pass
                    else:
                        # Compare modification epochs
                        if t[6] > old_t[6]:
                            seen_tids[tid] = t
            
            unique_targets = list(seen_tids.values())
            print(f"  De-duplicated targets count: {len(unique_targets)}")
            
            # Rebuild payload
            raw_payload["targets"] = unique_targets
            
            # Compress again
            raw_json_str = json.dumps(raw_payload, ensure_ascii=False)
            compressed_bytes = gzip.compress(raw_json_str.encode('utf-8'))
            new_base64_str = base64.b64encode(compressed_bytes).decode('utf-8')
            
            # Save original JSON file back
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump({
                    "compressed_data": new_base64_str,
                    "updated_at": datetime.now().isoformat(),
                    "survey_type_filter": data.get("survey_type_filter"),
                    "kab_code_filter": data.get("kab_code_filter")
                }, f, indent=2)
            print(f"  Saved de-duplicated JSON to {basename}")
            
            # Save JS version for local file fallback loading
            # e.g., granular_assignments_se_umum_7208.json -> window.PARTITION_SE_UMUM_7208
            part_name = basename.replace("granular_assignments_", "").replace(".json", "")
            var_name = f"PARTITION_{part_name.upper()}"
            js_filepath = filepath.replace(".json", ".js")
            
            with open(js_filepath, "w", encoding="utf-8") as f:
                f.write(f"window.{var_name} = {{\n")
                f.write(f"  \"compressed_data\": \"{new_base64_str}\",\n")
                f.write(f"  \"updated_at\": \"{datetime.now().isoformat()}\"\n")
                f.write("};\n")
            print(f"  Saved JS fallback file to {os.path.basename(js_filepath)} (window.{var_name})")
            
        except Exception as e:
            print(f"  [ERROR] Failed to process {basename}: {e}")
            
    # 2. Call merge_granulars.py
    print("\nCalling merge_granulars.py to compile the new master files and upload to Supabase...")
    sys.path.append(workspace_dir)
    from merge_granulars import merge_granulars
    merge_granulars()
    print("\nAll done!")

if __name__ == "__main__":
    main()
