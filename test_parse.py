import json

try:
    with open('fast_petugas_progress.js', 'r') as f:
        content = f.read()
    
    # Extract just the JSON part
    start = content.find('{')
    if start != -1:
        end = content.rfind('}') + 1
        json_str = content[start:end]
        
        data = json.loads(json_str)
        print("Pencacah count:", len(data.get("Pencacah", {})))
        print("Pengawas count:", len(data.get("Pengawas", {})))
    else:
        print("Could not find JSON payload")
except Exception as e:
    print("Error:", e)
