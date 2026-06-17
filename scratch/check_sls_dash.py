import json

print("Reading assign_data.js to find SLS entries with '-' as desa_name or sls_name...")
with open("assign_data.js", "r", encoding="utf-8") as f:
    content = f.read()

# We want to extract the lists ASSIGN_SLS_DATA_UMUM and ASSIGN_SLS_DATA_UB
# Since the js contains window.ASSIGN_SLS_DATA_UMUM = [...], we can search for the json string.
# A simpler way is to find occurrences of '"desa_name": "-"' or '"sls_name": "-"' in the file.
import re
print("Searching for '-' names in general:")
print("desa_name: '-' count in general:", content.count('"desa_name": "-"'))
print("sls_name: '-' count in general:", content.count('"sls_name": "-"'))

# Let's parse JSON by extracting JSON objects
# Let's extract window.ASSIGN_SLS_DATA_UMUM
m = re.search(r'window\.ASSIGN_SLS_DATA_UMUM\s*=\s*(\[.*?\]);', content, re.DOTALL)
if m:
    data_umum = json.loads(m.group(1))
    print(f"Loaded {len(data_umum)} items from ASSIGN_SLS_DATA_UMUM")
    dash_desas = [x for x in data_umum if x.get("desa_name") == "-" or x.get("sls_name") == "-"]
    print(f"Found {len(dash_desas)} items with '-' in ASSIGN_SLS_DATA_UMUM. Sample:")
    for d in dash_desas[:5]:
        print(d)

m2 = re.search(r'window\.ASSIGN_SLS_DATA_UB\s*=\s*(\[.*?\]);', content, re.DOTALL)
if m2:
    data_ub = json.loads(m2.group(1))
    print(f"Loaded {len(data_ub)} items from ASSIGN_SLS_DATA_UB")
    dash_desas_ub = [x for x in data_ub if x.get("desa_name") == "-" or x.get("sls_name") == "-"]
    print(f"Found {len(dash_desas_ub)} items with '-' in ASSIGN_SLS_DATA_UB. Sample:")
    for d in dash_desas_ub[:5]:
        print(d)
