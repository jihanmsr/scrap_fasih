import asyncio
import json
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = None
        for port in [9223, 9222]:
            try:
                browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
                break
            except Exception:
                pass
        if not browser:
            print("Failed to connect to browser CDP")
            return
        
        context = browser.contexts[0]
        page = None
        for p_page in context.pages:
            if "fasih-dashboard.bps.go.id" in p_page.url:
                page = p_page
                break
        if not page:
            page = await context.new_page()
            await page.goto("https://fasih-dashboard.bps.go.id/superset/dashboard/se2026/", wait_until="domcontentloaded")
            await asyncio.sleep(5)
            
        print(f"Connected to page: {page.url}")
        
        js_code = """
            async () => {
                const url = 'https://fasih-dashboard.bps.go.id/api/v1/dataset/7047';
                try {
                    const r = await fetch(url);
                    if (!r.ok) return { error: `HTTP ${r.status}: ${await r.text()}` };
                    return await r.json();
                } catch (e) {
                    return { error: e.toString() };
                }
            }
        """
        res = await page.evaluate(js_code)
        if "error" in res:
            print("Error:", res["error"])
        else:
            cols = res.get("result", {}).get("columns", [])
            print(f"Found {len(cols)} columns:")
            for c in cols:
                print(f" - Name: {c.get('column_name')}, Type: {c.get('type')}, Expression: {c.get('expression')}")

if __name__ == "__main__":
    asyncio.run(main())
