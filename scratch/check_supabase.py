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

# Fetch all records
res = supabase.table("email_logs").select("*").execute()
data = res.data

print(f"Total rows in Supabase: {len(data)}")

# Count unique codes
unique_codes = set(r.get("code") for r in data if r.get("code") != "-")
print(f"Total unique companies in Supabase: {len(unique_codes)}")

# Check if survey_status column exists and its distribution
statuses = {}
for r in data:
    status = r.get("survey_status", "COLUMN_MISSING")
    statuses[status] = statuses.get(status, 0) + 1

print("\n=== SEBARAN STATUS DI SUPABASE ===")
for status, count in statuses.items():
    print(f"{status}: {count}")
