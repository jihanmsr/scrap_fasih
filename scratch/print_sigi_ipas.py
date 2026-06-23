import json
import re

# Read ipas_data.js
with open("/Users/jihanmaisaroh/scrap_fasih/ipas_data.js", "r") as f:
    content = f.read()

# Find the json inside window.IPAS_DATA or equivalent
# Usually it is written as `var IPAS_DATA = { ... }` or `const IPAS_DATA = { ... }` or JSON.
# Let's extract the array or object
# Let's look for "[10] SIGI"
match = re.search(r'\{\s*"kabupaten":\s*"\[10\]\s*SIGI".*?\}', content, re.DOTALL)
if match:
    print(match.group(0))
else:
    # Just print lines around "SIGI" in ipas_data.js
    lines = content.splitlines()
    for idx, line in enumerate(lines):
        if "[10] SIGI" in line:
            for l in lines[max(0, idx-5):min(len(lines), idx+30)]:
                print(l)
            break
