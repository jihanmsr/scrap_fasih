import csv, json, os, glob

history_map = {}

files = glob.glob("fast_petugas_all_2026-*.csv")
for f in sorted(files):
    date_str = f.replace("fast_petugas_all_", "").replace(".csv", "")
    print(f"Processing {f} for date {date_str}...")
    
    petugas_map = {"Pencacah": {}, "Pengawas": {}}
    
    with open(f, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if 'Email' in row:
                # Summarized CSV format
                email = row['Email'].strip()
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
                
                p_map = petugas_map[role][email]
                p_map["target"] += int(row.get("Total Target") or 0)
                p_map["open"] += int(row.get("OPEN") or 0)
                p_map["draft"] += int(row.get("DRAFT") or 0)
                p_map["submitted_pencacah"] += int(row.get("SUBMITTED BY Pencacah") or 0)
                p_map["submitted_respondent"] += int(row.get("SUBMITTED RESPONDENT") or 0)
                p_map["approved"] += int(row.get("APPROVED BY Pengawas") or 0)
                p_map["rejected"] += int(row.get("REJECTED BY Pengawas") or 0) + int(row.get("REJECTED BY Admin Kabupaten") or 0)
                p_map["revoked"] += int(row.get("REVOKED BY Pengawas") or 0)
                p_map["edited_pengawas"] += int(row.get("EDITED BY Pengawas") or 0)
                p_map["edited_admin"] += int(row.get("EDITED BY Admin Kabupaten") or 0)
                p_map["completed_admin"] += int(row.get("COMPLETED BY Admin Kabupaten") or 0)
            else:
                # Raw CSV format
                role = row.get('assigneeRoleAlias', 'Pencacah')
                if role not in ['Pencacah', 'Pengawas']:
                    role = 'Pencacah'
                    
                email = row.get('assigneeEmail', '').strip()
                if not email:
                    email = row.get('assigneeUsername', '').strip()
                    
                if not email: continue
                
                s_name = row.get('assignmentStatusAlias', 'OPEN')
                if not s_name: s_name = 'OPEN'
                s_name = s_name.upper()
                
                if email not in petugas_map[role]:
                    petugas_map[role][email] = {
                        "target": 0, "submitted_pencacah": 0, "submitted_respondent": 0,
                        "approved": 0, "rejected": 0, "draft": 0, "open": 0,
                        "revoked": 0, "edited_pengawas": 0, "edited_admin": 0, "completed_admin": 0,
                        "sls_details": {}
                    }
                    
                petugas_map[role][email]["target"] += 1
                
                if s_name == "OPEN": petugas_map[role][email]["open"] += 1
                elif s_name == "DRAFT": petugas_map[role][email]["draft"] += 1
                elif s_name == "SUBMITTED BY PENCACAH": petugas_map[role][email]["submitted_pencacah"] += 1
                elif s_name == "SUBMITTED RESPONDENT": petugas_map[role][email]["submitted_respondent"] += 1
                elif "APPROVED" in s_name: petugas_map[role][email]["approved"] += 1
                elif "REJECTED BY ADMIN" in s_name: petugas_map[role][email]["rejected"] += 1
                elif "REJECTED" in s_name: petugas_map[role][email]["rejected"] += 1
                elif "REVOKED" in s_name: petugas_map[role][email]["revoked"] += 1
                elif "EDITED BY PENGAWAS" in s_name: petugas_map[role][email]["edited_pengawas"] += 1
                elif "EDITED BY ADMIN" in s_name: petugas_map[role][email]["edited_admin"] += 1
                elif "COMPLETED BY ADMIN" in s_name: petugas_map[role][email]["completed_admin"] += 1
            
    history_map[date_str] = petugas_map
    
with open("fast_petugas_history.js", "w", encoding='utf-8') as f:
    f.write(f"window.PETUGAS_HISTORY_MAP = {json.dumps(history_map, indent=4)};\n")

print("Done rebuilding fast_petugas_history.js!")
