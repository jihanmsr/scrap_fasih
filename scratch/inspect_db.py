import os
import json
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: Supabase credentials not found in .env")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("Connected to Supabase. Querying tables...")

# Let's inspect dashboard_store keys
try:
    res = supabase.table("dashboard_store").select("key").execute()
    keys = [r["key"] for r in res.data]
    print("Found keys in dashboard_store:")
    for k in sorted(keys)[:30]:
        print(f" - {k}")
    if len(keys) > 30:
        print(f" ... and {len(keys) - 30} more keys")
except Exception as e:
    print(f"Error querying dashboard_store: {e}")

# Let's try to query database schema metadata if possible
try:
    # Just running a simple RPC or custom query if allowed, or we can check what tables exist by querying them.
    # Let's see if we can query common table names
    test_tables = ["email_logs", "dashboard_store", "granular_assignments", "assignments", "petugas", "daily_stats"]
    for table in test_tables:
        try:
            res = supabase.table(table).select("*").limit(1).execute()
            print(f"Table '{table}' exists! Schema sample: {list(res.data[0].keys()) if res.data else 'Empty table'}")
        except Exception as e:
            print(f"Table '{table}' does not exist or error: {str(e)[:100]}")
except Exception as e:
    print(f"Error inspecting schemas: {e}")
