import os
import json
from supabase import create_client

def main():
    env = {}
    with open(".env", "r") as f:
        for line in f:
            if "=" in line:
                k, v = line.strip().split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    url = env.get("SUPABASE_URL")
    key = env.get("SUPABASE_KEY")
    supabase = create_client(url, key)
    
    res = supabase.table("dashboard_store").select("value").eq("key", "granular_assignments").execute()
    if res.data:
        val = res.data[0]["value"]
        print("Keys inside val:", list(val.keys()) if isinstance(val, dict) else "Not a dict")
        if isinstance(val, dict):
            for k, v in val.items():
                print(f"Key: {k}, Type: {type(v)}, Sample/Length: {len(str(v)) if v else 0}")
                
if __name__ == "__main__":
    main()
