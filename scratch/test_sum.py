import json
from collections import defaultdict

with open("daily_submission_stats.json", "r") as f:
    data = json.load(f)

by_date = defaultdict(int)
by_kab_today = {}

for row in data:
    if row["date"] == "2026-06-22":
        by_kab_today[row["kab_name"]] = row["count"]
    by_date[row["date"]] += row["count"]

print("SUM BY DATE:")
for d, val in sorted(by_date.items()):
    print(f"  {d}: {val}")

print("\nBY KABUPATEN FOR 2026-06-22:")
for kab, val in sorted(by_kab_today.items()):
    print(f"  {kab}: {val}")
