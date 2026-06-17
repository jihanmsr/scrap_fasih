import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: SUPABASE_URL or SUPABASE_KEY not in .env")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
print("Connected. Querying dashboard_store keys...")

try:
    res = supabase.table("dashboard_store").select("key, updated_at").execute()
    print("Keys in dashboard_store:")
    for row in res.data:
        print(f"Key: {row.get('key')}, Updated At: {row.get('updated_at')}")
except Exception as e:
    print(f"Error: {e}")
