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

try:
    response = httpx.get(url, headers=headers)
    data = response.json()
    
    if not data:
        print("No data for 2026-07-15 in Supabase")
    else:
        yest_data = data[0]['value']
        if isinstance(yest_data, str):
            yest_data = json.loads(yest_data)
        
        with open('ipas_data.js', 'r') as f:
            content = f.read()
            start = content.find('{')
            today_data = json.loads(content[start:])
            
        for s_type in ['se_umum', 'se_ub']:
            for t_kab in today_data.get(s_type, []):
                y_kab = next((k for k in yest_data.get(s_type, []) if k['kabupaten'] == t_kab['kabupaten']), None)
                if y_kab:
                    t_kab['new_usaha_today'] = t_kab.get('new_usaha_overall', 0) - y_kab.get('new_usaha_overall', 0)
                    t_kab['new_rumah_today'] = t_kab.get('new_rumah_overall', 0) - y_kab.get('new_rumah_overall', 0)
                    t_kab['today_completed'] = max(0, t_kab.get('total_submitted', 0) - y_kab.get('total_submitted', 0))
                    
                    for t_kec in t_kab.get('kecamatan_list', []):
                        y_kec = next((k for k in y_kab.get('kecamatan_list', []) if k['kecamatan'] == t_kec['kecamatan']), None)
                        if y_kec:
                            t_kec['new_usaha_today'] = t_kec.get('new_usaha_overall', 0) - y_kec.get('new_usaha_overall', 0)
                            t_kec['new_rumah_today'] = t_kec.get('new_rumah_overall', 0) - y_kec.get('new_rumah_overall', 0)
                            t_kec['today_completed'] = max(0, t_kec.get('total_submitted', 0) - y_kec.get('total_submitted', 0))
                            
        with open('ipas_data.js', 'w') as f:
            f.write("window.IPAS_DATA = " + json.dumps(today_data, indent=2) + ";\n")
        
        json_str = json.dumps(today_data)
        for key in ["ipas_data", "ipas_data:2026-07-16"]:
            post_url = f"{supabase_url}/rest/v1/dashboard_store?key=eq.{key}"
            httpx.patch(post_url, headers={**headers, "Content-Type": "application/json"}, json={"value": json_str})
            
        print("Fixed ipas_data.js and updated Supabase!")
except Exception as e:
    import traceback
    traceback.print_exc()
