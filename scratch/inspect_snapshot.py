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

def inspect_key(key):
    print(f"\n--- Inspecting key: {key} ---")
    res = supabase.table("dashboard_store").select("value").eq("key", key).execute()
    if not res.data:
        print("No data found.")
        return
    val = res.data[0].get("value", {})
    updated_at = val.get("updated_at", "unknown")
    print(f"Data updated_at: {updated_at}")
    
    # Check general info
    for survey in ["se_umum", "se_ub"]:
        if survey in val:
            print(f"\nSurvey: {survey}")
            for kab in val[survey]:
                print(f"  Kabupaten: {kab.get('kabupaten')}")
                print(f"    total_submitted: {kab.get('total_submitted')}")
                print(f"    today_completed: {kab.get('today_completed')}")
                print(f"    yesterday_completed: {kab.get('yesterday_completed')}")
                print(f"    two_days_ago_completed: {kab.get('two_days_ago_completed')}")

inspect_key("ipas_data:2026-06-17")
inspect_key("ipas_data:2026-06-18")
