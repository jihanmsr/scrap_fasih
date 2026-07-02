import json

with open('hasil_pegawai.json', 'r') as f:
    users = json.load(f)

user_map = {}
for u in users:
    username = u.get('username')
    full_name = u.get('nama')
    if username and full_name:
        user_map[username] = full_name

with open('users.js', 'w') as f:
    f.write('window.STATIC_USER_MAP = ')
    json.dump(user_map, f, separators=(',', ':'))
    f.write(';\n')
print("users.js created.")
