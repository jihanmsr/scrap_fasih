import asyncio
from playwright.async_api import async_playwright
import json

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir="/Users/jihanmaisaroh/scrap_fasih/playwright_chrome_profile",
            executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            headless=True
        )
        page = browser.pages[0]
        
        await page.goto("https://fasih-sm.bps.go.id/app/dashboard")
        await asyncio.sleep(2)
        
        cookies = await browser.cookies()
        token = ""
        for c in cookies:
            if c["name"] == "XSRF-TOKEN":
                from urllib.parse import unquote
                token = unquote(c["value"])
                break
        
        res = await page.evaluate("""
            async ({token}) => {
                const r = await fetch("https://fasih-sm.bps.go.id/app/api/survey-user/api/v1/allocations-view/by-user?surveyPeriodId=fd68e454-ba45-4b85-8205-f3bf777ded24&page=0&size=1", {
                    headers: { "X-XSRF-TOKEN": token }
                });
                return await r.json();
            }
        """, {"token": token})
        print(json.dumps(res, indent=2))
        
        await browser.close()

asyncio.run(main())
