import pandas as pd
import json
import re

with open("fast_petugas_history.js", "r") as f:
    content = f.read()

match = re.search(r'window\.PETUGAS_HISTORY_MAP\s*=\s*(\{.*\});?', content, re.DOTALL)
if not match:
    print("Cannot find json")
    exit(1)

hist = json.loads(match.group(1))

if "2026-07-20" in hist:
    df = pd.read_csv("fast_petugas_all_2026-07-20.csv")
    date_data = hist["2026-07-20"]
    
    new_date_data = {}
    for idx, row in df.iterrows():
        email = str(row['Email']).strip()
        if pd.isna(row['Email']): continue
        
        target = int(row.get('Total Target', 0))
        open_ = int(row.get('OPEN', 0))
        draft = int(row.get('DRAFT', 0))
        sub_pen = int(row.get('SUBMITTED BY Pencacah', 0))
        sub_res = int(row.get('SUBMITTED RESPONDENT', 0))
        app = int(row.get('APPROVED BY Pengawas', 0))
        rej = int(row.get('REJECTED BY Pengawas', 0))
        rev = int(row.get('REVOKED BY Pengawas', 0))
        ed_pen = int(row.get('EDITED BY Pengawas', 0))
        ed_adm = int(row.get('EDITED BY Admin Kabupaten', 0))
        com_adm = int(row.get('COMPLETED BY Admin Kabupaten', 0))
        
        if email not in new_date_data:
            new_date_data[email] = {
                "target": 0, "submitted_pencacah": 0, "submitted_respondent": 0,
                "approved": 0, "rejected": 0, "draft": 0, "open": 0, "revoked": 0,
                "edited_pengawas": 0, "edited_admin": 0, "completed_admin": 0,
                "sls_details": {}
            }
            
        d = new_date_data[email]
        d["target"] += target
        d["open"] += open_
        d["draft"] += draft
        d["submitted_pencacah"] += sub_pen
        d["submitted_respondent"] += sub_res
        d["approved"] += app
        d["rejected"] += rej
        d["revoked"] += rev
        d["edited_pengawas"] += ed_pen
        d["edited_admin"] += ed_adm
        d["completed_admin"] += com_adm
        
    hist["2026-07-20"] = new_date_data

new_json = json.dumps(hist, indent=4)
with open("fast_petugas_history.js", "w") as f:
    f.write(f"window.PETUGAS_HISTORY_MAP = {new_json};\n")
print("Fixed fast_petugas_history.js for 2026-07-20")
