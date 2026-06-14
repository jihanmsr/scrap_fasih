import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9223")
        context = browser.contexts[0]
        page = context.pages[0]
        print(f"Connected to page: {page.url}")
        
        # Click the main "Petugas" tab next to "Viewer"
        # In the screenshot, the tab is: <div class="...">Petugas</div>
        # Let's try to click it. We can target it using text:
        # Wait, there is a sidebar button "Petugas" and the top tab "Petugas".
        # Let's locate the top tab. It is an element with text "Petugas" inside the tab bar.
        # Let's click it:
        try:
            await page.click("div.ant-radio-group >> text=Petugas")
            print("Clicked Petugas radio tab")
        except Exception as e:
            try:
                await page.click("text=Petugas")
                print("Clicked text=Petugas")
            except Exception as e2:
                print("Failed to click Petugas:", e2)
                
        await page.wait_for_timeout(3000)
        
        # Let's print all visible buttons or subtabs to see what is available
        buttons = await page.eval_on_selector_all("button, div.ant-radio-button-wrapper, a", """
            elements => elements.map(el => ({
                text: el.innerText,
                tagName: el.tagName,
                className: el.className
            }))
        """)
        print("\nAll buttons/tabs on page:")
        for btn in buttons:
            if btn['text']:
                print(f"- [{btn['tagName']}] {btn['text']} (Class: {btn['className']})")
                
        await page.screenshot(path="scratch/active_page_role_petugas.png")
        print("Screenshot saved to scratch/active_page_role_petugas.png")

asyncio.run(run())
