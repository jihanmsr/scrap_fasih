import json

with open("sync_data.js", "r") as f:
    content = f.read().replace("window.SUPERSET_SYNC_SLS_DATA = ", "")
    if content.endswith(";\n"):
        content = content[:-2]

data = json.loads(content)
print("Total assign:", sum(d.get("assign", 0) for d in data))
print("Total sync:", sum(d.get("sync_count", 0) for d in data))
print("Total SLS:", len(data))
