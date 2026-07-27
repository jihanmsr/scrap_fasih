import json, csv, os

def clean_json_str(content):
    start_brace = content.find('{')
    start_bracket = content.find('[')
    
    start = -1
    if start_brace != -1 and start_bracket != -1:
        start = min(start_brace, start_bracket)
    elif start_brace != -1:
        start = start_brace
    elif start_bracket != -1:
        start = start_bracket

    end_brace = content.rfind('}')
    end_bracket = content.rfind(']')
    
    end = -1
    if end_brace != -1 and end_bracket != -1:
        end = max(end_brace, end_bracket) + 1
    elif end_brace != -1:
        end = end_brace + 1
    elif end_bracket != -1:
        end = end_bracket + 1

    return content[start:end]

try:
    with open("daily_summary.js", "r") as f:
        content = f.read()
        ds = json.loads(clean_json_str(content))
    
    csv_file = "daily_summary.csv"
    with open(csv_file, "w", newline="") as f:
        fieldnames = ["tanggal", "kabupaten", "total_aktivitas", "total_submitted", "total_approved", "total_rejected", "total_usaha_tambahan"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in ds:
            writer.writerow(r)
    print(f"Berhasil membuat {csv_file} ({len(ds)} baris)")
except Exception as e:
    print(f"daily_summary.js error: {e}")
