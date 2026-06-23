import json

with open("daily_submission_stats.json", "r") as f:
    stats = json.load(f)

daily_totals = {}
for item in stats:
    date = item.get("date")
    count = item.get("count", 0)
    if date:
        daily_totals[date] = daily_totals.get(date, 0) + count

print("Daily Totals from daily_submission_stats.json:")
for date in sorted(daily_totals.keys()):
    print(f"  {date}: {daily_totals[date]:,}")
