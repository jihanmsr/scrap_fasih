import json
import gzip
import base64
from datetime import datetime, timezone, timedelta

def get_wita_date_string(epoch_secs):
    if not epoch_secs:
        return None
    try:
        dt_utc = datetime.fromtimestamp(epoch_secs, tz=timezone.utc)
        wita_offset = timezone(timedelta(hours=8))
        dt_wita = dt_utc.astimezone(wita_offset)
        return dt_wita.strftime("%Y-%m-%d")
    except Exception:
        return None

with open("/Users/jihanmaisaroh/scrap_fasih/granular_assignments.json", "r") as f:
    data = json.load(f)

comp = data.get("compressed_data")
if comp:
    raw = json.loads(gzip.decompress(base64.b64decode(comp)).decode('utf-8'))
    targets = raw.get("targets", [])
    statuses = raw.get("statuses", [])
    
    print(f"Total targets: {len(targets)}")
    
    status_counts = {}
    date_counts = {}
    for t in targets:
        # t = [tid, code_id, name, stat_idx, pet_idx, reg_idx, epoch_mod, survey_flag]
        status = statuses[t[3]]
        status_counts[status] = status_counts.get(status, 0) + 1
        
        epoch_mod = t[6]
        if status != "OPEN" and status != "DRAFT" and epoch_mod > 0:
            date_str = get_wita_date_string(epoch_mod)
            if date_str:
                date_counts[date_str] = date_counts.get(date_str, 0) + 1
                
    print("\nTarget counts by status:")
    for status, cnt in sorted(status_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {status}: {cnt:,}")
        
    print("\nNon-OPEN/non-DRAFT targets by WITA date modified:")
    for d, cnt in sorted(date_counts.items()):
        print(f"  {d}: {cnt:,}")
else:
    print("No compressed_data found")

