import os
import json
import base64
import gzip
import requests

doh_url = "https://dns.google/resolve?name=pnzfjkweiypmzdribxjk.supabase.co&type=A"
doh_res = requests.get(doh_url).json()
ip_address = doh_res['Answer'][0]['data']

from dotenv import load_dotenv
load_dotenv()
key = os.getenv("SUPABASE_KEY")

headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json",
    "Host": "pnzfjkweiypmzdribxjk.supabase.co"
}

rest_url = f"https://{ip_address}/rest/v1/dashboard_store?key=eq.assign_data_fast&select=value"
res = requests.get(rest_url, headers=headers, verify=False)
val = res.json()[0]['value']
compressed_bytes = base64.b64decode(val['compressed_data'])
raw_str = gzip.decompress(compressed_bytes).decode('utf-8')
assign_payload = json.loads(raw_str)

for kab in assign_payload.get('assign_data_umum', []):
    print(f"{kab['nama_kab']}: {kab['total']}")

print("SLS Data sample for Morowali:")
sls_morowali = [s for s in assign_payload.get('assign_sls_data_umum', []) if 'MOROWALI' in s[4]]
print(len(sls_morowali))
