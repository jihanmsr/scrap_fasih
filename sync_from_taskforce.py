import requests

files_to_sync = [
    "ipas_data.js",
    "daily_submission_stats.js",
    "daily_summary.js",
    "fast_petugas_progress.js",
    "fast_petugas_history.js",
    "fast_master_assign_data.js",
    "assign_data.js",
    "mysql_data.js",
    "rekon_data.js"
]

base_url = "https://taskforce.bpssulteng.id/"

for filename in files_to_sync:
    try:
        url = base_url + filename
        print(f"Downloading {filename}...")
        r = requests.get(url)
        if r.status_code == 200:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(r.text)
            print(f"  [SUCCESS] {filename} saved.")
        else:
            print(f"  [ERROR] {filename} returned status {r.status_code}")
    except Exception as e:
        print(f"  [ERROR] Failed to download {filename}: {e}")

print("Sync completed!")
