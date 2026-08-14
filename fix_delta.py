import json

with open("ipas_data.js", "r") as f:
    text = f.read()

prefix = "window.IPAS_DATA = "
data = json.loads(text[len(prefix):-2])

for stype in ["se_umum", "se_ub"]:
    for kab in data.get(stype, []):
        kab["yesterday_completed"] = kab.get("two_days_ago_completed", 0)
        kab["yesterday_completed_breakdown"] = kab.get("two_days_ago_completed_breakdown", {})
        kab["two_days_ago_completed"] = 0
        kab["two_days_ago_completed_breakdown"] = {}
        for kec in kab.get("kecamatan_list", []):
            kec["yesterday_completed"] = kec.get("two_days_ago_completed", 0)
            kec["yesterday_completed_breakdown"] = kec.get("two_days_ago_completed_breakdown", {})
            kec["two_days_ago_completed"] = 0
            kec["two_days_ago_completed_breakdown"] = {}

with open("ipas_data.js", "w") as f:
    f.write(prefix + json.dumps(data, indent=2) + ";\n")
print("Fixed ipas_data.js")
