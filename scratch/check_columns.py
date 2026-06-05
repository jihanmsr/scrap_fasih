import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Supabase config not found!")
    exit()

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
res = supabase.table("email_logs").select("*").limit(5).execute()
print("First 5 records from Supabase:")
import json
print(json.dumps(res.data, indent=2))
