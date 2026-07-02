import json
import base64
import gzip
import os
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

def main():
    script_dir = "/Users/jihanmaisaroh/scrap_fasih"
    json_path = os.path.join(script_dir, "granular_assignments_se_umum_7212.json")
    
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    compressed_bytes = base64.b64decode(data["compressed_data"])
    raw_json_str = gzip.decompress(compressed_bytes).decode('utf-8')
    payload = json.loads(raw_json_str)
    
    statuses_list = payload.get("statuses", [])
    targets = payload.get("targets", [])
    
    print(f"Total targets: {len(targets)}")
    
    valid_epoch_count = 0
    non_open_count = 0
    date_counts = {}
    
    for t in targets:
        stat_idx = t[3]
        epoch_mod = t[6]
        status_str = statuses_list[stat_idx] if stat_idx < len(statuses_list) else "UNKNOWN"
        
        if status_str != "OPEN" and status_str != "DRAFT":
            non_open_count += 1
            if epoch_mod > 0:
                valid_epoch_count += 1
                wita_date = get_wita_date_string(epoch_mod)
                if wita_date:
                    date_counts[wita_date] = date_counts.get(wita_date, 0) + 1
                    
    print(f"Non-open/draft count: {non_open_count}")
    print(f"Valid epoch count: {valid_epoch_count}")
    print("Dates breakdown:")
    for d, c in sorted(date_counts.items()):
        print(f" - {d}: {c}")

if __name__ == "__main__":
    main()
