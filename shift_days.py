import json
import re

file_path = '/Users/jihanmaisaroh/scrap_fasih/ipas_data.js'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

match = re.search(r'window\.IPAS_DATA\s*=\s*(\{.*\});?', content, re.DOTALL)
if not match:
    print("Could not find window.IPAS_DATA in ipas_data.js")
    exit(1)

data_str = match.group(1)
data = json.loads(data_str)

def shift_node(node):
    if "today_completed" in node:
        node["two_days_ago_completed"] = node.get("yesterday_completed", 0)
        node["two_days_ago_completed_breakdown"] = node.get("yesterday_completed_breakdown", {})
        node["yesterday_completed"] = node.get("today_completed", 0)
        node["yesterday_completed_breakdown"] = node.get("today_completed_breakdown", {})
        node["today_completed"] = 0
        node["today_completed_breakdown"] = {}

    for key, val in node.items():
        if isinstance(val, dict):
            shift_node(val)
        elif isinstance(val, list):
            for item in val:
                if isinstance(item, dict):
                    shift_node(item)

shift_node(data)

# Rewrite
new_json = json.dumps(data, indent=2, ensure_ascii=False)
new_content = content[:match.start(1)] + new_json + content[match.end(1):]

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Berhasil menggeser today_completed menjadi yesterday_completed di ipas_data.js")
