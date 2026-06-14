import asyncio
from playwright.async_api import async_playwright
import json

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9223")
        context = browser.contexts[0]
        page = context.pages[0]
        
        if len(page.frames) > 1:
            frame = page.frames[1]
            
            # Click the proper span containing "Lainnya"
            clicked_info = await frame.evaluate("""
                () => {
                    const spans = Array.from(document.querySelectorAll('span'));
                    const lainnya = spans.find(el => el.innerText && el.innerText.trim().endsWith('Lainnya'));
                    if (lainnya) {
                        const info = {
                            tagName: lainnya.tagName,
                            className: lainnya.className,
                            innerText: lainnya.innerText,
                            parentTagName: lainnya.parentElement ? lainnya.parentElement.tagName : '',
                            parentClassName: lainnya.parentElement ? lainnya.parentElement.className : ''
                        };
                        
                        // Click either the span or its clickable parent div
                        const parentClass = lainnya.parentElement ? lainnya.parentElement.className : '';
                        if (typeof parentClass === 'string' && parentClass.includes('cursor-pointer')) {
                            lainnya.parentElement.click();
                            info.clickedParent = true;
                        } else {
                            lainnya.click();
                            info.clickedParent = false;
                        }
                        return info;
                    }
                    return null;
                }
            """)
            print("Clicked element info:", json.dumps(clicked_info, indent=2))
            await asyncio.sleep(3)
            
            # Now let's see if there is any popover or dialog on the screen!
            # Let's check for absolute elements or modal/dialog elements inside Frame 1
            popovers = await frame.evaluate("""
                () => {
                    const results = [];
                    const all = document.querySelectorAll('*');
                    for (let el of all) {
                        const style = window.getComputedStyle(el);
                        const className = el.className;
                        const classStr = typeof className === 'string' ? className : '';
                        
                        if ((style.position === 'absolute' || style.position === 'fixed' || classStr.includes('dialog') || classStr.includes('popover') || classStr.includes('modal')) && el.innerText && el.innerText.trim().length > 0) {
                            results.push({
                                tagName: el.tagName,
                                className: classStr,
                                text: el.innerText.substring(0, 500)
                            });
                        }
                    }
                    return results;
                }
            """)
            print("\n=== Popovers/Modals in Frame 1 ===")
            print(json.dumps(popovers, indent=2))
            
            # Let's take a screenshot
            await page.screenshot(path="scratch/active_page_after_real_lainnya_click.png")
            print("Saved screenshot to scratch/active_page_after_real_lainnya_click.png")
        else:
            print("No second frame found")

asyncio.run(run())
