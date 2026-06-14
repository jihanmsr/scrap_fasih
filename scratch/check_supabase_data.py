import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("Supabase configuration missing in .env")
    exit()

supabase = create_client(url, key)

res = supabase.table("email_logs").select("*").execute()
data = res.data
print("Total records in Supabase:", len(data))

if data:
    print("Available columns:", list(data[0].keys()))

unique_codes = {r["code"] for r in data}
print("Unique company codes in Supabase:", len(unique_codes))

# Check for Banggai Laut
banggai_laut_records = [r for r in data if "banggai laut" in str(r.get("kab_name")).lower() or "banggai laut" in str(r.get("kabupaten")).lower() or "banggai laut" in str(r.get("company_name")).lower()]
print("Banggai Laut records count in Supabase:", len(banggai_laut_records))
if banggai_laut_records:
    print("Banggai Laut sample records:")
    for r in banggai_laut_records[:5]:
         print(r)
else:
    print("No Banggai Laut records found in Supabase.")
