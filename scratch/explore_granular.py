import json
import base64
import gzip
import os

with open("granular_assignments_se_umum_7201.json", "r") as f:
    data = json.load(f)

compressed = data["compressed_data"]
raw = gzip.decompress(base64.b64decode(compressed)).decode('utf-8')
payload = json.loads(raw)

print("Keys:", list(payload.keys()))
if payload.get("targets"):
    print("Sample target:", payload["targets"][0])
if payload.get("statuses"):
    print("Statuses:", payload["statuses"])
if payload.get("petugas"):
    print("Sample petugas:", payload["petugas"][0])
