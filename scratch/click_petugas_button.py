import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9223")
        context = browser.contexts[0]
        page = context.pages[0]
        print(f"Connected to page: {page.url}")
        
        # We need to click the middle button "Petugas" in the row (Admin | Viewer | Petugas)
        # Let's list all elements containing text "Petugas" first
        elements = await page.eval_on_selector_all("text=Petugas", """
            elements => elements.map(el => ({
                tagName: el.tagName,
                className: el.className,
                innerText: el.innerText,
                parentTag: el.parentElement.tagName,
                parentClass: el.parentElement.className
            }))
        """)
        
        print("\nAll 'Petugas' elements found:")
        for idx, el in enumerate(elements):
            print(f"[{idx}] {el['tagName']} - '{el['innerText']}' - Class: {el['className']}, Parent: {el['parentTag']} ({el['parentClass']})")
            
        # Let's find the one that is likely the button. It might have parent class with button or radio or similar,
        # or it is a button/div itself. Let's find:
        # In the screenshot, it is a row of tabs/buttons: Admin | Viewer | Petugas.
        # Let's click the one that has text "Petugas" and is part of that group.
        # Often it is a button or span inside a div.
        # Let's try to click: page.locator("button:has-text('Petugas')") or similar.
        # Let's try to target the button using page.locator("text=Petugas").nth(...)
        # Let's try clicking the button by locating elements that are buttons or divs.
        
        # Let's click it based on class or content.
        # In active_page_role_petugas.png, it is a horizontal list: Admin | Viewer | Petugas.
        # Let's click it:
        try:
            # We can find all elements with text "Petugas" and check if it's the one next to Viewer
            # The Viewer button text is "Viewer". The sibling button text is "Petugas".
            # Let's use Playwright locator to click the button:
            # page.locator("xpath=//div[contains(text(), 'Viewer')]/following-sibling::div[contains(text(), 'Petugas')]")
            # Or we can just click "text=Petugas" but with a more specific locator:
            # e.g., page.locator(".btn:has-text('Petugas')") or page.locator("button:has-text('Petugas')")
            # Let's evaluate clicking in javascript:
            await page.evaluate("""
                const els = Array.from(document.querySelectorAll('*'));
                // Find element next to Viewer
                const viewerEl = els.find(el => el.innerText && el.innerText.trim() === 'Viewer');
                if (viewerEl) {
                    // Look for parent or siblings
                    const parent = viewerEl.parentElement;
                    const petugasEl = Array.from(parent.querySelectorAll('*')).find(el => el.innerText && el.innerText.trim() === 'Petugas' && el !== viewerEl);
                    if (petugasEl) {
                        petugasEl.click();
                        console.log("Clicked Petugas next to Viewer in JS");
                    }
                }
            """)
            print("Evaluated JS click next to Viewer")
        except Exception as e:
            print("Error executing JS click:", e)
            
        await page.wait_for_timeout(4000)
        await page.screenshot(path="scratch/active_page_after_petugas_click.png")
        print("Saved screenshot to scratch/active_page_after_petugas_click.png")

asyncio.run(run())
