import json
import os
import re

script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ipas_path = os.path.join(script_dir, "ipas_data.js")
stats_path = os.path.join(script_dir, "daily_submission_stats.json")

# 1. Read and parse ipas_data.js
with open(ipas_path, "r", encoding="utf-8") as f:
    content = f.read()

# Extract JSON from window.IPAS_DATA = { ... }
json_match = re.search(r"window\.IPAS_DATA\s*=\s*(\{.*?\});", content, re.DOTALL)
if json_match:
    ipas_data = json.loads(json_match.group(1))
else:
    print("Could not find window.IPAS_DATA in ipas_data.js")
    ipas_data = {}

# 2. Sum up fields from ipas_data['se_umum']
se_umum = ipas_data.get("se_umum", [])
print(f"=== IPAS_DATA se_umum (Count: {len(se_umum)}) ===")
total_prelist = sum(item.get("total_prelist", 0) for item in se_umum)
total_submitted = sum(item.get("total_submitted", 0) for item in se_umum)
today_completed = sum(item.get("today_completed", 0) for item in se_umum)
yesterday_completed = sum(item.get("yesterday_completed", 0) for item in se_umum)
two_days_ago_completed = sum(item.get("two_days_ago_completed", 0) for item in se_umum)

print(f"Total Target (Prelist): {total_prelist}")
print(f"Total Selesai (Submitted): {total_submitted}")
print(f"Today Completed (22/06): {today_completed}")
print(f"Yesterday Completed (21/06): {yesterday_completed}")
print(f"H-2 Completed (20/06): {two_days_ago_completed}")

# 3. Read and sum daily_submission_stats.json for 2026-06-22
if os.path.exists(stats_path):
    with open(stats_path, "r", encoding="utf-8") as f:
        stats_data = json.load(f)
    print("\n=== daily_submission_stats.json for 2026-06-22 ===")
    stats_today = [r for r in stats_data if r.get("date") == "2026-06-22" and r.get("survey_type") == "se_umum"]
    stats_yesterday = [r for r in stats_data if r.get("date") == "2026-06-21" and r.get("survey_type") == "se_umum"]
    
    print(f"Today stats rows count: {len(stats_today)}")
    print(f"Today stats sum: {sum(r.get('count', 0) for r in stats_today)}")
    print(f"Yesterday stats sum: {sum(r.get('count', 0) for r in stats_yesterday)}")
    
    # Detail per kabupaten for today in stats
    print("\nDetail per kabupaten (today stats):")
    for r in sorted(stats_today, key=lambda x: x.get('kab_name', '')):
        print(f"  {r.get('kab_name')}: {r.get('count')}")
else:
    print("\nNo daily_submission_stats.json found.")
