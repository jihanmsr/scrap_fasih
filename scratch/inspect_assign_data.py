import os
import json
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: Supabase credentials not found in .env")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    res = supabase.table("dashboard_store").select("value").eq("key", "assign_data").execute()
    if res.data:
        val = res.data[0]["value"]
        print("assign_data structure keys:", list(val.keys()))
        
        # Check lengths
        for k in ["assign_data_umum", "assign_data_ub", "assign_sls_data_umum", "assign_sls_data_ub", "petugas_data_umum", "petugas_data_ub"]:
            items = val.get(k, [])
            print(f" - {k}: {len(items)} items")
            if items:
                print(f"   Sample item: {items[0]}")
    else:
        print("Key 'assign_data' not found in dashboard_store")
except Exception as e:
    print(f"Error querying dashboard_store: {e}")
