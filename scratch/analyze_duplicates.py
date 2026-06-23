import json
import re

def analyze_data():
    with open('/Users/jihanmaisaroh/scrap_fasih/data.js', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract JSON part from data.js (which looks like: window.EMAIL_DATA = [...];)
    match = re.search(r'window\.EMAIL_DATA\s*=\s*(\[.*\]);', content, re.DOTALL)
    if not match:
        print("Could not find window.EMAIL_DATA in data.js")
        return
        
    data = json.loads(match.group(1))
    print(f"Total rows in data.js: {len(data)}")
    
    unique_codes = set()
    for row in data:
        code = row.get('code')
        unique_codes.add(code)
        
    print(f"Total unique company codes: {len(unique_codes)}")

if __name__ == '__main__':
    analyze_data()
