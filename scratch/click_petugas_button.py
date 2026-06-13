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
        
        # We want to click the BUTTON with text "Petugas"
        # Let's find all buttons containing the text "Petugas"
        buttons = page.locator("button:has-text('Petugas')")
        count = await buttons.count()
        print(f"Found {count} buttons with text 'Petugas'")
        
        for i in range(count):
            btn = buttons.nth(i)
            text = await btn.inner_text()
            print(f"Button {i}: text={text}, visible={await btn.is_visible()}")
            # Click it if visible
            if await btn.is_visible():
                await btn.click()
                print(f"Clicked button {i}!")
                break
                
        await asyncio.sleep(4)
        await page.screenshot(path="scratch/active_page_after_button_click.png")
        print("Screenshot saved to scratch/active_page_after_button_click.png")

asyncio.run(run())
