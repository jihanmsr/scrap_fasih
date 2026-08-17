import json
import re
from datetime import datetime, timedelta

with open("daily_summary.js", "r", encoding="utf-8") as f:
    content = f.read()
match = re.search(r'window\.DAILY_SUMMARY\s*=\s*(\[.*?\]);', content, re.DOTALL)
if not match:
    print("Could not parse daily_summary.js")
    exit(1)
daily_summary = json.loads(match.group(1))

with open("ipas_data.js", "r", encoding="utf-8") as f:
    ipas_content = f.read()
match = re.search(r'window\.IPAS_DATA\s*=\s*(\{.*?\});', ipas_content, re.DOTALL)
if not match:
    print("Could not parse ipas_data.js")
    exit(1)
ipas_data = json.loads(match.group(1))

today = datetime.now()
h0_date_str = today.strftime("%Y-%m-%d")
h1_date_str = (today - timedelta(days=1)).strftime("%Y-%m-%d")
h2_date_str = (today - timedelta(days=2)).strftime("%Y-%m-%d")

daily_map = {}
for row in daily_summary:
    tgl = row.get("tanggal")
    kab = str(row.get("kabupaten", "")).upper()
    if kab not in daily_map:
        daily_map[kab] = {}
    daily_map[kab][tgl] = row.get("total_submitted", 0)

def get_sub(kab_name, date_str):
    if kab_name in daily_map:
        # daily_summary contains absolute delta per day
        return daily_map[kab_name].get(date_str, 0)
    return 0

for survey_type in ["se_umum", "se_ub"]:
    if survey_type in ipas_data:
        for kab in ipas_data[survey_type]:
            kab_name = kab.get("kabupaten", "")
            kab_clean = re.sub(r'\[\d+\]', '', kab_name).strip().upper()
            
            sub_h0 = get_sub(kab_clean, h0_date_str)
            sub_h1 = get_sub(kab_clean, h1_date_str)
            sub_h2 = get_sub(kab_clean, h2_date_str)
            
            prelist = kab.get("total_prelist", 0)
            
            if prelist > 0:
                kab["delta_persen"] = round((sub_h0 / prelist) * 100, 2)
                kab["delta_kemarin_persen"] = round((sub_h1 / prelist) * 100, 2)
                kab["delta_lusa_persen"] = round((sub_h2 / prelist) * 100, 2)
            else:
                kab["delta_persen"] = 0.0
                kab["delta_kemarin_persen"] = 0.0
                kab["delta_lusa_persen"] = 0.0
                
            kab["new_usaha_today"] = 0
            kab["new_rumah_today"] = 0
            kab["new_usaha_yesterday"] = 0
            kab["new_rumah_yesterday"] = 0
            if "new_usaha_overall" not in kab: kab["new_usaha_overall"] = 0
            if "new_rumah_overall" not in kab: kab["new_rumah_overall"] = 0
            
            for kec in kab.get("kecamatan_list", []):
                kec["delta_persen"] = 0.0
                kec["delta_kemarin_persen"] = 0.0
                kec["delta_lusa_persen"] = 0.0
                kec["new_usaha_today"] = 0
                kec["new_rumah_today"] = 0
                if "new_usaha" not in kec: kec["new_usaha"] = 0
                if "new_rumah" not in kec: kec["new_rumah"] = 0

new_json = json.dumps(ipas_data, indent=2, ensure_ascii=False)
new_content = ipas_content[:match.start(1)] + new_json + ipas_content[match.end(1):]

with open("ipas_data.js", "w", encoding="utf-8") as f:
    f.write(new_content)

print("Berhasil memperbaiki perhitungan DELTA KINERJA (%) menggunakan nilai absolut harian!")
