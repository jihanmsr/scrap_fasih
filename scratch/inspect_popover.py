import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9223")
        context = browser.contexts[0]
        page = context.pages[0]
        
        if len(page.frames) > 1:
            frame = page.frames[1]
            
            # Click "Lainnya" inside the frame
            clicked = await frame.evaluate("""
                () => {
                    const elements = Array.from(document.querySelectorAll('*'));
                    const lainnya = elements.find(el => el.innerText && el.innerText.trim().endsWith('Lainnya'));
                    if (lainnya) {
                        lainnya.click();
                        return true;
                    }
                    return false;
                }
            """)
            print(f"Clicked 'Lainnya': {clicked}")
            await asyncio.sleep(2)
            
            # Now inspect elements in frame 1
            popovers = await frame.evaluate("""
                () => {
                    const results = [];
                    // Find elements that are absolutely or fixed positioned
                    const all = document.querySelectorAll('*');
                    for (let el of all) {
                        const style = window.getComputedStyle(el);
                        if ((style.position === 'absolute' || style.position === 'fixed') && el.innerText && el.innerText.trim().length > 0) {
                            results.push({
                                tagName: el.tagName,
                                className: el.className,
                                text: el.innerText.substring(0, 500),
                                id: el.id
                            });
                        }
                    }
                    return results;
                }
            """)
            print("\n=== Popovers inside Frame 1 ===")
            import json
            print(json.dumps(popovers, indent=2))
            
            # Let's also check the main page body
            main_popovers = await page.evaluate("""
                () => {
                    const results = [];
                    const all = document.querySelectorAll('*');
                    for (let el of all) {
                        const style = window.getComputedStyle(el);
                        if ((style.position === 'absolute' || style.position === 'fixed') && el.innerText && el.innerText.trim().length > 0) {
                            results.push({
                                tagName: el.tagName,
                                className: el.className,
                                text: el.innerText.substring(0, 500)
                            });
                        }
                    }
                    return results;
                }
            """)
            print("\n=== Popovers in Main Page ===")
            print(json.dumps(main_popovers, indent=2))
            
        else:
            print("No second frame found")

asyncio.run(run())
