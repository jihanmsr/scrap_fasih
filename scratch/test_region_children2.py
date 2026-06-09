import asyncio
from playwright.async_api import async_playwright
import json

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()

        cookies = await context.cookies()
        token = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
        from urllib.parse import unquote
        token = unquote(token)
        
        kab_id = "9c9b2d79-9fb1-4ce7-b0f1-6b7bb5511beb" # Banggai Kepulauan
        
        urls = [
            f"https://fasih-sm.bps.go.id/app/api/region/api/v1/regions/children?parentId={kab_id}",
            f"https://fasih-sm.bps.go.id/app/api/region/api/v1/region/children?parentId={kab_id}",
            f"https://fasih-sm.bps.go.id/app/api/region/api/v1/regions?parentId={kab_id}",
            f"https://fasih-sm.bps.go.id/app/api/region/api/v1/region?parentId={kab_id}",
            f"https://fasih-sm.bps.go.id/app/api/region/api/v1/region/list-by-parent-id?parentId={kab_id}"
        ]
        
        for url in urls:
            print(f"\nTesting: {url}")
            res = await page.evaluate("""
                async ({url, token}) => {
                    try {
                        const r = await fetch(url, { headers: { "X-XSRF-TOKEN": token } });
                        if (!r.ok) return { status: r.status };
                        return { status: r.status, json: await r.json() };
                    } catch (e) {
                        return { error: e.toString() };
                    }
                }
            """, {"url": url, "token": token})
            print("Status:", res.get("status"))

if __name__ == "__main__":
    asyncio.run(main())
