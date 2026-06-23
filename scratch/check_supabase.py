import os
import json
import sys
from dotenv import load_dotenv

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from merge_granulars import load_supabase_config

def main():
    print("Connecting to Supabase...")
    supabase = load_supabase_config()
    print("Fetching keys from dashboard_store...")
    res = supabase.table("dashboard_store").select("key, updated_at").execute()
    print(f"Found {len(res.data)} rows:")
    for row in res.data:
        print(f"  Key: {row['key']}, Updated At: {row.get('updated_at')}")

if __name__ == "__main__":
    main()
