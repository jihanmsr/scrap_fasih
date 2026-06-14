import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9223")
        print(f"Connected to port 9223, contexts: {len(browser.contexts)}")
        
        for c_idx, context in enumerate(browser.contexts):
            print(f"Context {c_idx} has {len(context.pages)} pages")
            for p_idx, page in enumerate(context.pages):
                title = await page.title()
                print(f"  Page {p_idx}: '{title}' - {page.url}")
                
                # Check if this page contains "Viewer" or "Admin"
                content = await page.content()
                has_viewer = "Viewer" in content
                has_admin = "Admin" in content
                print(f"    has 'Viewer': {has_viewer}, has 'Admin': {has_admin}")

asyncio.run(run())
