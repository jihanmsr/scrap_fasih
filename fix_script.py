import sys

with open("scrape_responsibility.py", "r") as f:
    lines = f.readlines()

new_lines = []
in_role_loop = False
loop_start = -1

for i, line in enumerate(lines):
    if "for role_name, role_id in ROLES.items():" in line:
        new_lines.append(line)
        new_lines.append("            for kab in kabupaten_list:\n")
        new_lines.append("                kab_id = kab['id']\n")
        new_lines.append("                kab_name = kab['name']\n")
        continue
        
    if "print(f\"\\n======================================\")" in line and "Menarik Data Role:" in lines[i+1]:
        # Indent these prints further
        new_lines.append("                print(f\"\\n======================================\")\n")
        continue
    if "print(f\"Menarik Data Role: {role_name}\")" in line:
        new_lines.append("                print(f\"Menarik Data Role: {role_name} - {kab_name}\")\n")
        continue
    if "print(f\"======================================\")" in line and "Menarik Data Role:" in lines[i-1]:
        new_lines.append("                print(f\"======================================\")\n")
        continue

    if "current_page = 0" in line and "retries =" not in line:
        new_lines.append("                current_page = 0\n")
        continue
    if "retries = 0" in line and "max_retries =" in lines[i+1]:
        new_lines.append("                retries = 0\n")
        continue
    if "max_retries = 35" in line:
        new_lines.append("                max_retries = 35\n")
        continue
    if "while True:" in line:
        new_lines.append("                while True:\n")
        continue

    if "payload = {" in line:
        in_payload = True
    
    if "\"region2Id\": None" in line:
        line = line.replace("\"region2Id\": None", "\"region2Id\": kab_id")
        
    if "for role_name" not in line and "current_page = 0" not in line:
        # Check if line is inside the while loop (indentation >= 16)
        if len(line) - len(line.lstrip()) >= 12 and "kab_name" not in line and "kab_id" not in line:
            # We need to shift everything inside the role loop by 4 spaces
            if not line.strip().startswith("for role") and not line.strip().startswith("all_results = []"):
                if line.strip() != "":
                    # If it's already indented >= 12, just add 4 spaces
                    # Wait, the original code had `current_page = 0` at indent 12.
                    # Now it should be at indent 16.
                    new_lines.append("    " + line)
                else:
                    new_lines.append(line)
        else:
            if "print(f\"    [INFO] Auto-save progresif berhasil. Data aman.\")" in line:
                new_lines.append(line.replace("berhasil", "berhasil untuk {kab_name}"))
            else:
                new_lines.append(line)

with open("scrape_responsibility.py.new", "w") as f:
    f.writelines(new_lines)
