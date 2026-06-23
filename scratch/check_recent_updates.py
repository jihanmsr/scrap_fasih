import glob
import os
import time

script_dir = "/Users/jihanmaisaroh/scrap_fasih"
files = glob.glob(os.path.join(script_dir, "granular_assignments_se_umum_*.json"))

print(f"{'FILE':<40} | {'LAST MODIFIED':<25} | {'SIZE (MB)':<10}")
print("-" * 80)
for f in sorted(files):
    mtime = os.path.getmtime(f)
    mtime_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mtime))
    size_mb = os.path.getsize(f) / (1024 * 1024)
    print(f"{os.path.basename(f):<40} | {mtime_str:<25} | {size_mb:<10.2f}")
