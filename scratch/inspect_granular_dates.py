import os
import json
import gzip
import base64
from datetime import datetime, timezone, timedelta

script_dir = "/Users/jihanmaisaroh/scrap_fasih"
fpath = os.path.join(script_dir, "granular_assignments_se_umum_7201.json")

def get_wita_date_string(epoch_secs):
    if not epoch_secs:
        return None
    try:
        dt_utc = datetime.fromtimestamp(epoch_secs, tz=timezone.utc)
        wita_offset = timezone(timedelta(hours=8))
        dt_wita = dt_utc.astimezone(wita_offset)
        return dt_wita.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return None

if os.path.exists(fpath):
    print("Reading partitions...")
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)
    comp = data.get("compressed_data")
    if comp:
        raw = json.loads(gzip.decompress(base64.b64decode(comp)).decode('utf-8'))
        targets = raw.get("targets", [])
        statuses = raw.get("statuses", [])
        print(f"Total targets: {len(targets)}")
        
        # Count modification dates for non-OPEN targets
        date_counts = {}
        for t in targets:
            # t = [tid, code_id, name, stat_idx, pet_idx, reg_idx, epoch_mod, survey_flag]
            status = statuses[t[3]]
            epoch_mod = t[6]
            if status != "OPEN":
                date_str = get_wita_date_string(epoch_mod)
                # Just date part
                d_part = date_str.split()[0] if date_str else "None"
                date_counts[d_part] = date_counts.get(d_part, 0) + 1
                
        print("Modification Date counts for non-OPEN targets:")
        for d, count in sorted(date_counts.items(), reverse=True)[:20]:
            print(f"  {d}: {count}")
            
        # Print a few samples of 2026-06-22 modified targets
        print("\nSamples modified on 2026-06-22:")
        count = 0
        for t in targets:
            status = statuses[t[3]]
            epoch_mod = t[6]
            date_str = get_wita_date_string(epoch_mod)
            if date_str and date_str.startswith("2026-06-22"):
                print(f"  ID: {t[0]}, Code: {t[1]}, Name: {t[2]}, Status: {status}, DateModified: {date_str}")
                count += 1
                if count >= 10:
                    break
else:
    print(f"File not found: {fpath}")
