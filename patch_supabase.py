import os
import json
import base64
import gzip
import pandas as pd
import requests

# Resolve Supabase domain using Google DoH to bypass ISP DNS block
doh_url = "https://dns.google/resolve?name=pnzfjkweiypmzdribxjk.supabase.co&type=A"
print("Bypassing ISP DNS block via Google DoH...")
try:
    doh_res = requests.get(doh_url).json()
    ip_address = doh_res['Answer'][0]['data']
    print(f"Resolved Supabase IP: {ip_address}")
except Exception as e:
    print(f"Failed to resolve via DoH: {e}")
    exit(1)

from dotenv import load_dotenv
load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json",
    "Host": "pnzfjkweiypmzdribxjk.supabase.co"
}

# Fetch data using direct IP
print("Fetching assign_data_fast from Supabase...")
rest_url = f"https://{ip_address}/rest/v1/dashboard_store?key=eq.assign_data_fast&select=value"
res = requests.get(rest_url, headers=headers, verify=False)
if res.status_code != 200 or not res.json():
    print(f"Failed to fetch data: {res.status_code} {res.text}")
    exit(1)

val = res.json()[0]['value']
print("Decompressing data...")
compressed_bytes = base64.b64decode(val['compressed_data'])
raw_str = gzip.decompress(compressed_bytes).decode('utf-8')
assign_payload = json.loads(raw_str)
petugas_umum = assign_payload.get("petugas_data_umum", [])

print("Loading Excel data...")
import glob
excel_file = max(glob.glob('Rekap Progress Petugas*.xlsx'))
df = pd.read_excel(excel_file)
df_p = df[df['pencacah_email'].notna() & (df['pencacah_email'] != '')]

excel_petugas_regions = {}
for _, row in df_p.iterrows():
    email = str(row['pencacah_email']).strip()
    if email not in excel_petugas_regions:
        excel_petugas_regions[email] = []
    reg_code = str(row['level_5_full_code']).replace(".0", "")
    if not any(r['regionCode'] == reg_code for r in excel_petugas_regions[email]):
        excel_petugas_regions[email].append({"regionCode": reg_code, "regionName": "-"})

existing_emails = {p.get('email', p.get('username')) for p in petugas_umum}
added_count = 0
for email, regions in excel_petugas_regions.items():
    if email not in existing_emails:
        petugas_umum.append({
            "username": email,
            "email": email,
            "fullname": "-",
            "roleName": "Pencacah",
            "regions": regions,
            "totalRegions": len(regions)
        })
        added_count += 1

print(f"Added {added_count} missing enumerators to petugas_data_umum!")

if added_count > 0:
    print("Compressing and updating Supabase...")
    assign_payload["petugas_data_umum"] = petugas_umum
    new_raw_str = json.dumps(assign_payload, ensure_ascii=False)
    new_compressed_str = base64.b64encode(gzip.compress(new_raw_str.encode('utf-8'))).decode('utf-8')
    
    new_db_payload = {
        "is_compressed": True,
        "compressed_data": new_compressed_str
    }
    
    patch_url = f"https://{ip_address}/rest/v1/dashboard_store?key=eq.assign_data_fast"
    res_patch = requests.patch(patch_url, headers=headers, json={"value": new_db_payload}, verify=False)
    
    if res_patch.status_code in [200, 204]:
        print("Supabase updated successfully!")
    else:
        print(f"Failed to update Supabase: {res_patch.status_code} {res_patch.text}")
else:
    print("No missing enumerators to add.")

