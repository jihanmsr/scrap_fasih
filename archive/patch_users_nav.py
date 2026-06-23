with open('scrape_users.py', 'r', encoding='utf-8') as f:
    code = f.read()

target = '''        context = browser.contexts[0]
        page = context.pages[0]'''

replacement = '''        context = browser.contexts[0]
        page = context.pages[0]
        print("[INFO] Navigating to FASIH...")
        try:
            await page.goto("https://fasih-sm.bps.go.id/app/surveys?page=0&perPage=10&layout=list", timeout=15000)
            await page.wait_for_load_state("networkidle")
        except:
            pass'''

if target in code:
    code = code.replace(target, replacement)
    with open('scrape_users.py', 'w', encoding='utf-8') as f:
        f.write(code)
    print("Patched scrape_users.py navigation!")
else:
    print("Target not found!")
