import asyncio
from playwright.async_api import async_playwright
import json

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        page = None
        for pg in context.pages:
            if "fasih-sm.bps.go.id" in pg.url:
                page = pg
                break
        
        if not page:
            print("No active page found. Navigating to fasih...")
            page = await context.new_page()
            await page.goto("https://fasih-sm.bps.go.id/app/dashboard")
            await page.wait_for_timeout(3000)

        cookies = await context.cookies("https://fasih-sm.bps.go.id")
        token = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
        from urllib.parse import unquote
        token = unquote(token) if token else ""
        
        print("XSRF-TOKEN:", token[:10] + "...")
        
        uuid_map = await page.evaluate("""
            async (token) => {
                const kabCodes = ["7201", "7202", "7203", "7204", "7205", "7206", "7207", "7208", "7209", "7210", "7211", "7212", "7271"];
                const map = {};
                for (const code of kabCodes) {
                    try {
                        const url = `https://fasih-sm.bps.go.id/app/api/region/api/v1/region/custom-by-smallest-code-and-level?groupId=6b0b053f-aa43-4855-ac8f-26857b735c93&smallestLevelFullCode=${code}&level=2`;
                        const res = await fetch(url, { headers: { "X-XSRF-TOKEN": token } });
                        const json = await res.json();
                        if (json && json.success && json.data) {
                            const level2 = json.data.level1.level2;
                            if (level2) {
                                map[level2.code] = { "id": level2.id, "name": level2.name };
                            }
                        }
                    } catch (e) {}
                }
                return map;
            }
        """, token)
        
        print("Resolved map:")
        print(json.dumps(uuid_map, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
