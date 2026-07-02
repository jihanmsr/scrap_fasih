import json
import base64
import gzip
import os

def main():
    script_dir = "/Users/jihanmaisaroh/scrap_fasih"
    json_path = os.path.join(script_dir, "granular_assignments_se_umum_7211.json")
    
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    compressed_bytes = base64.b64decode(data["compressed_data"])
    raw_json_str = gzip.decompress(compressed_bytes).decode('utf-8')
    payload = json.loads(raw_json_str)
    
    targets = payload.get("targets", [])
    print(f"Sample targets:")
    for t in targets[:10]:
        print(t)

if __name__ == "__main__":
    main()
