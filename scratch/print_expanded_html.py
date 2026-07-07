import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0]
        local_page = next((pg for pg in context.pages if "index.html" in pg.url), None)
        if local_page:
            html = await local_page.inner_html("#se_umum-stats-expanded")
            print("HTML:")
            print(html)
        else:
            print("Local page not found.")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
