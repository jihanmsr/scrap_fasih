import os
import json
import gzip
import base64
import glob
from collections import Counter
from datetime import datetime, timezone, timedelta

script_dir = "/Users/jihanmaisaroh/scrap_fasih"

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

files = glob.glob(os.path.join(script_dir, "granular_assignments_*.json"))
status_counter = Counter()

for fpath in files:
    try:
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
        comp = data.get("compressed_data")
        if not comp: continue
        
        raw = json.loads(gzip.decompress(base64.b64decode(comp)).decode('utf-8'))
        targets = raw.get("targets", [])
        statuses = raw.get("statuses", [])
        
        for t in targets:
            status = statuses[t[3]]
            epoch_mod = t[6]
            if epoch_mod > 0:
                d_part = get_wita_date_string(epoch_mod)
                if d_part == "2026-06-22":
                    status_counter[status] += 1
    except Exception as e:
        print(f"Error processing {fpath}: {e}")

print("Statuses of all targets modified on 2026-06-22:")
for status, count in status_counter.most_common():
    print(f"  {status}: {count}")
