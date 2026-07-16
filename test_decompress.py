import json, os, httpx, zlib, base64

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
compressed_b64 = val['compressed_data']
compressed_bytes = base64.b64decode(compressed_b64)
decompressed_bytes = zlib.decompress(compressed_bytes, 16 + zlib.MAX_WBITS)
decompressed_json = json.loads(decompressed_bytes.decode('utf-8'))
print("Keys in decompressed:", decompressed_json.keys())
print("Length of assign_sls_data_umum:", len(decompressed_json.get('assign_sls_data_umum', [])))
