import pandas as pd
import json
import re

csv_files = [
    'sqllab_tarik_dashboard_cdp_20260817T091824.csv', # SE UMUM
    'sqllab_tarik_dashboard_cdp_20260817T092442.csv'  # SE UB
]

dfs = [pd.read_csv(f) for f in csv_files]
df = pd.concat(dfs, ignore_index=True)

# Ensure numeric columns
cols = ['total_aktivitas', 'submitted_respondent', 'submitted_by_pencacah', 
        'approved_by_pengawas', 'rejected_by_pengawas', 'rejected_by_admin_kabupaten']

for c in cols:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0).astype(int)
    else:
        df[c] = 0

kab_mapping = {
    7201: "BANGGAI KEPULAUAN", 7202: "BANGGAI", 7203: "MOROWALI",
    7204: "POSO", 7205: "DONGGALA", 7206: "TOLI-TOLI", 7207: "BUOL",
    7208: "PARIGI MOUTONG", 7209: "TOJO UNA-UNA", 7210: "SIGI",
    7211: "BANGGAI LAUT", 7212: "MOROWALI UTARA", 7271: "PALU"
}

with open('daily_summary.js', 'r', encoding='utf-8') as f:
    content = f.read()

match = re.search(r'window\.DAILY_SUMMARY\s*=\s*(\[.*?\]);', content, re.DOTALL)
if not match:
    print("Could not find DAILY_SUMMARY in file")
    exit(1)

summary_list = json.loads(match.group(1))

# Keep data strictly before 12 August
new_summary = [item for item in summary_list if item['tanggal'] < '2026-08-12']

date_kab_map = {}

for _, row in df.iterrows():
    tgl = str(row['tanggal']).strip()
    if tgl < '2026-08-12':
        continue
        
    kab_code = int(row['kode_kabupaten'])
    kab_name = kab_mapping.get(kab_code, str(kab_code))
    
    submitted = row['submitted_respondent'] + row['submitted_by_pencacah']
    approved = row['approved_by_pengawas']
    rejected = row['rejected_by_pengawas'] + row['rejected_by_admin_kabupaten']
    aktivitas = row['total_aktivitas']
    
    key = (tgl, kab_name)
    if key not in date_kab_map:
        date_kab_map[key] = {
            "tanggal": tgl,
            "kabupaten": kab_name,
            "total_aktivitas": 0,
            "total_submitted": 0,
            "total_approved": 0,
            "total_rejected": 0,
            "total_usaha_tambahan": 0
        }
    
    date_kab_map[key]['total_aktivitas'] += aktivitas
    date_kab_map[key]['total_submitted'] += submitted
    date_kab_map[key]['total_approved'] += approved
    date_kab_map[key]['total_rejected'] += rejected

# Append the new combined data
for key in sorted(date_kab_map.keys()):
    new_summary.append(date_kab_map[key])

new_json = json.dumps(new_summary, indent=2, ensure_ascii=False)
content = content[:match.start(1)] + new_json + content[match.end(1):]

with open('daily_summary.js', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Berhasil mengupdate daily_summary.js dengan {len(date_kab_map)} record harian dari penggabungan SE UMUM dan SE UB!")
