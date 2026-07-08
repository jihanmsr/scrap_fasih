import urllib.request
import json

kab_codes = ['7201', '7202', '7203', '7204', '7205', '7206', '7207', '7208', '7209', '7210', '7211', '7212', '7271']
all_data = {}

for kab in kab_codes:
    print(f"Fetching {kab}...")
    try:
        url = f"https://dds-api.bpssulteng.id/api.php?action=get_petugas_summary&survey=se_umum&kab={kab}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            all_data[kab] = data
    except Exception as e:
        print(f"Error fetching {kab}: {e}")

with open('/Users/jihanmaisaroh/scrap_fasih/mysql_data.js', 'w') as f:
    f.write(f"window.MYSQL_DATA_STATIC = {json.dumps(all_data)};\n")
print("Done!")
