import asyncio
from playwright.async_api import async_playwright
import json

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()
        
        # Navigate if needed
        if "fasih-sm.bps.go.id" not in page.url:
            await page.goto("https://fasih-sm.bps.go.id/app/dashboard")

        cookies = await context.cookies("https://fasih-sm.bps.go.id")
        token = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
        from urllib.parse import unquote
        token = unquote(token) if token else ""
        
        url = "https://fasih-sm.bps.go.id/app/api/region/api/v1/region/custom-by-smallest-code-and-level?groupId=6b0b053f-aa43-4855-ac8f-26857b735c93&smallestLevelFullCode=7201&level=2"
        
        res = await page.evaluate("""
            async ({url, token}) => {
                const r = await fetch(url, { headers: { "X-XSRF-TOKEN": token } });
                if (!r.ok) return { status: r.status, text: await r.text() };
                return { status: r.status, json: await r.json() };
            }
        """, {"url": url, "token": token})
        
        print(json.dumps(res, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
