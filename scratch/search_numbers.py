import json

with open("scratch/captured_actual.json") as f:
    data = json.load(f)

def search_val(obj, url):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ["totalHit", "recordsTotal", "recordsFiltered", "totalElements"]:
                print(f"[{url}] {k}: {v}")
            if isinstance(v, (int, float)) and 200000 <= v <= 300000:
                print(f"FOUND NUMBER {v} in key {k} for {url}")
            else:
                search_val(v, url)
    elif isinstance(obj, list):
        for item in obj:
            search_val(item, url)

for r in data:
    search_val(r["response"], r["url"])
