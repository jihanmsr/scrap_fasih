import json
import gzip
import base64
from datetime import datetime, timezone, timedelta

def get_wita_date_string(epoch_secs):
    if not epoch_secs:
        return None
    dt_utc = datetime.fromtimestamp(epoch_secs, tz=timezone.utc)
    wita_offset = timezone(timedelta(hours=8))
    dt_wita = dt_utc.astimezone(wita_offset)
    return dt_wita.strftime("%Y-%m-%d")

with open("granular_assignments_se_umum_7205.json", "r") as f:
    data = json.load(f)

comp = data["compressed_data"]
raw = json.loads(gzip.decompress(base64.b64decode(comp)).decode('utf-8'))

targets = raw["targets"]
statuses = raw["statuses"]
regions = raw["regions"]

count_today = 0
examples = []

for t in targets:
    # t = [tid, code_id, name, stat_idx, pet_idx, reg_idx, epoch_mod, survey_flag]
    status = statuses[t[3]]
    epoch_mod = t[6]
    wita_date = get_wita_date_string(epoch_mod)
    
    if wita_date == "2026-06-22":
        count_today += 1
        if len(examples) < 10:
            examples.append({
                "id": t[0],
                "code_identity": t[1],
                "status": status,
                "epoch_mod": epoch_mod,
                "date_str": datetime.fromtimestamp(epoch_mod, tz=timezone.utc).astimezone(timezone(timedelta(hours=8))).isoformat()
            })

print(f"Total counted for today in Buol: {count_today}")
print("Samples:")
print(json.dumps(examples, indent=2))
