import os
import json
import gzip
import base64
from supabase import create_client

def main():
    # Load .env
    env = {}
    with open(".env", "r") as f:
        for line in f:
            if "=" in line:
                k, v = line.strip().split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
                
    url = env.get("SUPABASE_URL")
    key = env.get("SUPABASE_KEY")
    supabase = create_client(url, key)
    
    print("Fetching 'granular_assignments' from Supabase...")
    res = supabase.table("dashboard_store").select("value").eq("key", "granular_assignments").execute()
    if not res.data:
        print("No granular_assignments key found in Supabase.")
        return
        
    val = res.data[0]["value"]
    print("Value type:", type(val))
    
    if isinstance(val, dict):
        comp = val.get("compressed_data")
        updated_at = val.get("updated_at")
        print(f"Loaded dict. Updated at: {updated_at}. Compressed string length: {len(comp) if comp else 0}")
        if comp:
            raw_bytes = base64.b64decode(comp)
            decomp = gzip.decompress(raw_bytes).decode('utf-8')
            data = json.loads(decomp)
            print("Decompressed payload keys:", list(data.keys()))
            print("Targets count:", len(data.get("targets", [])))
            print("Sample target:", data.get("targets", [])[0] if data.get("targets") else None)
            
if __name__ == "__main__":
    main()
