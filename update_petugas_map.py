import json, re, os, gzip, base64

pp_file = "/Users/jihanmaisaroh/scrap_fasih/petugas_progress.js"
with open(pp_file, 'r') as f:
    pp_content = f.read()

json_str = pp_content.replace('window.PETUGAS_PROGRESS_MAP = ', '').strip()
if json_str.endswith(';'):
    json_str = json_str[:-1]

petugas_map = json.loads(json_str)

new_progress = {}

for f in os.listdir("/Users/jihanmaisaroh/scrap_fasih"):
    if f.startswith("granular_assignments_se_umum_") and f.endswith(".json"):
        kab = f.split("_")[-1].replace(".json", "")
        d = json.load(open(f"/Users/jihanmaisaroh/scrap_fasih/{f}"))
        if "compressed_data" not in d: continue
        raw = gzip.decompress(base64.b64decode(d["compressed_data"])).decode("utf-8")
        raw_json = json.loads(raw)
        
        petugas_idx_to_email = {}
        for i, p in enumerate(raw_json["petugas"]):
            email = str(p[0]).strip().lower()
            if email and email != '-':
                petugas_idx_to_email[i] = email
                if email not in new_progress:
                    new_progress[email] = {
                        "target": 0, "submitted_pencacah": 0, "submitted_respondent": 0,
                        "approved": 0, "rejected": 0, "draft": 0, "open": 0
                    }
                
        for t in raw_json["targets"]:
            overall_status = raw_json["statuses"][t[3]].upper()
            
            pencacah_idx = t[4]
            pengawas_idx = t[8]
            
            # Assign progress to Pencacah
            if pencacah_idx != -1 and pencacah_idx in petugas_idx_to_email:
                email = petugas_idx_to_email[pencacah_idx]
                new_progress[email]["target"] += 1
                if overall_status == "SUBMITTED BY PENCACAH":
                    new_progress[email]["submitted_pencacah"] += 1
                elif "APPROVED" in overall_status:
                    new_progress[email]["approved"] += 1
                elif "REJECTED" in overall_status:
                    new_progress[email]["rejected"] += 1
                elif overall_status == "DRAFT":
                    new_progress[email]["draft"] += 1
                elif overall_status == "OPEN":
                    new_progress[email]["open"] += 1
            
            # Assign progress to Pengawas
            if pengawas_idx != -1 and pengawas_idx in petugas_idx_to_email:
                email = petugas_idx_to_email[pengawas_idx]
                new_progress[email]["target"] += 1
                if overall_status == "SUBMITTED BY PENCACAH":
                    new_progress[email]["submitted_pencacah"] += 1
                elif "APPROVED" in overall_status:
                    new_progress[email]["approved"] += 1
                elif "REJECTED" in overall_status:
                    new_progress[email]["rejected"] += 1
                elif overall_status == "DRAFT":
                    new_progress[email]["draft"] += 1
                elif overall_status == "OPEN":
                    new_progress[email]["open"] += 1

updated_count = 0
for email, prog in new_progress.items():
    if prog["target"] > 0:
        petugas_map[email] = prog
        updated_count += 1

with open(pp_file, 'w') as f:
    f.write(f"window.PETUGAS_PROGRESS_MAP = {json.dumps(petugas_map, indent=4)};\n")
    
print(f"Successfully updated {updated_count} petugas in PETUGAS_PROGRESS_MAP.")
