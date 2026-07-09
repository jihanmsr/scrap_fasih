import json, gzip, base64

d = json.load(open("/Users/jihanmaisaroh/scrap_fasih/granular_assignments_se_umum_7271.json"))
raw = gzip.decompress(base64.b64decode(d["compressed_data"])).decode("utf-8")
raw_json = json.loads(raw)

p_idx = -1
for i, p in enumerate(raw_json["petugas"]):
    if "puguhsnt79@gmail.com" in str(p[0]).lower():
        p_idx = i
        break

if p_idx == -1:
    print("Not found")
else:
    print(f"Found Fatmawati at index {p_idx}: {raw_json['petugas'][p_idx]}")
    status_counts = {}
    for t in raw_json["targets"]:
        if t[4] == p_idx or t[8] == p_idx:
            status_name = raw_json["statuses"][t[3]].upper()
            status_counts[status_name] = status_counts.get(status_name, 0) + 1
            
    print("Status counts for Fatmawati in granular data:", status_counts)
