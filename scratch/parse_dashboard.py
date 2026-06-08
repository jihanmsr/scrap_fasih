import json

with open("scratch/captured_dashboard.json", "r") as f:
    data = json.load(f)

print(f"Total requests: {len(data)}")
for idx, req in enumerate(data):
    url = req.get("url", "")
    method = req.get("method", "")
    print(f"[{idx}] {method} {url}")
    post_data = req.get("post_data", "")
    if post_data:
        print(f"  Payload: {post_data[:200]}")
