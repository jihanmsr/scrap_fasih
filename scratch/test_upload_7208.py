import os
import json
import sys
from dotenv import load_dotenv

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from merge_granulars import load_supabase_config

def main():
    print("Connecting to Supabase...")
    supabase = load_supabase_config()
    
    fpath = "granular_assignments_se_umum_7208.json"
    if not os.path.exists(fpath):
        print(f"File {fpath} not found!")
        return
        
    print(f"Reading {fpath}...")
    with open(fpath, "r", encoding="utf-8") as f:
        d = json.load(f)
    comp = d.get("compressed_data")
    if not comp:
        print("compressed_data not found in file!")
        return
        
    print(f"Compressed data length: {len(comp)} characters.")
    import base64, gzip
    raw = gzip.decompress(base64.b64decode(comp)).decode('utf-8')
    payload_data = json.loads(raw)
    targets = payload_data['targets']
    seen = set()
    dedup = []
    for t in targets:
        if t[0] not in seen:
            seen.add(t[0])
            dedup.append(t)
    payload_data['targets'] = dedup
    raw_json = json.dumps(payload_data, ensure_ascii=False)
    comp_bytes = gzip.compress(raw_json.encode('utf-8'))
    b64 = base64.b64encode(comp_bytes).decode('utf-8')
    
    print(f"De-duplicated compressed data length: {len(b64)} characters.")
    
    payload = {
        "compressed_data": b64,
        "updated_at": d.get("updated_at")
    }
    
    print("Uploading to Supabase...")
    try:
        res = supabase.table("dashboard_store").upsert({"key": "granular_assignments_se_umum_7208", "value": payload}).execute()
        print("Success!", res)
    except Exception as e:
        print("Failed to upload:", e)

if __name__ == "__main__":
    main()
