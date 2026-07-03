import os
import json
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: Supabase credentials not found")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
res = supabase.table("dashboard_store").select("value").eq("key", "daily_submission_stats").execute()

if res.data and res.data[0]["value"]:
    data = res.data[0]["value"]
    print(f"Fetched {len(data)} items of daily_submission_stats from Supabase.")
    
    script_dir = "/Users/jihanmaisaroh/scrap_fasih"
    json_path = os.path.join(script_dir, "daily_submission_stats.json")
    js_path = os.path.join(script_dir, "daily_submission_stats.js")
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    print(f"Saved {json_path}")
    
    with open(js_path, "w", encoding="utf-8") as f:
        f.write(f"window.DAILY_SUBMISSION_STATS = {json.dumps(data, indent=4)};\n")
    print(f"Saved {js_path}")
else:
    print("No daily_submission_stats data found in Supabase.")
