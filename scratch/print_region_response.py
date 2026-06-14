import asyncio
import json
import logging
from playwright.async_api import async_playwright
from urllib.parse import unquote

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9223")
        context = browser.contexts[0]
        page = await context.new_page()
        await page.goto("https://fasih-sm.bps.go.id/app/dashboard", wait_until="domcontentloaded", timeout=15000)

        cookies = await context.cookies()
        token = unquote(next(c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"))

        kab_codes = ["7201", "7202", "7203", "7204", "7205", "7206", "7207", "7208", "7209", "7210", "7211", "7212", "7271"]
        print("\n=== BPS REGION API RESPONSES ===")
        for code in kab_codes:
            url = f"https://fasih-sm.bps.go.id/app/api/region/api/v1/region/custom-by-smallest-code-and-level?groupId=6b0b053f-aa43-4855-ac8f-26857b735c93&smallestLevelFullCode={code}&level=2"
            res = await page.evaluate(f"fetch('{url}', {{ headers: {{ 'X-XSRF-TOKEN': '{token}' }} }}).then(r => r.json())")
            level2 = res["data"]["level1"]["level2"]
            print(f"Queried smallestLevelFullCode={code} -> level2: code={level2['code']}, name={level2['name']}, id={level2['id']}")

if __name__ == "__main__":
    asyncio.run(main())
