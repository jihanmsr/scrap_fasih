import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9223")
        context = browser.contexts[0]
        page = context.pages[0]
        
        captured = []
        context.on("request", lambda r: captured.append((r.method, r.url)))
        
        if len(page.frames) > 1:
            frame = page.frames[1]
            
            # Close modal if open first
            try:
                await frame.click("text=Close")
                await asyncio.sleep(1)
            except:
                pass
                
            # Click the proper span containing "Lainnya"
            await frame.evaluate("""
                () => {
                    const spans = Array.from(document.querySelectorAll('span'));
                    const lainnya = spans.find(el => el.innerText && el.innerText.trim().endsWith('Lainnya'));
                    if (lainnya) {
                        const parentClass = lainnya.parentElement ? lainnya.parentElement.className : '';
                        if (typeof parentClass === 'string' && parentClass.includes('cursor-pointer')) {
                            lainnya.parentElement.click();
                        } else {
                            lainnya.click();
                        }
                    }
                }
            """)
            await asyncio.sleep(4)
            
            print("\n=== CONTEXT CAPTURED REQUESTS ===")
            for method, url in captured:
                print(f"- {method} {url}")
        else:
            print("No second frame found")

asyncio.run(run())
