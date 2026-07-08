import os
import datetime

files = [
    "/Users/jihanmaisaroh/scrap_fasih/Progres Sulteng Fasih SM SE2026.xlsx",
    "/Users/jihanmaisaroh/scrap_fasih/progress-assignment-fd68e454-ba45-4b85-8205-f3bf777ded24 (2).csv",
    "/Users/jihanmaisaroh/scrap_fasih/progress-assignment-fd68e454-ba45-4b85-8205-f3bf777ded24 (3).csv",
    "/Users/jihanmaisaroh/scrap_fasih/progress-assignment-fd68e454-ba45-4b85-8205-f3bf777ded24.csv"
]

for f in files:
    if os.path.exists(f):
        mtime = os.path.getmtime(f)
        dt = datetime.datetime.fromtimestamp(mtime)
        print(f"File: {os.path.basename(f)}")
        print(f"  Mod time: {dt.isoformat()}")
        print(f"  Size: {os.path.getsize(f)} bytes")
