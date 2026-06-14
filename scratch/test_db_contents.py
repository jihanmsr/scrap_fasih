import os
from dotenv import load_dotenv
from supabase import create_client
import json

load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

res = supabase.table("email_logs").select("*").limit(5).execute()
print(json.dumps(res.data, indent=2))
