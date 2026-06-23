with open('scrape_users.py', 'r', encoding='utf-8') as f:
    code = f.read()

target = '''        except Exception:
            print("[INFO] Meluncurkan instance Chrome baru...")
            chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            browser_context = await p.chromium.launch_persistent_context(
                user_data_dir=USER_DATA_DIR, headless=False, executable_path=chrome_path,
                args=["--disable-blink-features=AutomationControlled"]
            )
            page = browser_context.pages[0]
            browser = browser_context'''

replacement = '''        except Exception:
            print("[ERROR] Chrome belum dibuka di port 9222!")
            return'''

if target in code:
    code = code.replace(target, replacement)
    with open('scrape_users.py', 'w', encoding='utf-8') as f:
        f.write(code)
    print("Reverted scrape_users.py to CDP only!")
else:
    print("Target not found!")
