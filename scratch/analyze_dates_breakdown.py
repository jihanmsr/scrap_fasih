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
    
    analysis_dates = ["2026-06-20", "2026-06-21", "2026-06-22"]
    date_status_counts = {d: {} for d in analysis_dates}
    
    for t in targets:
        # t = [tid, code_id, name, stat_idx, pet_idx, reg_idx, epoch_mod, survey_flag]
        status = statuses[t[3]]
        epoch_mod = t[6]
        if epoch_mod > 0:
            date_str = get_wita_date_string(epoch_mod)
            if date_str in date_status_counts:
                date_status_counts[date_str][status] = date_status_counts[date_str].get(status, 0) + 1
                
    for date in analysis_dates:
        print(f"\n=== Status breakdown for modification date {date} ===")
        total_mod = sum(date_status_counts[date].values())
        print(f"Total modified targets: {total_mod:,}")
        for status, cnt in sorted(date_status_counts[date].items(), key=lambda x: x[1], reverse=True):
            pct = (cnt / total_mod * 100) if total_mod > 0 else 0
            print(f"  {status}: {cnt:,} ({pct:.2f}%)")
else:
    print("No compressed_data found")
