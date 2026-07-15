import json, csv

with open("fast_petugas_history.js", "r") as f:
    content = f.read()
    start = content.find('{')
    end = content.rfind('}') + 1
    history_map = json.loads(content[start:end])

files = ["fast_petugas_all_2026-07-14.csv", "fast_petugas_all_2026-07-15.csv"]
for f in files:
    date_str = f.replace("fast_petugas_all_", "").replace(".csv", "")
    print(f"Updating date {date_str}...")
    petugas_map = {"Pencacah": {}, "Pengawas": {}}
    
    with open(f, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            email = row.get('Email', '').strip()
            if not email: continue
            
            role = row.get('Role', 'Pencacah')
            if role not in ['Pencacah', 'Pengawas']: role = 'Pencacah'
            
            if email not in petugas_map[role]:
                petugas_map[role][email] = {
                    "target": 0, "submitted_pencacah": 0, "submitted_respondent": 0,
                    "approved": 0, "rejected": 0, "draft": 0, "open": 0,
                    "revoked": 0, "edited_pengawas": 0, "edited_admin": 0, "completed_admin": 0,
                    "sls_details": {}
                }
                
            petugas_map[role][email]["target"] += int(row.get('Total Target', 0))
            petugas_map[role][email]["open"] += int(row.get('OPEN', 0))
            petugas_map[role][email]["draft"] += int(row.get('DRAFT', 0))
            petugas_map[role][email]["submitted_pencacah"] += int(row.get('SUBMITTED BY Pencacah', 0))
            petugas_map[role][email]["submitted_respondent"] += int(row.get('SUBMITTED RESPONDENT', 0))
            petugas_map[role][email]["approved"] += int(row.get('APPROVED BY Pengawas', 0))
            petugas_map[role][email]["rejected"] += int(row.get('REJECTED BY Pengawas', 0)) + int(row.get('REJECTED BY Admin Kabupaten', 0))
            petugas_map[role][email]["revoked"] += int(row.get('REVOKED BY Pengawas', 0))
            petugas_map[role][email]["edited_pengawas"] += int(row.get('EDITED BY Pengawas', 0))
            petugas_map[role][email]["edited_admin"] += int(row.get('EDITED BY Admin Kabupaten', 0))
            petugas_map[role][email]["completed_admin"] += int(row.get('COMPLETED BY Admin Kabupaten', 0))
            
    history_map[date_str] = petugas_map
    
with open("fast_petugas_history.js", "w", encoding='utf-8') as f:
    f.write(f"window.PETUGAS_HISTORY_MAP = {json.dumps(history_map, indent=4)};\n")

print("Done fixing fast_petugas_history.js for real!")
