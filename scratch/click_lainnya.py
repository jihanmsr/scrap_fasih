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
            # First let's click "Pengawas" tab to ensure we see the row with "42 Lainnya"
            await frame.evaluate("""
                () => {
                    const elements = Array.from(document.querySelectorAll('*'));
                    const pengawas = elements.find(el => el.innerText && el.innerText.trim() === 'Pengawas');
                    if (pengawas) pengawas.click();
                }
            """)
            await asyncio.sleep(2)
            
            # Now let's click "Lainnya"
            clicked = await frame.evaluate("""
                () => {
                    const elements = Array.from(document.querySelectorAll('*'));
                    const lainnya = elements.find(el => el.innerText && el.innerText.includes('Lainnya'));
                    if (lainnya) {
                        lainnya.click();
                        return true;
                    }
                    return false;
                }
            """)
            print(f"Clicked 'Lainnya': {clicked}")
            await asyncio.sleep(4)
            
            print("\n=== CAPTURED APIs WHEN CLICKING LAINNYA ===")
            for method, url, data in captured:
                if "api" in url:
                    print(f"- {method} {url}")
                    if data:
                        print(f"  Payload: {data}")
                        
            # Save screenshot of the dialog/modal
            await page.screenshot(path="scratch/active_page_after_lainnya_click.png")
            print("Saved screenshot to scratch/active_page_after_lainnya_click.png")
        else:
            print("No second frame found")

asyncio.run(run())
