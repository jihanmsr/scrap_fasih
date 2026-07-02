import json
with open("ipas_data.js", "r") as f:
    content = f.read()
json_str = content.replace("window.IPAS_DATA = ", "").strip()
if json_str.endswith(";"): json_str = json_str[:-1]
data = json.loads(json_str)

for survey in ["se_umum"]:
    today = 0
    yest = 0
    for kab in data.get(survey, []):
        today += kab.get("today_completed", 0)
        yest += kab.get("yesterday_completed", 0)
    print(f"Today: {today}, Yesterday: {yest}")
