import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9223")
        context = browser.contexts[0]
        page = context.pages[0]
        
        captured = []
        def handle_request(request):
            captured.append((request.method, request.url, request.post_data))
            
        page.on("request", handle_request)
        
        if len(page.frames) > 1:
            frame = page.frames[1]
            # Let's click "Pencacah" tab to trigger new API requests
            await frame.evaluate("""
                () => {
                    const elements = Array.from(document.querySelectorAll('*'));
                    const pencacah = elements.find(el => el.innerText && el.innerText.trim() === 'Pencacah');
                    if (pencacah) {
                        pencacah.click();
                        console.log("Clicked Pencacah inside the frame");
                    }
                }
            """)
            await asyncio.sleep(5)
            
            print("\n=== CAPTURED APIs WHEN CLICKING PENCACAH ===")
            for method, url, data in captured:
                if "api" in url:
                    print(f"- {method} {url}")
                    if data:
                        print(f"  Payload: {data}")
        else:
            print("No second frame found")

asyncio.run(run())
