import os
import json
import gzip
import base64
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: Supabase credentials not found in .env")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    res = supabase.table("dashboard_store").select("value").eq("key", "granular_assignments_se_umum_7210").execute()
    if res.data:
        val = res.data[0]["value"]
        comp = val.get("compressed_data")
        if comp:
            raw = json.loads(gzip.decompress(base64.b64decode(comp)).decode('utf-8'))
            print("Successfully fetched granular_assignments_se_umum_7210 from Supabase!")
            print("Total targets in DB:", len(raw.get("targets", [])))
            print("Updated at in DB:", val.get("updated_at"))
        else:
            print("compressed_data not found in database value.")
    else:
        print("Key 'granular_assignments_se_umum_7210' not found in DB.")
except Exception as e:
    print("Error:", e)
