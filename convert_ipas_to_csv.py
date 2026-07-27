import json, csv, os

def clean_json_str(content):
    start = content.find('{')
    end = content.rfind('}') + 1
    return content[start:end]

try:
    with open("ipas_data.js", "r") as f:
        content = f.read()
        j = json.loads(clean_json_str(content))

    for survey_type in ["se_umum", "se_ub"]:
        if survey_type not in j: continue
        
        rows = []
        for kab_data in j[survey_type]:
            kab_name = kab_data.get("kabupaten", "")
            for kec in kab_data.get("kecamatan_list", []):
                rows.append({
                    "Kabupaten": kab_name,
                    "Kecamatan": kec.get("kecamatan", ""),
                    "Total Prelist": kec.get("total_prelist", 0),
                    "Total Draft": kec.get("total_draft", 0),
                    "Total Open": kec.get("total_open", 0),
                    "Total Submitted": kec.get("total_submitted", 0),
                    "Total Rejected": kec.get("total_rejected", 0),
                    "Total Approved": kec.get("total_approved", 0),
                    "Submitted Pencacah": kec.get("total_submitted_pencacah", 0),
                    "Submitted Respondent": kec.get("total_submitted_respondent", 0),
                    "Persentase": kec.get("persentase", 0),
                    "Today Completed": kec.get("today_completed", 0),
                    "Yesterday Completed": kec.get("yesterday_completed", 0),
                    "New Usaha": kec.get("new_usaha_overall", 0),
                    "New Rumah": kec.get("new_rumah_overall", 0)
                })
                
        if rows:
            csv_file = f"ipas_data_{survey_type}.csv"
            with open(csv_file, "w", newline="") as f:
                fieldnames = ["Kabupaten", "Kecamatan", "Total Prelist", "Total Draft", "Total Open", "Total Submitted", "Total Rejected", "Total Approved", "Submitted Pencacah", "Submitted Respondent", "Persentase", "Today Completed", "Yesterday Completed", "New Usaha", "New Rumah"]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for r in rows:
                    writer.writerow(r)
            print(f"Berhasil membuat {csv_file} ({len(rows)} baris)")
except Exception as e:
    print(f"Error parse ipas_data.js: {e}")

try:
    with open("daily_summary.js", "r") as f:
        content = f.read()
        ds = json.loads(clean_json_str(content))
    
    for survey_type in ["se_umum", "se_ub"]:
        if survey_type not in ds: continue
        rows = []
        for date_str, kab_data in ds[survey_type].items():
            for kab_code, data in kab_data.items():
                rows.append({
                    "Date": date_str,
                    "Kab Code": kab_code,
                    "Total Target": data.get("total", 0),
                    "Total Submitted": data.get("submitted", 0),
                    "Delta Completed": data.get("delta_completed", 0),
                    "Delta Submitted": data.get("delta_submitted", 0)
                })
        
        if rows:
            csv_file = f"daily_summary_{survey_type}.csv"
            with open(csv_file, "w", newline="") as f:
                fieldnames = ["Date", "Kab Code", "Total Target", "Total Submitted", "Delta Completed", "Delta Submitted"]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for r in rows:
                    writer.writerow(r)
            print(f"Berhasil membuat {csv_file} ({len(rows)} baris)")
except Exception as e:
    print(f"daily_summary.js error: {e}")
