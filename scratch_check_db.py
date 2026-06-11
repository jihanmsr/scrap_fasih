import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
if not url or not key:
    print("Supabase credentials missing.")
    exit(1)

supabase = create_client(url, key)
try:
    # Query database metadata using a simple select
    res = supabase.table("email_logs").select("*").limit(1).execute()
    print("Connected to Supabase. Table email_logs exists.")
    
    # Try reading from a hypothetical dashboard_store table
    try:
        res2 = supabase.table("dashboard_store").select("*").limit(1).execute()
        print("Table dashboard_store exists.")
    except Exception as e:
        print("Table dashboard_store does not exist yet.", str(e))
except Exception as e:
    print("Error:", e)
