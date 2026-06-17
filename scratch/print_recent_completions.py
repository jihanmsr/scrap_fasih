import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
for key in ["ipas_data:2026-06-17", "ipas_data:2026-06-18"]:
    res = supabase.table("dashboard_store").select("value").eq("key", key).execute()
    if res.data:
        val = res.data[0].get("value", {})
        print(f"\n================ KEY: {key} (UPDATED: {val.get('updated_at')}) ================")
        se_umum = val.get("se_umum", [])
        for kab in se_umum[:3]:
            print(f"Kab: {kab.get('kabupaten')}")
            print(f"  today_completed: {kab.get('today_completed')}")
            print(f"  yesterday_completed: {kab.get('yesterday_completed')}")
            print(f"  two_days_ago_completed: {kab.get('two_days_ago_completed')}")
    else:
        print(f"Key {key} not found.")
