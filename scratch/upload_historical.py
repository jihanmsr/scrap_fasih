import os
import csv
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"))
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: SUPABASE_URL or SUPABASE_KEY not found in .env file!")
    exit(1)

if SUPABASE_URL.endswith("/rest/v1/"):
    SUPABASE_URL = SUPABASE_URL[:-9]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
csv_path = "all_email_history.csv"

if not os.path.exists(csv_path):
    print(f"Error: {csv_path} not found!")
    exit(1)

print("Reading CSV data...")
all_records = []
with open(csv_path, mode="r", encoding="utf-8") as f:
    reader = csv.reader(f)
    header = next(reader, None)
    for row in reader:
        if len(row) >= 8:
            all_records.append({
                "code": row[0],
                "company_name": row[1],
                "email": row[3],
                "global_status": row[4],
                "status": row[5],
                "timestamp": row[6],
                "order": int(row[7]) if row[7].isdigit() else 0
            })

print(f"Read {len(all_records)} history logs. Uploading to Supabase...")

# Delete old records
supabase.table("email_logs").delete().neq("code", "FORCE_DELETE_ALL_XYZ").execute()

# Batch insert in chunks of 500
chunk_size = 500
for i in range(0, len(all_records), chunk_size):
    chunk = all_records[i:i + chunk_size]
    supabase.table("email_logs").insert(chunk).execute()
    print(f"Uploaded chunk {i//chunk_size + 1} ({len(chunk)} records)")

print("Success! All historical data uploaded to Supabase.")
