import json, re

with open("ipas_data.js", "r", encoding="utf-8") as f:
    js_content = f.read()
    json_str = js_content.replace("window.IPAS_DATA = ", "").strip().rstrip(";")
    final_js_obj = json.loads(json_str)

new_se_umum = final_js_obj["se_umum"]
for kab in new_se_umum:
    kab_clean = re.sub(r'\[\d+\]', '', kab["kabupaten"]).replace('[','').replace(']','').strip()
    kab_clean = " ".join([w for w in kab_clean.split() if not (w.isdigit() or w.startswith("72"))]).upper().strip()
    print(f"Original: {kab['kabupaten']} -> Cleaned: '{kab_clean}'")
