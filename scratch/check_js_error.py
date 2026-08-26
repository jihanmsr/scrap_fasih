from playwright.sync_api import sync_playwright

def run(playwright):
    browser = playwright.chromium.launch()
    page = browser.new_page()
    page.on("console", lambda msg: print(f"CONSOLE {msg.type}: {msg.text}"))
    page.on("pageerror", lambda err: print(f"PAGE ERROR: {err}"))
    
    try:
        page.goto("file:///Users/jihanmaisaroh/scrap_fasih/index.html")
        page.wait_for_timeout(3000)
    except Exception as e:
        print(f"Error loading page: {e}")
    browser.close()

with sync_playwright() as playwright:
    run(playwright)
