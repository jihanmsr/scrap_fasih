import json, gzip, base64

d = json.load(open("/Users/jihanmaisaroh/scrap_fasih/granular_assignments_se_umum_7271.json"))
raw = gzip.decompress(base64.b64decode(d["compressed_data"])).decode("utf-8")
raw_json = json.loads(raw)

p_idx = -1
for i, p in enumerate(raw_json["petugas"]):
    if "tajahyanti" in p[0].lower():
        p_idx = i
        break

if p_idx == -1:
    print("Not found")
else:
    print(f"Found at index {p_idx}: {raw_json['petugas'][p_idx]}")
    status_counts = {}
    for t in raw_json["targets"]:
        if t[6] == p_idx: # Pencacah
            s_idx = t[5] # Overall status
            pcl_s_idx = t[7] # Pcl status
            status_name = raw_json["statuses"][s_idx]
            pcl_s_name = raw_json["statuses"][pcl_s_idx] if pcl_s_idx != -1 else ""
            
            # Use the logic from app.js to determine final status
            final_s = status_name
            if final_s == "OPEN" and pcl_s_name == "SUBMITTED":
                final_s = "SUBMITTED BY Pencacah"
                
            status_counts[final_s] = status_counts.get(final_s, 0) + 1
            
    print("Status counts for taja:", status_counts)
