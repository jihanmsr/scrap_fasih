import json, glob, gzip, base64

with open("granular_assignments_se_umum_7206.json", "r") as f:
    d = json.load(f)

compressed = base64.b64decode(d["compressed_data"])
raw = gzip.decompress(compressed).decode("utf-8")
data = json.loads(raw)
targets = data["targets"]

assign_umum = {"7206": {"total": 0}}
for t in targets:
    assign_umum["7206"]["total"] += 1
print("Simple total:", assign_umum["7206"]["total"])

# Is there deduplication in merge_granulars.py?
