import json
import re

# Read the fast_petugas_history.js file
with open('fast_petugas_history.js', 'r') as f:
    content = f.read()

# Extract the JSON object using regex
match = re.search(r'window\.PETUGAS_HISTORY_MAP\s*=\s*(\{.*?\});', content, re.DOTALL)
if match:
    data = json.loads(match.group(1))
    
    email = "elismahmudbasu@gmail.com"
    print(f"History for {email}:")
    print("-" * 50)
    
    for date in sorted(data.keys()):
        if "Pencacah" in data[date] and email in data[date]["Pencacah"]:
            stats = data[date]["Pencacah"][email]
            
            # Print the stats
            target = stats.get('target', 0)
            submitted_pencacah = stats.get('submitted_pencacah', 0)
            approved = stats.get('approved', 0)
            rejected = stats.get('rejected', 0)
            open_val = stats.get('open', 0)
            draft = stats.get('draft', 0)
            
            print(f"Date: {date}")
            print(f"  Target: {target}")
            print(f"  Open: {open_val}")
            print(f"  Draft: {draft}")
            print(f"  Submit PPL: {submitted_pencacah}")
            print(f"  Approved: {approved}")
            print(f"  Rejected: {rejected}")
            print("-" * 50)
else:
    print("Could not parse PETUGAS_HISTORY_MAP")
