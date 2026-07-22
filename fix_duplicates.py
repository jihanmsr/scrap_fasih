import csv
import json
import re

# 1. Deduplicate the CSV file
csv_filename = "fast_petugas_all_2026-07-20.csv"
unique_rows = []
seen = set()
header = None

with open(csv_filename, 'r') as f:
    reader = csv.reader(f)
    for i, row in enumerate(reader):
        if i == 0:
            header = row
            unique_rows.append(row)
            continue
        
        row_tuple = tuple(row)
        if row_tuple not in seen:
            seen.add(row_tuple)
            unique_rows.append(row)

# Save deduplicated CSV
with open(csv_filename, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerows(unique_rows)

print(f"Deduplicated CSV: saved {len(unique_rows)} rows.")

# 2. Re-calculate the stats for 2026-07-20
# email, role, id_sls, target, open, draft, submitted_pencacah, approved, rejected, edited_admin, completed_admin, submitted_respondent, revoked, edited_pengawas

recalc_data = {"Pencacah": {}, "Pengawas": {}}

for i, row in enumerate(unique_rows):
    if i == 0:
        continue
    if len(row) < 14:
        continue
        
    email, role, id_sls = row[0], row[1], row[2]
    
    try:
        target = int(row[3])
        open_val = int(row[4])
        draft = int(row[5])
        submitted_pencacah = int(row[6])
        approved = int(row[7])
        rejected = int(row[8])
        edited_admin = int(row[9])
        completed_admin = int(row[10])
        submitted_respondent = int(row[11])
        revoked = int(row[12])
        edited_pengawas = int(row[13])
    except:
        continue

    if role not in recalc_data:
        recalc_data[role] = {}
        
    if email not in recalc_data[role]:
        recalc_data[role][email] = {
            "target": 0, "submitted_pencacah": 0, "submitted_respondent": 0, 
            "approved": 0, "rejected": 0, "draft": 0, "open": 0, "revoked": 0, 
            "edited_pengawas": 0, "edited_admin": 0, "completed_admin": 0, "sls_details": {}
        }
        
    p = recalc_data[role][email]
    p["target"] += target
    p["submitted_pencacah"] += submitted_pencacah
    p["submitted_respondent"] += submitted_respondent
    p["approved"] += approved
    p["rejected"] += rejected
    p["draft"] += draft
    p["open"] += open_val
    p["revoked"] += revoked
    p["edited_pengawas"] += edited_pengawas
    p["edited_admin"] += edited_admin
    p["completed_admin"] += completed_admin

# 3. Update fast_petugas_history.js
history_filename = "fast_petugas_history.js"
with open(history_filename, 'r') as f:
    content = f.read()

match = re.search(r'window\.PETUGAS_HISTORY_MAP\s*=\s*(\{.*?\});', content, re.DOTALL)
if match:
    history_data = json.loads(match.group(1))
    
    if "2026-07-20" in history_data:
        history_data["2026-07-20"] = recalc_data
        print("Updated history data for 2026-07-20 in memory.")
        
        # Save back to file
        new_json = json.dumps(history_data, indent=4)
        new_content = f"window.PETUGAS_HISTORY_MAP = {new_json};"
        
        with open(history_filename, 'w') as f:
            f.write(new_content)
        print("Successfully written back to fast_petugas_history.js")
else:
    print("Could not parse PETUGAS_HISTORY_MAP")

