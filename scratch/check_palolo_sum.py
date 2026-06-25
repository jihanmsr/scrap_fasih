import json
import re

with open("assign_data.js", "r", encoding="utf-8") as f:
    content = f.read()

m = re.search(r"window\.ASSIGN_DATA_UMUM\s*=\s*(\[.*?\]);", content, re.DOTALL)
if m:
    data = json.loads(m.group(1))
    print(json.dumps(data[0], indent=2))
