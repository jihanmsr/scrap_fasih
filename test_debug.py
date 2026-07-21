import json

with open("fast_petugas_progress.js", "r") as f:
    data = f.read().split("=", 1)[1].strip().strip(";")
    j = json.loads(data)

pencacah = j.get("Pencacah", {})
parigi = []
for email, details in pencacah.items():
    for reg in details.get("sls_details", {}):
        if reg.startswith("7208"):
            parigi.append(email)
            break
print(f"Total: {len(parigi)}")
print(f"Sample: {parigi[:10]}")
