import json
import os
import requests

LOCAL_API_URL = os.getenv("LOCAL_API_URL", "https://dds-api.bpssulteng.id/api.php")

def post_to_api(action, json_data):
    url = "https://103.5.51.154/api.php"
    headers = {"Host": "dds-api.bpssulteng.id"}
    return requests.post(f"{url}?action={action}", json=json_data, headers=headers, verify=False)

def main():
    print("Loading hasil_pegawai.json...")
    try:
        with open('hasil_pegawai.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading JSON: {e}")
        return

    users_to_seed = []
    for row in data:
        username = str(row.get('username') or '').strip()
        # Fallback to niplama if no username
        if not username:
            username = str(row.get('niplama') or '').strip()
        if not username:
            continue
            
        full_name = str(row.get('nama') or '').strip()
        role = str(row.get('jabatan') or 'petugas').strip()
        
        # User requested password to be the same as username
        password = username
        
        users_to_seed.append({
            'username': username,
            'password': password,
            'full_name': full_name,
            'role': role
        })
        
    print(f"Found {len(users_to_seed)} valid users to seed.")
    
    # Process in batches to avoid huge payloads
    batch_size = 500
    for i in range(0, len(users_to_seed), batch_size):
        batch = users_to_seed[i:i+batch_size]
        res = post_to_api('seed_users', batch)
        print(f"Batch {i//batch_size + 1}: Status {res.status_code}")
        try:
            print(f"Response: {res.json()}")
        except:
            print(f"Response text: {res.text}")

if __name__ == "__main__":
    main()
