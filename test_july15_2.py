import json, os, httpx

with open('.env', 'r') as f:
    for line in f:
        if line.startswith('SUPABASE_URL='):
            supabase_url = line.strip().split('=', 1)[1]
        if line.startswith('SUPABASE_KEY='):
            supabase_key = line.strip().split('=', 1)[1]

url = f'{supabase_url}/rest/v1/dashboard_store?select=value&key=eq.ipas_data:2026-07-15'
headers = {
    'apikey': supabase_key,
    'Authorization': f'Bearer {supabase_key}'
}
response = httpx.get(url, headers=headers)
data = response.json()
yest = data[0]['value']
if isinstance(yest, str): yest = json.loads(yest)

with open('ipas_data.js', 'r') as f:
    content = f.read()
    start = content.find('{')
    end = content.rfind('}') + 1
    today_data = json.loads(content[start:end])

total_yest = sum(k['total_submitted'] for k in yest['se_umum'])
total_today = sum(k['total_submitted'] for k in today_data['se_umum'])
print(f"YEST SUBMIT: {total_yest}")
print(f"TODAY SUBMIT: {total_today}")
