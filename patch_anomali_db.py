import json
import gzip
import base64
import os
import ssl
import urllib.request

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# 1. Build lookup from granular data and users.js (via update_users_js.py logic, but we'll just read users.js)
print("Building lookup from granular data...")
granular_files = [f for f in os.listdir('.') if f.startswith('granular_assignments_se_umum_') and f.endswith('.json')]

lookup = {}
for fname in granular_files:
    with open(fname) as f:
        d = json.load(f)
    raw = gzip.decompress(base64.b64decode(d['compressed_data']))
    data = json.loads(raw)
    targets = data.get('targets', [])
    for t in targets:
        if isinstance(t, list) and len(t) >= 9:
            nama_usaha = t[2]
            petugas_email = t[8]
            lookup[t[0]] = {'nama_usaha': nama_usaha, 'petugas_email': petugas_email}

# Load user map from users.js
user_map = {}
try:
    with open('users.js') as f:
        content = f.read()
        json_str = content.split('=', 1)[1].strip().rstrip(';')
        user_map = json.loads(json_str)
except Exception as e:
    print("Error loading users.js", e)

print(f"Loaded {len(lookup)} assignments into lookup map.")

# 2. Fetch all anomalies from API
print("Fetching anomalies from API...")
url_get = 'https://dds-api.bpssulteng.id/api.php?action=get_anomali'
req = urllib.request.Request(url_get, headers={'Host': 'dds-api.bpssulteng.id'})
with urllib.request.urlopen(req, context=ctx) as response:
    anomalies = json.loads(response.read().decode())

# 3. Patch anomalies
to_update = []
for a in anomalies:
    aid = a.get('assignment_id', '')
    nama_krt = a.get('nama_krt', '')
    nama_petugas = a.get('nama_petugas', '')
    
    needs_update = False
    payload = {'id': a['id']}
    
    if aid in lookup:
        target_info = lookup[aid]
        
        # Check nama_krt
        if (len(nama_krt) == 36 and '-' in nama_krt) or not nama_krt or nama_krt == '-':
            if target_info['nama_usaha']:
                payload['nama_krt'] = target_info['nama_usaha']
                needs_update = True
                
        # Check nama_petugas
        if not nama_petugas or nama_petugas == '-':
            email = str(target_info.get('petugas_email', ''))
            uname = email.split('@')[0] if email else ''
            p_name = user_map.get(uname, email)
            if p_name:
                payload['nama_petugas'] = p_name
                needs_update = True
                
    if needs_update:
        to_update.append(payload)

print(f"Found {len(to_update)} anomalies to patch.")

from concurrent.futures import ThreadPoolExecutor

url_patch = 'https://dds-api.bpssulteng.id/api.php'

def patch_one(u):
    u['action'] = 'patch_anomali_db'
    data = json.dumps(u).encode('utf-8')
    req = urllib.request.Request(url_patch, data=data, headers={'Host': 'dds-api.bpssulteng.id', 'Content-Type': 'application/json'})
    try:
        urllib.request.urlopen(req, context=ctx)
        return True
    except Exception as e:
        print("Error updating id", u['id'], e)
        return False

print(f"Starting threads to patch {len(to_update)} anomalies...")
success = 0
with ThreadPoolExecutor(max_workers=50) as executor:
    results = executor.map(patch_one, to_update)
    for r in results:
        if r:
            success += 1

print(f"Patched {success}/{len(to_update)} anomalies.")
