import json
import re
import pandas as pd
from datetime import datetime, timedelta

# Load existing ipas_data.js
with open("ipas_data.js", "r", encoding="utf-8") as f:
    ipas_content = f.read()
match = re.search(r'window\.IPAS_DATA\s*=\s*(\{.*?\});', ipas_content, re.DOTALL)
if not match:
    print("Could not parse ipas_data.js")
    exit(1)
ipas_data = json.loads(match.group(1))

# Load daily data specifically for each survey
df_umum = pd.read_csv('sqllab_tarik_dashboard_cdp_20260817T091824.csv')
df_ub = pd.read_csv('sqllab_tarik_dashboard_cdp_20260817T092442.csv')

kab_mapping = {
    7201: "BANGGAI KEPULAUAN", 7202: "BANGGAI", 7203: "MOROWALI",
    7204: "POSO", 7205: "DONGGALA", 7206: "TOLI-TOLI", 7207: "BUOL",
    7208: "PARIGI MOUTONG", 7209: "TOJO UNA-UNA", 7210: "SIGI",
    7211: "BANGGAI LAUT", 7212: "MOROWALI UTARA", 7271: "PALU"
}

def build_daily_map(df):
    m = {}
    for _, row in df.iterrows():
        tgl = str(row['tanggal']).strip()
        kab_code = int(row['kode_kabupaten'])
        kab_name = kab_mapping.get(kab_code, str(kab_code))
        
        # Calculate submitted = submitted_respondent + submitted_by_pencacah + approved_by_pengawas + rejected_by_pengawas etc
        # Wait, in patch_daily_summary, we calculated total_submitted as (submitted_respondent + submitted_by_pencacah). Let's use the exact sum from the CSV columns just in case:
        submitted = row.get('submitted_respondent', 0) + row.get('submitted_by_pencacah', 0)
        
        if kab_name not in m:
            m[kab_name] = {}
        if tgl not in m[kab_name]:
            m[kab_name][tgl] = 0
        m[kab_name][tgl] += submitted
    return m

map_umum = build_daily_map(df_umum)
map_ub = build_daily_map(df_ub)

today = datetime.now()
h0_date_str = today.strftime("%Y-%m-%d")
h1_date_str = (today - timedelta(days=1)).strftime("%Y-%m-%d")
h2_date_str = (today - timedelta(days=2)).strftime("%Y-%m-%d")

def get_sub(m, kab_name, date_str):
    if kab_name in m:
        return m[kab_name].get(date_str, 0)
    return 0

for survey_type in ["se_umum", "se_ub"]:
    if survey_type in ipas_data:
        m = map_umum if survey_type == "se_umum" else map_ub
        for kab in ipas_data[survey_type]:
            kab_name = kab.get("kabupaten", "")
            kab_clean = re.sub(r'\[\d+\]', '', kab_name).strip().upper()
            
            sub_h0 = get_sub(m, kab_clean, h0_date_str)
            sub_h1 = get_sub(m, kab_clean, h1_date_str)
            sub_h2 = get_sub(m, kab_clean, h2_date_str)
            
            prelist = kab.get("total_prelist", 0)
            
            if prelist > 0:
                kab["delta_persen"] = round((sub_h0 / prelist) * 100, 2)
                kab["delta_kemarin_persen"] = round((sub_h1 / prelist) * 100, 2)
                kab["delta_lusa_persen"] = round((sub_h2 / prelist) * 100, 2)
            else:
                kab["delta_persen"] = 0.0
                kab["delta_kemarin_persen"] = 0.0
                kab["delta_lusa_persen"] = 0.0

new_json = json.dumps(ipas_data, indent=2, ensure_ascii=False)
new_content = ipas_content[:match.start(1)] + new_json + ipas_content[match.end(1):]

with open("ipas_data.js", "w", encoding="utf-8") as f:
    f.write(new_content)

print("Berhasil memperbaiki Delta Kinerja (%) untuk UB agar tidak tembus ribuan persen!")
