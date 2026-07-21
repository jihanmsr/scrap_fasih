import json

with open("fast_petugas_progress.js", "r") as f:
    data = f.read().split("=", 1)[1].strip().strip(";")
    j = json.loads(data)

kab_codes = {
    "01": "bangkep", "02": "banggai", "03": "morowali", "04": "poso",
    "05": "donggala", "06": "tolis", "07": "buol", "08": "parigi moutong",
    "09": "touna", "10": "sigi", "11": "balut", "12": "morut", "71": "palu"
}

results = {k: {"Pencacah": set(), "Pengawas": set()} for k in kab_codes.keys()}

for role in ["Pencacah", "Pengawas"]:
    for email, details in j.get(role, {}).items():
        for reg in details.get("sls_details", {}):
            kab_code = reg[2:4]
            if kab_code in results:
                results[kab_code][role].add(email)

for code, name in kab_codes.items():
    penc = len(results[code]["Pencacah"])
    peng = len(results[code]["Pengawas"])
    print(f"{name} {peng} | {penc}")
