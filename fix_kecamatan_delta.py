import json, os, datetime
from supabase import create_client

def load_env():
    env = {}
    with open('.env') as f:
        for line in f:
            if '=' in line:
                k, v = line.strip().split('=', 1)
                env[k] = v
    return env

env = load_env()
supabase = create_client(env["SUPABASE_URL"], env["SUPABASE_KEY"])

def get_snapshot(date_str):
    res = supabase.table("dashboard_store").select("value").eq("key", f"ipas_data:{date_str}").execute()
    if res.data:
        val = res.data[0]['value']
        if isinstance(val, str): val = json.loads(val)
        return val
    return None

today = datetime.date.today()
yesterday = today - datetime.timedelta(days=1)
lusa = today - datetime.timedelta(days=2)

snap_yest = get_snapshot(yesterday.strftime("%Y-%m-%d"))
snap_lusa = get_snapshot(lusa.strftime("%Y-%m-%d"))

def get_kec_submitted(snap, survey_type, kab_name, kec_name):
    if not snap: return 0
    for kab in snap.get(survey_type, []):
        if kab['kabupaten'] == kab_name:
            for kec in kab.get('kecamatan_list', []):
                if kec['kecamatan'] == kec_name:
                    return kec.get('total_submitted', 0)
    return 0

with open('ipas_data.js', 'r') as f:
    content = f.read().replace('window.IPAS_DATA = ', '').strip()
    if content.endswith(';'): content = content[:-1]
    current_data = json.loads(content)

for survey_type in ['se_umum', 'se_ub']:
    for kab in current_data.get(survey_type, []):
        for kec in kab.get('kecamatan_list', []):
            kab_name = kab['kabupaten']
            kec_name = kec['kecamatan']
            
            sub_today = kec.get('total_submitted', 0)
            sub_yest = get_kec_submitted(snap_yest, survey_type, kab_name, kec_name)
            sub_lusa = get_kec_submitted(snap_lusa, survey_type, kab_name, kec_name)
            
            if sub_yest > 0:
                kec['today_completed'] = max(0, sub_today - sub_yest)
            if sub_lusa > 0:
                kec['yesterday_completed'] = max(0, sub_yest - sub_lusa)
            
            # Recalculate percentages
            k_total = kec.get('total_prelist', 0)
            if k_total > 0:
                kec['delta_persen'] = round((kec.get('today_completed', 0) / k_total) * 100, 2)
                kec['delta_kemarin_persen'] = round((kec.get('yesterday_completed', 0) / k_total) * 100, 2)
                kec['delta_lusa_persen'] = 0 # No data for H-3 to calculate lusa delta
            else:
                kec['delta_persen'] = 0.0
                kec['delta_kemarin_persen'] = 0.0
                kec['delta_lusa_persen'] = 0.0

with open('ipas_data.js', 'w') as f:
    f.write('window.IPAS_DATA = ' + json.dumps(current_data, indent=2) + ';')

print("Fixed ipas_data.js successfully!")
