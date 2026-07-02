import json
import base64
import gzip
import os

def main():
    script_dir = "/Users/jihanmaisaroh/scrap_fasih"
    json_path = os.path.join(script_dir, "granular_assignments_se_umum_7202.json")
    
    if not os.path.exists(json_path):
        print(f"File {json_path} tidak ditemukan.")
        return
        
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    compressed_bytes = base64.b64decode(data["compressed_data"])
    raw_json_str = gzip.decompress(compressed_bytes).decode('utf-8')
    payload = json.loads(raw_json_str)
    
    statuses_list = payload.get("statuses", [])
    targets = payload.get("targets", [])
    
    print(f"Total targets in 7202: {len(targets)}")
    
    valid_epoch_count = 0
    non_open_count = 0
    
    for t in targets:
        stat_idx = t[3]
        epoch_mod = t[6]
        status_str = statuses_list[stat_idx] if stat_idx < len(statuses_list) else "UNKNOWN"
        
        if status_str != "OPEN" and status_str != "DRAFT":
            non_open_count += 1
            if epoch_mod > 0:
                valid_epoch_count += 1
                    
    print(f"Non-open/draft count: {non_open_count}")
    print(f"Valid epoch count: {valid_epoch_count}")

if __name__ == "__main__":
    main()
