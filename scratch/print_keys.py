import json

with open("scratch/sample_rejected_records.json", "r") as f:
    records = json.load(f)
    
if records:
    rec = records[0]
    for k, v in rec.items():
        if isinstance(v, (dict, list)):
            print(f"{k}: ({type(v).__name__} of size {len(v)})")
        else:
            print(f"{k}: {v}")
    
    print("\n--- assignmentResponsibility breakdown ---")
    for resp in rec.get("assignmentResponsibility", []):
        print(json.dumps(resp, indent=2))
else:
    print("No records found.")
