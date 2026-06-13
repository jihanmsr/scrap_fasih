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
        
        # We want to click the "Petugas" role tab button.
        # Let's find all elements containing the text "Petugas" and print their tag/class
        elements = await page.eval_on_selector_all("text=Petugas", """
            elements => elements.map(el => ({
                tagName: el.tagName,
                className: el.className,
                innerText: el.innerText,
                parentTag: el.parentElement.tagName,
                parentClass: el.parentElement.className
            }))
        """)
        
        print("\nFound 'Petugas' elements:")
        for idx, el in enumerate(elements):
            print(f"[{idx}] Tag: {el['tagName']}, Class: {el['className']}, Parent: {el['parentTag']} ({el['parentClass']})")
            
        # Let's find the one that is inside the main content (e.g., has ant-radio-button or similar class, or is not in the sidebar)
        # Usually it has ant-radio-button-wrapper or is next to Viewer
        target_idx = None
        for idx, el in enumerate(elements):
            if "ant-radio" in el['className'] or "ant-radio" in el['parentClass'] or el['tagName'] == "SPAN" and "ant-radio" in el['parentClass']:
                target_idx = idx
                print(f"Match found at index {idx} based on ant-radio class!")
                break
                
        if target_idx is None:
            # Let's click the one that is NOT a link/sidebar item (e.g., inside the main content)
            # Typically sidebar items are <a> tags or inside a menu
            for idx, el in enumerate(elements):
                if el['tagName'] != "A" and "menu" not in el['parentClass'].lower() and "sidebar" not in el['parentClass'].lower():
                    target_idx = idx
                    print(f"Match found at index {idx} based on tag/parent class!")
                    break
                    
        if target_idx is not None:
            # Click it!
            loc = page.locator("text=Petugas").nth(target_idx)
            await loc.click()
            print(f"Clicked element at index {target_idx}")
            await asyncio.sleep(3)
            await page.screenshot(path="scratch/active_page_after_role_click.png")
            print("Saved screenshot to scratch/active_page_after_role_click.png")
        else:
            print("Could not determine the correct element to click.")

asyncio.run(run())
