import sys

with open('scrape_users.py', 'r', encoding='utf-8') as f:
    code = f.read()

target = '''        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            print("[INFO] Terhubung ke browser aktif.")
        except Exception:
            print("[ERROR] Browser tidak jalan di debug mode. Jalankan Chrome dg --remote-debugging-port=9222")
            return
            
        context = browser.contexts[0]
        page = context.pages[0]'''

replacement = '''        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            print("[INFO] Terhubung ke browser aktif.")
            context = browser.contexts[0]
            page = context.pages[0]
        except Exception:
            print("[INFO] Meluncurkan instance Chrome baru...")
            chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            browser_context = await p.chromium.launch_persistent_context(
                user_data_dir=USER_DATA_DIR, headless=False, executable_path=chrome_path,
                args=["--disable-blink-features=AutomationControlled"]
            )
            page = browser_context.pages[0]
            browser = browser_context'''

code = code.replace(target, replacement)

with open('scrape_users.py', 'w', encoding='utf-8') as f:
    f.write(code)
print("Patched scrape_users.py!")
