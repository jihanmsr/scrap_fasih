import json
import gzip

with gzip.open("Granular_7271.json.gz", "rt", encoding="utf-8") as f:
    payload = json.load(f)

targets = payload.get("targets", [])
petugas = payload.get("petugas", [])

lia_idx = -1
for i, p in enumerate(petugas):
    if p[0] == "liapatappa@gmail.com":
        lia_idx = i
        break

if lia_idx == -1:
    print("liapatappa@gmail.com not found in granular petugas list")
else:
    count = 0
    pengawas_count = 0
    for t in targets:
        if t[4] == lia_idx:
            count += 1
        if len(t) > 8 and t[8] == lia_idx:
            pengawas_count += 1
    print(f"liapatappa@gmail.com as Pencacah: {count}")
    print(f"liapatappa@gmail.com as Pengawas: {pengawas_count}")
    print(f"Total target in Granular: {count + pengawas_count}")
