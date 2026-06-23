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
print("Connected. Fetching daily_submission_stats...")

try:
    res = supabase.table("dashboard_store").select("value").eq("key", "daily_submission_stats").execute()
    if res.data:
        val = res.data[0].get("value")
        print(f"Total rows in daily_submission_stats: {len(val) if val else 0}")
        
        # Calculate sum for 2026-06-22
        sum_today = 0
        sum_se_umum = 0
        sum_se_ub = 0
        details = []
        for row in val:
            if row.get("date") == "2026-06-22":
                cnt = row.get("count", 0)
                sum_today += cnt
                if row.get("survey_type") == "se_umum":
                    sum_se_umum += cnt
                else:
                    sum_se_ub += cnt
                details.append(row)
                
        print(f"Total count for 2026-06-22: {sum_today}")
        print(f"  se_umum: {sum_se_umum}")
        print(f"  se_ub: {sum_se_ub}")
        print("Details:")
        for r in sorted(details, key=lambda x: x.get("count", 0), reverse=True):
            print(f"  Kab: {r.get('kab_name')}, Type: {r.get('survey_type')}, Count: {r.get('count')}")
    else:
        print("Key daily_submission_stats not found or empty.")
except Exception as e:
    print(f"Error: {e}")
