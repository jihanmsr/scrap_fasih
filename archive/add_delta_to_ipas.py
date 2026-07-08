import pandas as pd
import json
import re
import math

# 1. Read Excel
excel_path = "Progres Sulteng Fasih SM SE2026.xlsx"
xls = pd.ExcelFile(excel_path)
valid_sheets = [s for s in xls.sheet_names if 'Juli' in s or 'Agustus' in s or 'Juni' in s]

if len(valid_sheets) < 2:
    print("Not enough sheets for delta")
    exit(1)

today_sheet = valid_sheets[-1]
yesterday_sheet = valid_sheets[-2]

df_today = pd.read_excel(excel_path, sheet_name=today_sheet)
df_yesterday = pd.read_excel(excel_path, sheet_name=yesterday_sheet)

delta_map = {}
for idx, row in df_today.iterrows():
    try:
        if pd.isna(row['Wilayah']): continue
        wcode = str(int(float(row['Wilayah'])))
        pct_today = float(row.get('Persentase', 0))
        
        match = df_yesterday[df_yesterday['Wilayah'].astype(str).str.replace('.0','',regex=False) == wcode]
        if not match.empty:
            pct_yesterday = float(match.iloc[0].get('Persentase', 0))
            delta = pct_today - pct_yesterday
            delta_map[wcode] = round(delta, 2)
    except Exception as e:
        print(e)

print(f"Delta map calculated: {delta_map}")

# 2. Inject into ipas_data.js
KAB_MAPPING = {
    "7201": "[01] BANGGAI KEPULAUAN",
    "7202": "[02] BANGGAI",
    "7203": "[03] MOROWALI",
    "7204": "[04] POSO",
    "7205": "[05] DONGGALA",
    "7206": "[06] TOLI-TOLI",
    "7207": "[07] BUOL",
    "7208": "[08] PARIGI MOUTONG",
    "7209": "[09] TOJO UNA-UNA",
    "7210": "[10] SIGI",
    "7211": "[11] BANGGAI LAUT",
    "7212": "[12] MOROWALI UTARA",
    "7271": "[71] PALU"
}

with open('ipas_data.js', 'r', encoding='utf-8') as f:
    content = f.read()

pattern = re.compile(r'window\.IPAS_DATA\s*=\s*(\{.*?\});', re.DOTALL)
match = pattern.search(content)
if not match:
    print("Could not find window.IPAS_DATA in ipas_data.js")
    exit(1)

data = json.loads(match.group(1))

def update_survey(survey_type):
    if survey_type in data:
        for kab in data[survey_type]:
            kab_name = kab.get("kabupaten")
            # Find code
            code = None
            for k, v in KAB_MAPPING.items():
                if v == kab_name:
                    code = k
                    break
            if code and code in delta_map:
                kab["delta_persen"] = delta_map[code]
            else:
                kab["delta_persen"] = 0.0

update_survey("se_umum")
update_survey("se_ub")

with open('ipas_data.js', 'w', encoding='utf-8') as f:
    f.write("window.IPAS_DATA = " + json.dumps(data, indent=2, ensure_ascii=False) + ";\n")

print("Successfully injected delta into ipas_data.js")
