import re

with open("scrape_responsibility.py", "r") as f:
    content = f.read()

# Replace the loop start
old_loop = """        for role_name, role_id in ROLES.items():
            current_page = 0
            print(f"\\n======================================")
            print(f"Menarik Data Role: {role_name}")
            print(f"======================================")
            retries = 0
            max_retries = 35
            
            while True:"""

new_loop = """        for role_name, role_id in ROLES.items():
            for kab in kabupaten_list:
                kab_id = kab["id"]
                kab_name = kab["name"]
                
                current_page = 0
                print(f"\\n======================================")
                print(f"Menarik Data Role: {role_name} - {kab_name}")
                print(f"======================================")
                retries = 0
                max_retries = 35
                
                while True:"""

content = content.replace(old_loop, new_loop)

# Fix the region2Id in payload
content = content.replace('"region2Id": None,', '"region2Id": kab_id,')

# Indent everything inside `while True:` and the save block.
# Wait, it's easier to just do it via regex for the block.

lines = content.split('\n')
in_loop = False
for i, line in enumerate(lines):
    if "while True:" in line:
        in_loop = True
        continue
    if "print(f\"\\n[SUCCESS] Berhasil ditarik semua!\")" in line:
        in_loop = False
        
    if in_loop and line.strip() != "":
        # Indent by 4 spaces
        lines[i] = "    " + line

content = '\n'.join(lines)

# Fix the auto save print
content = content.replace('print(f"        [INFO] Auto-save progresif berhasil. Data aman.")', 'print(f"        [INFO] Auto-save progresif berhasil untuk {kab_name}. Data aman.")')

with open("scrape_responsibility_fixed.py", "w") as f:
    f.write(content)
