import json
import base64
import gzip
import os

def main():
    script_dir = "/Users/jihanmaisaroh/scrap_fasih"
    json_path = os.path.join(script_dir, "granular_assignments_se_umum_7212.json")
    
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    compressed_bytes = base64.b64decode(data["compressed_data"])
    raw_json_str = gzip.decompress(compressed_bytes).decode('utf-8')
    payload = json.loads(raw_json_str)
    
    statuses_list = payload.get("statuses", [])
    targets = payload.get("targets", [])
    
    print("Statuses list in JSON:", statuses_list)
    
    status_counts = {}
    for t in targets:
        stat_idx = t[3]
        status_str = statuses_list[stat_idx] if stat_idx < len(statuses_list) else "UNKNOWN"
        status_counts[status_str] = status_counts.get(status_str, 0) + 1
        
    print("Counts per status:")
    for status, count in status_counts.items():
        print(f" - {status}: {count}")

if __name__ == "__main__":
    main()
