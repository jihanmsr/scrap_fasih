import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9223")
        context = browser.contexts[0]
        page = context.pages[0]
        
        if len(page.frames) > 1:
            frame = page.frames[1]
            print(f"Frame URL: {frame.url}")
            
            # Click the tab "Petugas" next to "Viewer" inside the frame
            # Let's find elements that contain text "Petugas"
            await frame.evaluate("""
                () => {
                    const elements = Array.from(document.querySelectorAll('*'));
                    const viewer = elements.find(el => el.innerText && el.innerText.trim() === 'Viewer');
                    if (viewer) {
                        const parent = viewer.parentElement;
                        const petugas = Array.from(parent.querySelectorAll('*')).find(el => el.innerText && el.innerText.trim() === 'Petugas' && el !== viewer);
                        if (petugas) {
                            petugas.click();
                            console.log("Clicked Petugas next to Viewer inside the frame");
                        } else {
                            console.log("Petugas sibling button not found");
                        }
                    } else {
                        console.log("Viewer button not found inside frame");
                    }
                }
            """)
            await asyncio.sleep(4)
            
            # Print the new text inside the frame
            text = await frame.evaluate("() => document.body ? document.body.innerText.substring(0, 1000) : 'No body'")
            print("Frame text after click:\n", text[:600])
            
            # Take screenshot of the page
            await page.screenshot(path="scratch/active_page_after_frame_click.png")
            print("Saved screenshot to scratch/active_page_after_frame_click.png")
        else:
            print("No second frame found")

asyncio.run(run())
