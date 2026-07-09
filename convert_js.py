import json
import csv

csv_file = "/Users/jihanmaisaroh/scrap_fasih/fast_petugas_palu.csv"
petugas_map = {
    "Pencacah": {},
    "Pengawas": {}
}

with open(csv_file, "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        email = row.get("Email", "").strip().lower()
        role = row.get("Role", "")
        if not email or not role: continue
        if email not in petugas_map[role]:
            petugas_map[role][email] = {
                "target": 0, "submitted_pencacah": 0, "submitted_respondent": 0,
                "approved": 0, "rejected": 0, "draft": 0, "open": 0
            }
        
        petugas_map[role][email]["target"] += int(row.get("Total Target", 0))
        petugas_map[role][email]["open"] += int(row.get("OPEN", 0))
        petugas_map[role][email]["draft"] += int(row.get("DRAFT", 0))
        petugas_map[role][email]["submitted_pencacah"] += int(row.get("SUBMITTED BY Pencacah", 0))
        petugas_map[role][email]["approved"] += int(row.get("APPROVED BY Pengawas", 0))
        petugas_map[role][email]["rejected"] += int(row.get("REJECTED BY Pengawas", 0))

js_file = "/Users/jihanmaisaroh/scrap_fasih/fast_petugas_progress.js"
with open(js_file, "w") as f:
    f.write(f"window.PETUGAS_PROGRESS_MAP = {json.dumps(petugas_map, indent=4)};\n")
print("Done")
