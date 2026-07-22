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

# Let's fix July 20 and July 21 if they are broken
def fix_date(date_str, csv_file):
    if date_str in hist:
        df = pd.read_csv(csv_file)
        
        new_date_data = {"Pencacah": {}, "Pengawas": {}}
        for idx, row in df.iterrows():
            email = str(row['Email']).strip()
            role = str(row.get('Role', 'Pencacah')).strip()
            if pd.isna(row['Email']): continue
            
            # Use 'Pencacah' or 'Pengawas'
            role_key = "Pengawas" if "pengawas" in role.lower() else "Pencacah"
            
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
            
            # region detail
            region = str(row.get('Region Code', ''))
            
            if email not in new_date_data[role_key]:
                new_date_data[role_key][email] = {
                    "target": 0, "submitted_pencacah": 0, "submitted_respondent": 0,
                    "approved": 0, "rejected": 0, "draft": 0, "open": 0, "revoked": 0,
                    "edited_pengawas": 0, "edited_admin": 0, "completed_admin": 0,
                    "sls_details": {}
                }
                
            d = new_date_data[role_key][email]
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
            
            if region:
                if region not in d["sls_details"]:
                    d["sls_details"][region] = {"total": 0, "status": {}}
                d["sls_details"][region]["total"] += target
                if open_ > 0: d["sls_details"][region]["status"]["OPEN"] = d["sls_details"][region]["status"].get("OPEN", 0) + open_
                if app > 0: d["sls_details"][region]["status"]["APPROVED BY Pengawas"] = d["sls_details"][region]["status"].get("APPROVED BY Pengawas", 0) + app
                if sub_pen > 0: d["sls_details"][region]["status"]["SUBMITTED BY Pencacah"] = d["sls_details"][region]["status"].get("SUBMITTED BY Pencacah", 0) + sub_pen
                # Add others if needed...
            
        hist[date_str] = new_date_data

# Fix both 20 and 21 from their exact CSVs
fix_date("2026-07-20", "fast_petugas_all_2026-07-20.csv")
fix_date("2026-07-21", "fast_petugas_all_2026-07-21.csv")

new_json = json.dumps(hist, indent=4)
with open("fast_petugas_history.js", "w") as f:
    f.write(f"window.PETUGAS_HISTORY_MAP = {new_json};\n")
print("Fixed fast_petugas_history.js for 20 and 21")
