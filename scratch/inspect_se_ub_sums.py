import json

with open("/Users/jihanmaisaroh/scrap_fasih/ipas_data.js", "r") as f:
    content = f.read()

json_str = content.split("window.IPAS_DATA =")[1].strip()
if json_str.endswith(";"):
    json_str = json_str[:-1]

data = json.loads(json_str)

sums = {
    "total_prelist": 0,
    "total_draft": 0,
    "total_open": 0,
    "total_submitted": 0,
    "total_submitted_pencacah": 0,
    "total_submitted_respondent": 0,
    "total_approved": 0,
    "total_rejected": 0,
    "new_usaha_overall": 0,
    "new_rumah_overall": 0
}

for item in data.get("se_ub", []):
    for key in sums.keys():
        sums[key] += item.get(key, 0)

print(sums)
