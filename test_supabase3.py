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
val = response.json()[0]['value']
print("Keys in assign_data:", val.keys())
print("Length of assign_sls_data_umum:", len(val.get('assign_sls_data_umum', [])))
