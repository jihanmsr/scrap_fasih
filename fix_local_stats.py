import requests
import json

doh_url = "https://cloudflare-dns.com/dns-query?name=pnzfjkweiypmzdribxjk.supabase.co&type=A"
try:
    doh_res = requests.get(doh_url, headers={"accept": "application/dns-json"}).json()
    ip_address = doh_res['Answer'][0]['data']
except Exception as e:
    doh_url = "https://dns.google/resolve?name=pnzfjkweiypmzdribxjk.supabase.co&type=A"
    doh_res = requests.get(doh_url).json()
    ip_address = doh_res['Answer'][0]['data']

from dotenv import load_dotenv
import os
load_dotenv()
key = os.getenv("SUPABASE_KEY")

headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json",
    "Host": "pnzfjkweiypmzdribxjk.supabase.co"
}

rest_url = f"https://{ip_address}/rest/v1/dashboard_store?key=eq.daily_submission_stats&select=value"
res = requests.get(rest_url, headers=headers, verify=False)
data = res.json()[0]['value']

with open("daily_submission_stats.js", "w") as f:
    f.write(f"window.DAILY_SUBMISSION_STATS = {json.dumps(data, indent=2)};\n")

print("Fixed daily_submission_stats.js")
