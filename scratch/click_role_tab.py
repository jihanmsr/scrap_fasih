import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9223")
        context = browser.contexts[0]
        
        page = None
        for p_page in context.pages:
            if "fasih-sm.bps.go.id" in p_page.url:
                page = p_page
                break
        if not page:
            print("No page found")
            return
            
        print(f"Connected to page: {page.url}")
        
        # 1. Close the modal by pressing Escape
        print("Closing active modal...")
        await page.keyboard.press("Escape")
        await asyncio.sleep(1)
        
        # 2. Find all buttons containing the text "Petugas"
        buttons = page.locator("button")
        count = await buttons.count()
        print(f"Found {count} total buttons")
        
        for i in range(count):
            btn = buttons.nth(i)
            text = await btn.inner_text()
            # We want the button whose exact text is "Petugas"
            if text.strip() == "Petugas" and await btn.is_visible():
                await btn.click()
                print(f"Clicked the exact Petugas button at index {i}!")
                break
                
        await asyncio.sleep(4)
        
        # Take a screenshot to verify
        await page.screenshot(path="scratch/active_page_petugas_selected.png")
        print("Screenshot saved to scratch/active_page_petugas_selected.png")

asyncio.run(run())
