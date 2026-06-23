import os
import json
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
res = supabase.table("dashboard_store").select("value").eq("key", "ipas_data").execute()
if res.data:
    val = res.data[0].get("value", {})
    print(f"Updated At: {val.get('updated_at')}")
    se_umum = val.get("se_umum", [])
    total_today = 0
    print("Se Umum Today Completed from ipas_data:")
    for kab in se_umum:
        today_cnt = kab.get("today_completed", 0)
        total_today += today_cnt
        print(f"  {kab.get('kabupaten')}: {today_cnt}")
        print(f"    breakdown: {kab.get('today_completed_breakdown')}")
    print(f"Total today_completed from ipas_data: {total_today}")
else:
    print("ipas_data key not found.")
