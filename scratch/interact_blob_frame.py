import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9223")
        context = browser.contexts[0]
        page = context.pages[0]
        print(f"Connected to page: {page.url}")
        print(f"Total frames: {len(page.frames)}")
        
        # Let's inspect the second frame (frame index 1)
        if len(page.frames) > 1:
            frame = page.frames[1]
            print(f"Frame 1 URL: {frame.url}")
            
            # Search for "Viewer" inside frame 1
            has_viewer = await frame.evaluate("""
                () => {
                    const txt = document.body ? document.body.innerText : '';
                    return txt.includes('Viewer');
                }
            """)
            print(f"Frame 1 has 'Viewer': {has_viewer}")
            
            # Print some text of frame 1
            text = await frame.evaluate("() => document.body ? document.body.innerText.substring(0, 1000) : 'No body'")
            print("Frame 1 text sample:\n", text[:500])
        else:
            print("No second frame found")

asyncio.run(run())
