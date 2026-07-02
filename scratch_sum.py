import json, re

with open("ipas_data.js", "r") as f:
    content = f.read()

json_str = content.replace("window.IPAS_DATA = ", "").strip()
if json_str.endswith(";"):
    json_str = json_str[:-1]

data = json.loads(json_str)

for survey in ["se_umum", "se_ub"]:
    if survey not in data: continue
    
    total_prelist = 0
    total_submitted = 0
    total_draft = 0
    total_open = 0
    
    for kab in data[survey]:
        total_prelist += kab.get("total_prelist", 0)
        total_submitted += kab.get("total_submitted", 0)
        total_draft += kab.get("total_draft", 0)
        total_open += kab.get("total_open", 0)
        
    print(f"[{survey.upper()}] Prelist: {total_prelist}, Submitted: {total_submitted}, Draft: {total_draft}, Open: {total_open}")

