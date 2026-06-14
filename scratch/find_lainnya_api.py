import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9223")
        context = browser.contexts[0]
        page = context.pages[0]
        
        captured = []
        def handle_request(request):
            captured.append((request.method, request.url))
            
        page.on("request", handle_request)
        
        if len(page.frames) > 1:
            frame = page.frames[1]
            
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
            
            print("\n=== CAPTURED REQUESTS ===")
            for method, url in captured:
                print(f"- {method} {url}")
        else:
            print("No second frame found")

asyncio.run(run())
