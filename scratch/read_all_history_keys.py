import os
import json
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: SUPABASE_URL or SUPABASE_KEY not in .env")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
print("Connected. Listing dashboard_store keys...")

try:
    res = supabase.table("dashboard_store").select("key").execute()
    keys = [r.get("key") for r in res.data]
    print(f"Total keys: {len(keys)}")
    daily_keys = [k for k in keys if "ipas_data" in k]
    print("IPAS data keys in DB:")
    for k in sorted(daily_keys):
        print(f" - {k}")
except Exception as e:
    print(f"Error: {e}")
