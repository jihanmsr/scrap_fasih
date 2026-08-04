import os
import json
import csv
import glob

def rebuild_csv_for_date(date_str):
    csv_file = f"/Users/jihanmaisaroh/scrap_fasih/fast_petugas_all_{date_str}.csv"
    
    # Read all JSON files for this date
    json_files = glob.glob(f"/Users/jihanmaisaroh/scrap_fasih/petugas/petugas/*_{date_str}.json")
    
    if not json_files:
        print(f"No JSON files found for {date_str}")
        return

    # Write fresh CSV
    with open(csv_file, mode='w', newline='', encoding='utf-8') as f_csv:
        writer = csv.writer(f_csv)
        writer.writerow(["Email", "Role", "Region Code", "Total Target", "OPEN", "DRAFT", "SUBMITTED BY Pencacah", "SUBMITTED RESPONDENT", "APPROVED BY Pengawas", "REJECTED BY Pengawas", "REVOKED BY Pengawas", "EDITED BY Pengawas", "EDITED BY Admin Kabupaten", "REJECTED BY Admin Kabupaten", "COMPLETED BY Admin Kabupaten"])
        
        for jf in json_files:
            role_name = "Pengawas" if "pengawas" in jf.lower() else "Pencacah"
            with open(jf, "r") as f_in:
                try:
                    data = json.load(f_in)
                except:
                    continue
                    
            content_list = []
            if "data" in data and isinstance(data["data"], list):
                content_list = data["data"]
            elif "content" in data and isinstance(data["content"], list):
                content_list = data["content"]
            elif "data" in data and isinstance(data["data"], dict) and "content" in data["data"]:
                content_list = data["data"]["content"]
                
            for row in content_list:
                email = row.get("email", "")
                for r_sum in row.get("regionSummary", []):
                    reg_code = r_sum.get("regionCode", "")
                    status_breakdown = r_sum.get("statusBreakdown", [])
                    counts = { "OPEN": 0, "DRAFT": 0, "SUBMITTED BY PENCACAH": 0, "SUBMITTED RESPONDENT": 0, "APPROVED BY PENGAWAS": 0, "REJECTED BY PENGAWAS": 0, "REVOKED BY PENGAWAS": 0, "EDITED BY PENGAWAS": 0, "EDITED BY ADMIN KABUPATEN": 0, "REJECTED BY ADMIN KABUPATEN": 0, "COMPLETED BY ADMIN KABUPATEN": 0 }
                    total = r_sum.get("total", 0)
                    for st in status_breakdown:
                        st_name = st.get("status", "").upper()
                        counts[st_name] = counts.get(st_name, 0) + st.get("count", 0)
                    writer.writerow([email, role_name, reg_code, total, counts.get("OPEN",0), counts.get("DRAFT",0), counts.get("SUBMITTED BY PENCACAH",0), counts.get("SUBMITTED RESPONDENT",0), counts.get("APPROVED BY PENGAWAS",0), counts.get("REJECTED BY PENGAWAS",0), counts.get("REVOKED BY PENGAWAS",0), counts.get("EDITED BY PENGAWAS",0), counts.get("EDITED BY ADMIN KABUPATEN",0), counts.get("REJECTED BY ADMIN KABUPATEN",0), counts.get("COMPLETED BY ADMIN KABUPATEN",0)])

    print(f"Rebuilt {csv_file}")

rebuild_csv_for_date("2026-08-02")
rebuild_csv_for_date("2026-08-03")
