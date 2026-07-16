import json, os, httpx

with open('.env', 'r') as f:
    for line in f:
        if line.startswith('SUPABASE_URL='):
            supabase_url = line.strip().split('=', 1)[1]
        if line.startswith('SUPABASE_KEY='):
            supabase_key = line.strip().split('=', 1)[1]

url = f'{supabase_url}/rest/v1/dashboard_store?select=value&key=eq.ipas_data:2026-07-16'
headers = {
    'apikey': supabase_key,
    'Authorization': f'Bearer {supabase_key}'
}
response = httpx.get(url, headers=headers)
data = response.json()
if not data:
    print("NO DATA IN SUPABASE FOR 2026-07-16")
else:
    print("DATA EXISTS in SUPABASE, length:", len(str(data[0]['value'])))

url2 = f'{supabase_url}/rest/v1/dashboard_store?select=value&key=eq.ipas_data'
response2 = httpx.get(url2, headers=headers)
data2 = response2.json()
if not data2:
    print("NO DATA IN SUPABASE FOR ipas_data")
else:
    print("DATA EXISTS in SUPABASE ipas_data, length:", len(str(data2[0]['value'])))

