import json

with open("scratch/captured_actual.json", "r") as f:
    data = json.load(f)

for idx, req in enumerate(data):
    url = req.get("url", "")
    if "datatable" in url:
        method = req.get("method", "")
        post_data = req.get("post_data", "")
        print(f"[{idx}] {method} {url}")
        if post_data:
            try:
                payload = json.loads(post_data)
                print("  Payload Keys:", list(payload.keys()))
                if "assignmentExtraParam" in payload:
                    print("  assignmentExtraParam:", payload["assignmentExtraParam"])
                # check columns search
                if "columns" in payload:
                    non_empty_searches = {}
                    for col in payload["columns"]:
                        if col.get("search") and col["search"].get("value"):
                            non_empty_searches[col["data"]] = col["search"]["value"]
                    if non_empty_searches:
                        print("  Column Searches:", non_empty_searches)
            except Exception as e:
                print("  Error parsing post_data:", e)
