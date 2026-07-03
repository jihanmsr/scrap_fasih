import os
import json
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
res = supabase.table("dashboard_store").select("key").execute()
keys = [r["key"] for r in res.data if "daily_submission_stats" in r["key"]]
print("All keys containing 'daily_submission_stats':")
for k in sorted(keys):
    res_val = supabase.table("dashboard_store").select("value").eq("key", k).execute()
    if res_val.data:
        val = res_val.data[0]["value"]
        if isinstance(val, list):
            print(f" - {k}: length {len(val)}")
        else:
            print(f" - {k}: not a list, type {type(val)}")
    else:
        print(f" - {k}: no data")
