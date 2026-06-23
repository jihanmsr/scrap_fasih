import os
import glob
from datetime import datetime

files = glob.glob("granular_assignments_se_umum_*.json")
files.sort()
print(f"{'Filename':<40} | {'Size (MB)':<10} | {'Last Modified':<20}")
print("-" * 80)
for f in files:
    mtime = os.path.getmtime(f)
    size_mb = os.path.getsize(f) / (1024 * 1024)
    dt = datetime.fromtimestamp(mtime)
    print(f"{f:<40} | {size_mb:<10.2f} | {dt.strftime('%Y-%m-%d %H:%M:%S')}")
