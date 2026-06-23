import os
import json
import re
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: SUPABASE_URL atau SUPABASE_KEY tidak ditemukan di .env!")
    exit(1)

script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
ipas_path = os.path.join(parent_dir, "ipas_data.js")

if not os.path.exists(ipas_path):
    print(f"Error: {ipas_path} tidak ditemukan!")
    exit(1)

with open(ipas_path, "r", encoding="utf-8") as f:
    content = f.read()

# Extract JSON
json_match = re.search(r"window\.IPAS_DATA\s*=\s*(\{.*?\});", content, re.DOTALL)
if not json_match:
    print("Error: Gagal mengekstrak JSON dari ipas_data.js!")
    exit(1)

ipas_obj = json.loads(json_match.group(1))

print("Menghubungkan ke Supabase...")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("Mengunggah ipas_data ke Supabase...")
supabase.table("dashboard_store").delete().eq("key", "ipas_data").execute()
supabase.table("dashboard_store").insert({"key": "ipas_data", "value": ipas_obj}).execute()

# Also upload daily key
import datetime
today_str = datetime.datetime.now().strftime("%Y-%m-%d")
daily_key = f"ipas_data:{today_str}"
supabase.table("dashboard_store").delete().eq("key", daily_key).execute()
supabase.table("dashboard_store").insert({"key": daily_key, "value": ipas_obj}).execute()

print("✅ Berhasil menyelaraskan ipas_data dari lokal ke Supabase!")
