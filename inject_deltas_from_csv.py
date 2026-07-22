import pandas as pd
import json
import re

# Read ipas_data.js
with open("ipas_data.js", "r") as f:
    ipas_content = f.read()
match = re.search(r'window\.IPAS_DATA\s*=\s*(\{.*?\});', ipas_content, re.DOTALL)
if not match:
    print("Could not parse ipas_data.js")
    exit(1)
ipas_data = json.loads(match.group(1))

# Process CSVs
try:
    df_h1 = pd.read_csv("fast_petugas_all_2026-07-21.csv")
    df_h2 = pd.read_csv("fast_petugas_all_2026-07-20.csv")
    df_today = pd.read_csv("fast_petugas_all_2026-07-22.csv")
except Exception as e:
    print(f"Error reading CSVs: {e}")
    exit(1)

# Clean column name just in case
def get_approved_col(df):
    for col in df.columns:
        if 'APPROVED' in col.upper():
            return col
    return None

def get_counts_se_umum(df):
    counts = {}
    approved_col = get_approved_col(df)
    if not approved_col: return counts
    
    for idx, row in df.iterrows():
        kode = str(row['Region Code']).zfill(16)
        if len(kode) >= 16 and kode[-2:] == '00':
            kab_code = kode[2:4]
            kab_name = get_kab_name(kab_code)
            counts[kab_name] = counts.get(kab_name, 0) + row[approved_col]
    return counts

def get_counts_se_ub(df):
    counts = {}
    approved_col = get_approved_col(df)
    if not approved_col: return counts
    
    for idx, row in df.iterrows():
        kode = str(row['Region Code']).zfill(16)
        if len(kode) >= 16 and kode[-2:] != '00':
            kab_code = kode[2:4]
            kab_name = get_kab_name(kab_code)
            counts[kab_name] = counts.get(kab_name, 0) + row[approved_col]
    return counts

kab_map = {
    '01': 'BANGGAI KEPULAUAN', '02': 'BANGGAI', '03': 'MOROWALI', '04': 'POSO',
    '05': 'DONGGALA', '06': 'TOLI-TOLI', '07': 'BUOL', '08': 'PARIGI MOUTONG',
    '09': 'TOJO UNA-UNA', '10': 'SIGI', '11': 'BANGGAI LAUT', '12': 'MOROWALI UTARA',
    '71': 'PALU'
}
def get_kab_name(code):
    return kab_map.get(code, 'UNKNOWN')

h1_se_umum = get_counts_se_umum(df_h1)
h2_se_umum = get_counts_se_umum(df_h2)
today_se_umum = get_counts_se_umum(df_today)

h1_se_ub = get_counts_se_ub(df_h1)
h2_se_ub = get_counts_se_ub(df_h2)
today_se_ub = get_counts_se_ub(df_today)

def update_kab_deltas(survey_list, h1_counts, h2_counts, today_counts):
    for kab in survey_list:
        kab_name = kab.get("kabupaten", "")
        kab_clean = re.sub(r'\[\d+\]', '', kab_name).strip().upper()
        
        tc0 = today_counts.get(kab_clean, 0)
        tc1 = h1_counts.get(kab_clean, 0)
        tc2 = h2_counts.get(kab_clean, 0)
        
        prelist = kab.get("total_prelist", 0)
        
        if prelist > 0:
            kab["delta_persen"] = round(((tc0 - tc1) / prelist) * 100, 2)
            kab["delta_kemarin_persen"] = round(((tc1 - tc2) / prelist) * 100, 2)
            kab["delta_lusa_persen"] = 0.0 # No H-3 data
        else:
            kab["delta_persen"] = 0.0
            kab["delta_kemarin_persen"] = 0.0
            kab["delta_lusa_persen"] = 0.0

if "se_umum" in ipas_data:
    update_kab_deltas(ipas_data["se_umum"], h1_se_umum, h2_se_umum, today_se_umum)

if "se_ub" in ipas_data:
    update_kab_deltas(ipas_data["se_ub"], h1_se_ub, h2_se_ub, today_se_ub)

new_json = json.dumps(ipas_data, indent=2)
new_content = f"window.IPAS_DATA = {new_json};\n"

with open("ipas_data.js", "w") as f:
    f.write(new_content)

print("Injected actual delta values from CSV history!")
