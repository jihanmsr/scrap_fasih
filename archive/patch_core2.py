with open('scrape_granular_core.py', 'r', encoding='utf-8') as f:
    code = f.read()

target = '''    print("[START] Mulai proses penarikan seluruh data secara granular...")'''

replacement = '''    print("[START] Mulai proses penarikan seluruh data secara granular...")
    global users_mapping
    users_mapping = {}
    try:
        import json
        with open("users_mapping.json", "r", encoding="utf-8") as f:
            users_mapping = json.load(f)
    except:
        pass'''

if target in code:
    code = code.replace(target, replacement)
    with open('scrape_granular_core.py', 'w', encoding='utf-8') as f:
        f.write(code)
    print("Patched users_mapping in scrape_granular_core.py!")
else:
    print("Target not found!")
