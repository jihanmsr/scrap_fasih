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
        
        # Test level=3 for 7271
        url = "https://fasih-sm.bps.go.id/app/api/region/api/v1/region/custom-by-smallest-code-and-level?groupId=6b0b053f-aa43-4855-ac8f-26857b735c93&smallestLevelFullCode=7271&level=3"
        
        print("Testing:", url)
        res = await page.evaluate(f"""
            async () => {{
                try {{
                    const r = await fetch('{url}', {{ headers: {{ "X-XSRF-TOKEN": '{token}' }} }});
                    return await r.json();
                }} catch (e) {{ return {{ error: e.toString() }}; }}
            }}
        """)
        
        print(json.dumps(res, indent=2)[:1000])

if __name__ == "__main__":
    asyncio.run(main())
