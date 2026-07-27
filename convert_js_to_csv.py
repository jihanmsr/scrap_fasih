import json
import csv
import datetime

# Read the JS file
with open("fast_petugas_progress.js", "r") as f:
    data = f.read().split("=", 1)[1].strip().strip(";")
    j = json.loads(data)

# Extract data
rows = []
for role, users in j.items():
    for email, details in users.items():
        sls_details = details.get("sls_details", {})
        for reg_code, sls in sls_details.items():
            total = sls.get("total", 0)
            status = sls.get("status", {})
            
            rows.append({
                "Email": email,
                "Role": role,
                "Region Code": reg_code,
                "Total Target": total,
                "OPEN": status.get("OPEN", 0),
                "DRAFT": status.get("DRAFT", 0),
                "SUBMITTED BY Pencacah": status.get("SUBMITTED BY PENCACAH", 0),
                "SUBMITTED RESPONDENT": status.get("SUBMITTED RESPONDENT", 0),
                "APPROVED BY Pengawas": status.get("APPROVED BY PENGAWAS", 0) or status.get("APPROVED", 0),
                "REJECTED BY Pengawas": status.get("REJECTED BY PENGAWAS", 0) or status.get("REJECTED", 0),
                "REVOKED BY Pengawas": status.get("REVOKED BY PENGAWAS", 0),
                "EDITED BY Pengawas": status.get("EDITED BY PENGAWAS", 0),
                "EDITED BY Admin Kabupaten": status.get("EDITED BY ADMIN KABUPATEN", 0),
                "REJECTED BY Admin Kabupaten": status.get("REJECTED BY ADMIN KABUPATEN", 0),
                "COMPLETED BY Admin Kabupaten": status.get("COMPLETED BY ADMIN KABUPATEN", 0)
            })

# Write CSV
today_str = datetime.datetime.now().strftime("%Y-%m-%d")
csv_filename = f"rekap_dari_js_{today_str}.csv"
fieldnames = ["Email", "Role", "Region Code", "Total Target", "OPEN", "DRAFT", "SUBMITTED BY Pencacah", "SUBMITTED RESPONDENT", "APPROVED BY Pengawas", "REJECTED BY Pengawas", "REVOKED BY Pengawas", "EDITED BY Pengawas", "EDITED BY Admin Kabupaten", "REJECTED BY Admin Kabupaten", "COMPLETED BY Admin Kabupaten"]

with open(csv_filename, "w", newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for r in rows:
        writer.writerow(r)

print(f"Berhasil membuat {csv_filename} dengan {len(rows)} baris data.")
