import csv
import glob
import os

files = glob.glob("fast_petugas_all_2026-*.csv")

for csv_filename in sorted(files):
    unique_rows = []
    seen = set()
    
    with open(csv_filename, 'r') as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if i == 0:
                unique_rows.append(row)
                continue
            
            # Use Email + Role + Region Code for uniqueness
            if len(row) > 2:
                key = (row[0], row[1], row[2])
                if key not in seen:
                    seen.add(key)
                    unique_rows.append(row)
            else:
                unique_rows.append(row)

    with open(csv_filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(unique_rows)
        
    print(f"Deduplicated {csv_filename}: saved {len(unique_rows)} rows.")
