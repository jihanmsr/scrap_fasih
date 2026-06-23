with open('scrape_sulteng_all.py', 'r', encoding='utf-8') as f:
    code = f.read()

target = '''for s in scripts:
    subprocess.run([sys.executable, s])
print("=== SEMUA PROSES SCRAPING SELESAI ===")'''

replacement = '''for s in scripts:
    subprocess.run([sys.executable, s])

print("=== MENGGABUNGKAN SEMUA HASIL ===")
subprocess.run([sys.executable, "merge_granulars.py"])

print("=== SEMUA PROSES SCRAPING SELESAI ===")'''

if target in code:
    code = code.replace(target, replacement)
    with open('scrape_sulteng_all.py', 'w', encoding='utf-8') as f:
        f.write(code)
    print("Patched scrape_sulteng_all.py!")
else:
    print("Target not found!")
