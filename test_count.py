import json

with open("fast_petugas_progress.js", "r") as f:
    data = f.read().split("=", 1)[1].strip().strip(";")
    j = json.loads(data)

pencacah = j.get("Pencacah", {})
parigi = 0
for email, details in pencacah.items():
    for reg in details.get("sls_details", {}):
        if reg.startswith("7208"):
            parigi += 1
            break
print(f"Parigi Moutong Pencacah: {parigi}")

pengawas = j.get("Pengawas", {})
parigi_p = 0
for email, details in pengawas.items():
    for reg in details.get("sls_details", {}):
        if reg.startswith("7208"):
            parigi_p += 1
            break
print(f"Parigi Moutong Pengawas: {parigi_p}")
