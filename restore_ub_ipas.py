import json
import re
import subprocess

# Get old ipas_data.js from git
try:
    old_content_bytes = subprocess.check_output(['git', 'show', 'HEAD:ipas_data.js'])
    old_content = old_content_bytes.decode('utf-8')
    match = re.search(r'window\.IPAS_DATA\s*=\s*(\{.*?\});', old_content, re.DOTALL)
    if not match:
        print("Could not parse old ipas_data.js")
        exit(1)
    old_ipas = json.loads(match.group(1))
except Exception as e:
    print(f"Error reading from git: {e}")
    exit(1)

# Get current ipas_data.js
try:
    with open("ipas_data.js", "r", encoding="utf-8") as f:
        curr_content = f.read()
    match2 = re.search(r'window\.IPAS_DATA\s*=\s*(\{.*?\});', curr_content, re.DOTALL)
    if not match2:
        print("Could not parse current ipas_data.js")
        exit(1)
    curr_ipas = json.loads(match2.group(1))
except Exception as e:
    print(f"Error reading current ipas_data.js: {e}")
    exit(1)

# Merge back keys from old_ipas that are missing in curr_ipas (like se_ub, etc)
for key, val in old_ipas.items():
    if key not in curr_ipas:
        curr_ipas[key] = val

new_json = json.dumps(curr_ipas, indent=2, ensure_ascii=False)
new_content = curr_content[:match2.start(1)] + new_json + curr_content[match2.end(1):]

with open("ipas_data.js", "w", encoding="utf-8") as f:
    f.write(new_content)

print("Berhasil mengembalikan data UB dan data referensi lainnya ke ipas_data.js!")
