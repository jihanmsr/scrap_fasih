import json, re, datetime

def get_wita_date(iso_str, offset_days=0):
    dt = datetime.datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    dt += datetime.timedelta(days=offset_days)
    # WITA is UTC+8, assume iso_str is already local or we just use it directly
    return dt.strftime("%Y-%m-%d")

with open("ipas_data.js", "r") as f:
    content = f.read()
match = re.search(r'window\.IPAS_DATA\s*=\s*(\{.*?\});', content, re.DOTALL)
ipas_data = json.loads(match.group(1))

updated_at = ipas_data.get("updated_at", datetime.datetime.now().isoformat())
today_str = get_wita_date(updated_at, 0)
yest_str = get_wita_date(updated_at, -1)
lusa_str = get_wita_date(updated_at, -2)

stats = []

def clean_kab(name):
    name = re.sub(r'\[\d+\]', '', name).replace('[', '').replace(']', '').strip()
    return " ".join([w for w in name.split() if not (w.isdigit() or w.startswith("72"))]).upper()

for survey_type in ["se_umum", "se_ub"]:
    for kab in ipas_data.get(survey_type, []):
        kab_name = clean_kab(kab.get("kabupaten", ""))
        if kab.get("today_completed"):
            stats.append({"date": today_str, "kab_name": kab_name, "survey_type": survey_type, "count": kab["today_completed"]})
        if kab.get("yesterday_completed"):
            stats.append({"date": yest_str, "kab_name": kab_name, "survey_type": survey_type, "count": kab["yesterday_completed"]})
        if kab.get("two_days_ago_completed"):
            stats.append({"date": lusa_str, "kab_name": kab_name, "survey_type": survey_type, "count": kab["two_days_ago_completed"]})

# Read existing stats to not overwrite old history
existing = []
try:
    with open("daily_submission_stats.js", "r") as f:
        c = f.read()
        m = re.search(r'window\.DAILY_SUBMISSION_STATS\s*=\s*(\[.*?\]);', c, re.DOTALL)
        if m:
            existing = json.loads(m.group(1))
except:
    pass

# Filter out the 3 days from existing
new_dates = {today_str, yest_str, lusa_str}
filtered_existing = [x for x in existing if x.get("date") not in new_dates]
final_stats = filtered_existing + stats

with open("daily_submission_stats.js", "w") as f:
    f.write(f"window.DAILY_SUBMISSION_STATS = {json.dumps(final_stats, indent=2)};\n")

print("Fixed daily_submission_stats.js")
