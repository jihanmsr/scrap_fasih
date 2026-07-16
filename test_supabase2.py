import json, os, httpx

with open('.env', 'r') as f:
    for line in f:
        if line.startswith('SUPABASE_URL='):
            supabase_url = line.strip().split('=', 1)[1]
        if line.startswith('SUPABASE_KEY='):
            supabase_key = line.strip().split('=', 1)[1]

headers = {
    'apikey': supabase_key,
    'Authorization': f'Bearer {supabase_key}'
}

url = f'{supabase_url}/rest/v1/dashboard_store?select=value&key=eq.assign_data'
response = httpx.get(url, headers=headers)
data = response.json()
if not data:
    print("NO DATA IN SUPABASE FOR assign_data")
else:
    val = data[0]['value']
    print("Type of assign_data value:", type(val))
    if isinstance(val, str):
        print("Starts with:", val[:100])
