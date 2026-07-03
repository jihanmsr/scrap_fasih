import openpyxl
import pandas as pd
import json

file_path = "/Users/jihanmaisaroh/scrap_fasih/Data_Mikro_Anomali_keluarga_5321_20260701_111359.xlsx"

try:
    # Read with header=3
    df = pd.read_excel(file_path, header=3)
    print("Columns in Excel:")
    print(list(df.columns))
    
    # Extract Assignment IDs and filter for UUIDs
    raw_ids = df["Assignment ID"].dropna().unique().tolist()
    
    # UUID regex validation
    import re
    uuid_pattern = re.compile(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$')
    assignment_ids = [x for x in raw_ids if uuid_pattern.match(str(x))]
    
    print(f"\nTotal Assignment IDs found (after UUID filter): {len(assignment_ids)}")
    print("Sample Assignment IDs:")
    print(assignment_ids[:10])
    
    # Save the list to ids_to_reject.json
    out_file = "scratch/ids_to_reject.json"
    with open(out_file, "w") as f:
        json.dump(assignment_ids, f, indent=2)
    print(f"\nSuccessfully saved IDs to {out_file}")




    
except Exception as e:
    print("Error reading excel:", e)
