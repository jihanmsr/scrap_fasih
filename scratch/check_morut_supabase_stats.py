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
print("Connected. Fetching daily_submission_stats from Supabase...")

try:
    res = supabase.table("dashboard_store").select("value").eq("key", "daily_submission_stats").execute()
    if res.data:
        val = res.data[0].get("value")
        print(f"Total rows: {len(val)}")
        morut_records = [r for r in val if "MOROWALI UTARA" in str(r.get("kab_name")).upper()]
        print(f"Morowali Utara records count: {len(morut_records)}")
        for r in sorted(morut_records, key=lambda x: x.get("date", "")):
            print(f"Date: {r.get('date')} | Count: {r.get('count')} | Survey: {r.get('survey_type')}")
    else:
        print("Not found")
except Exception as e:
    print(f"Error: {e}")
