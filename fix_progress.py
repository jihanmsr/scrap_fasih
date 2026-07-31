import csv, json, os, datetime

today_str = datetime.datetime.now().strftime("%Y-%m-%d")
csv_file = f"/Users/jihanmaisaroh/scrap_fasih/fast_petugas_all_{today_str}.csv"
petugas_map = { "Pencacah": {}, "Pengawas": {} }

with open(csv_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        email = row.get("Email", "").strip().lower()
        if not email:
            email = row.get("assigneeEmail", "").strip().lower()
            if not email:
                email = row.get("assigneeUsername", "").strip().lower()
                if not email: continue

        role = row.get("Role", "")
        if not role:
            role = row.get("assigneeRoleAlias", "Pencacah")
        if role not in ["Pencacah", "Pengawas"]:
            role = "Pencacah"

        reg_code = row.get("Region Code", "")
        if not reg_code:
            continue
            
        total = int(row.get("Total Target", 0) or 0)
        
        if email not in petugas_map[role]:
            petugas_map[role][email] = { "target": 0, "submitted_pencacah": 0, "submitted_respondent": 0, "approved": 0, "rejected": 0, "draft": 0, "open": 0, "revoked": 0, "edited_pengawas": 0, "edited_admin": 0, "completed_admin": 0, "sls_details": {} }
        
        petugas_map[role][email]["target"] += total
        
        if "sls_details" not in petugas_map[role][email]:
            petugas_map[role][email]["sls_details"] = {}
        if reg_code not in petugas_map[role][email]["sls_details"]:
            petugas_map[role][email]["sls_details"][reg_code] = {"total": 0, "status": {}}
            
        petugas_map[role][email]["sls_details"][reg_code]["total"] += total
        
        statuses = ["OPEN", "DRAFT", "SUBMITTED BY Pencacah", "SUBMITTED RESPONDENT", "APPROVED BY Pengawas", "REJECTED BY Pengawas", "REVOKED BY Pengawas", "EDITED BY Pengawas", "EDITED BY Admin Kabupaten", "REJECTED BY Admin Kabupaten", "COMPLETED BY Admin Kabupaten"]
        
        for s in statuses:
            val = int(row.get(s, 0) or 0)
            s_name = s.upper()
            if val > 0:
                petugas_map[role][email]["sls_details"][reg_code]["status"][s_name] = petugas_map[role][email]["sls_details"][reg_code]["status"].get(s_name, 0) + val
                if s_name == "OPEN": petugas_map[role][email]["open"] += val
                elif s_name == "DRAFT": petugas_map[role][email]["draft"] += val
                elif "SUBMITTED BY PENCACAH" in s_name: petugas_map[role][email]["submitted_pencacah"] += val
                elif "SUBMITTED RESPONDENT" in s_name: petugas_map[role][email]["submitted_respondent"] += val
                elif "APPROVED" in s_name: petugas_map[role][email]["approved"] += val
                elif "REJECTED BY ADMIN" in s_name: petugas_map[role][email]["rejected"] += val
                elif "REJECTED" in s_name: petugas_map[role][email]["rejected"] += val
                elif "REVOKED" in s_name: petugas_map[role][email]["revoked"] += val
                elif "EDITED BY PENGAWAS" in s_name: petugas_map[role][email]["edited_pengawas"] += val
                elif "EDITED BY ADMIN" in s_name: petugas_map[role][email]["edited_admin"] += val
                elif "COMPLETED BY ADMIN" in s_name: petugas_map[role][email]["completed_admin"] += val

with open("/Users/jihanmaisaroh/scrap_fasih/fast_petugas_progress.js", "w") as f:
    f.write(f"window.PETUGAS_PROGRESS_MAP = {json.dumps(petugas_map, indent=4)};\n")
print("Done writing fast_petugas_progress.js!")
