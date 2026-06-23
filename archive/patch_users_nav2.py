with open('scrape_users.py', 'r', encoding='utf-8') as f:
    code = f.read()

target = '''        users_umum = await fetch_users(page, SE_UMUM_PERIOD, "SE Umum")'''

replacement = '''        print("[INFO] Navigating to FASIH...")
        try:
            await page.goto("https://fasih-sm.bps.go.id/app/surveys", timeout=15000)
            await page.wait_for_load_state("networkidle", timeout=5000)
        except Exception as e:
            print(f"[WARNING] Navigation timeout/error: {e}")
            
        users_umum = await fetch_users(page, SE_UMUM_PERIOD, "SE Umum")'''

if target in code:
    code = code.replace(target, replacement)
    with open('scrape_users.py', 'w', encoding='utf-8') as f:
        f.write(code)
    print("Patched scrape_users.py navigation!")
else:
    print("Target not found!")
