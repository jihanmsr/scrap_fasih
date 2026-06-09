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
        
        # Test province
        prov_id = "5214ecb2-bef1-4a86-9446-451cf430928e"
        url = f"https://fasih-sm.bps.go.id/app/api/analytic/api/v2/se-2026/report-progress-listing-usaha?aggregationType=kabupaten&regionId={prov_id}&isUb=false"
        
        print("Testing:", url)
        res = await page.evaluate(f"""
            async () => {{
                try {{
                    const r = await fetch('{url}', {{ headers: {{ "X-XSRF-TOKEN": '{token}' }} }});
                    return await r.json();
                }} catch (e) {{ return {{ error: e.toString() }}; }}
            }}
        """)
        
        if "data" in res:
            total = 0
            for k in res["data"]:
                total += k.get("total_prelist", 0)
            print("Total Prelist calculated from all Kabupatens:", total)
            print(json.dumps(res, indent=2)[:500])
        else:
            print("Error:", res)

if __name__ == "__main__":
    asyncio.run(main())
