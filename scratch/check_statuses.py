import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Fetch all using pagination loop
all_data = []
offset = 0
limit = 1000
while True:
    res = supabase.table("email_logs").select("*").range(offset, offset + limit - 1).execute()
    if not res.data:
        break
    all_data.extend(res.data)
    offset += limit

# Group by company code
grouped = {}
for r in all_data:
    code = r.get("code")
    if not code:
        continue
    if code not in grouped:
        grouped[code] = {
            "code": code,
            "global_status": r.get("global_status"),
            "history": []
        }
    grouped[code]["history"].append(r)

# Count unique company global_statuses
counts = {}
for code, comp in grouped.items():
    status = comp["global_status"] or "-"
    status = status.lower().strip()
    counts[status] = counts.get(status, 0) + 1

print(f"Total unique companies grouped: {len(grouped)}")
print("Unique company global_status distribution:")
for status, count in counts.items():
    print(f"  {status}: {count}")
