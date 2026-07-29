import re

with open("petugas/fasih_petugas.py", "r") as f:
    content = f.read()

# Tambahkan import csv dan datetime
if "import csv" not in content:
    content = content.replace("import json", "import json\nimport csv\nimport datetime")

csv_logic = """
            # -- Append ke CSV --
            today_str = datetime.datetime.now().strftime("%Y-%m-%d")
            csv_file = f"/Users/jihanmaisaroh/scrap_fasih/fast_petugas_all_{today_str}.csv"
            
            # Buat header jika file belum ada
            file_exists = os.path.exists(csv_file)
            with open(csv_file, mode='a', newline='', encoding='utf-8') as f_csv:
                writer = csv.writer(f_csv)
                if not file_exists:
                    writer.writerow(["Email", "Role", "Region Code", "Total Target", "OPEN", "DRAFT", "SUBMITTED BY Pencacah", "SUBMITTED RESPONDENT", "APPROVED BY Pengawas", "REJECTED BY Pengawas", "REVOKED BY Pengawas", "EDITED BY Pengawas", "EDITED BY Admin Kabupaten", "REJECTED BY Admin Kabupaten", "COMPLETED BY Admin Kabupaten"])
                
                content_list = []
                if "data" in data and isinstance(data["data"], list):
                    content_list = data["data"]
                elif "content" in data and isinstance(data["content"], list):
                    content_list = data["content"]
                elif "data" in data and isinstance(data["data"], dict) and "content" in data["data"]:
                    content_list = data["data"]["content"]

                for row in content_list:
                    email = row.get("email", "")
                    # role_name is pengawas or pencacah, Capitalize it
                    role_c = "Pengawas" if role_name == "pengawas" else "Pencacah"
                    for r_sum in row.get("regionSummary", []):
                        reg_code = r_sum.get("regionCode", "")
                        status_breakdown = r_sum.get("statusBreakdown", [])
                        counts = { "OPEN": 0, "DRAFT": 0, "SUBMITTED BY PENCACAH": 0, "SUBMITTED RESPONDENT": 0, "APPROVED BY PENGAWAS": 0, "REJECTED BY PENGAWAS": 0, "REVOKED BY PENGAWAS": 0, "EDITED BY PENGAWAS": 0, "EDITED BY ADMIN KABUPATEN": 0, "REJECTED BY ADMIN KABUPATEN": 0, "COMPLETED BY ADMIN KABUPATEN": 0 }
                        total = r_sum.get("total", 0)
                        for st in status_breakdown:
                            st_name = st.get("status", "").upper()
                            if st_name in counts: counts[st_name] = st.get("count", 0)
                            else: counts[st_name] = st.get("count", 0)
                        writer.writerow([email, role_c, reg_code, total, counts.get("OPEN",0), counts.get("DRAFT",0), counts.get("SUBMITTED BY PENCACAH",0), counts.get("SUBMITTED RESPONDENT",0), counts.get("APPROVED BY PENGAWAS",0), counts.get("REJECTED BY PENGAWAS",0), counts.get("REVOKED BY PENGAWAS",0), counts.get("EDITED BY PENGAWAS",0), counts.get("EDITED BY ADMIN KABUPATEN",0), counts.get("REJECTED BY ADMIN KABUPATEN",0), counts.get("COMPLETED BY ADMIN KABUPATEN",0)])
            # -------------------
"""

content = content.replace('print(f"Berhasil mendapatkan Response tingkat {role_name}")', csv_logic + '\n            print(f"Berhasil mendapatkan Response tingkat {role_name}")')

with open("petugas/fasih_petugas.py", "w") as f:
    f.write(content)
