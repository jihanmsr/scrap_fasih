import json
import re

# Read ipas_data.js and extract the JSON object
with open("/Users/jihanmaisaroh/scrap_fasih/ipas_data.js", "r") as f:
    content = f.read()

# Extract the JSON part after window.IPAS_DATA = 
json_str = content.split("window.IPAS_DATA =")[1].strip()
if json_str.endswith(";"):
    json_str = json_str[:-1]

data = json.loads(json_str)

# Calculate sum of today_completed, yesterday_completed, two_days_ago_completed
sum_today = 0
sum_yesterday = 0
sum_two_days = 0

for item in data.get("se_umum", []):
    sum_today += item.get("today_completed", 0)
    sum_yesterday += item.get("yesterday_completed", 0)
    sum_two_days += item.get("two_days_ago_completed", 0)

print(f"SE Umum:")
print(f"  Sum today_completed: {sum_today}")
print(f"  Sum yesterday_completed: {sum_yesterday}")
print(f"  Sum two_days_ago_completed: {sum_two_days}")
