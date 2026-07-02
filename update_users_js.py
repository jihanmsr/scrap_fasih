import json, os, gzip, base64

user_map = {}
try:
    with open('hasil_pegawai.json') as f:
        pegawai = json.load(f)
        for p in pegawai:
            uname = p.get('username')
            if uname:
                user_map[uname] = p.get('nama', uname)
except:
    pass

granular_files = [f for f in os.listdir('.') if f.startswith('granular_assignments_se_umum_') and f.endswith('.json')]
for fname in granular_files:
    try:
        with open(fname) as f:
            d = json.load(f)
        raw = gzip.decompress(base64.b64decode(d['compressed_data']))
        data = json.loads(raw)
        for p in data.get('petugas', []):
            if isinstance(p, list) and len(p) >= 2:
                email = p[0]
                name = p[1]
                if email and name and name != '-':
                    uname = email.split('@')[0]
                    if uname not in user_map:
                        user_map[uname] = name
    except Exception as e:
        print(f"Error parsing {fname}: {e}")

with open('users.js', 'w') as f:
    f.write(f"window.STATIC_USER_MAP = {json.dumps(user_map)};\n")
print(f"Updated users.js with {len(user_map)} users.")
