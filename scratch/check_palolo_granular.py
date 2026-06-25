import json

with open("granular_assignments_se_umum_7210.json", "r", encoding="utf-8") as f:
    data = json.load(f)

compressed = data.get("compressed_data", [])
cols = data.get("columns", [])
region_idx = cols.index("region")

palolo = 0
sigi_biro = 0
for row in compressed:
    region = row[region_idx] or ""
    if "PALOLO" in region:
        palolo += 1
    elif "SIGI BIROMARU" in region:
        sigi_biro += 1

print("PALOLO target count in JSON:", palolo)
print("SIGI BIROMARU target count in JSON:", sigi_biro)
