import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        for port in [9222, 9223]:
            try:
                browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
                print(f"\nPort {port} contexts: {len(browser.contexts)}")
                for i, context in enumerate(browser.contexts):
                    print(f"  Context {i} pages: {len(context.pages)}")
                    for j, page in enumerate(context.pages):
                        print(f"    Page {j}: '{page.title()}' - {page.url}")
                await browser.close()
            except Exception as e:
                print(f"Port {port} error: {e}")

asyncio.run(run())
