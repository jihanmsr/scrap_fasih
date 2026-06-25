import asyncio
import os
from playwright.async_api import async_playwright
from urllib.parse import unquote

async def run():
    async with async_playwright() as p:
        user_data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "chrome_user_data")
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir, headless=False, 
            executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            no_viewport=True
        )
        page = browser.pages[0] if browser.pages else await browser.new_page()
        await page.goto("https://fasih-sm.bps.go.id/assignment/list/all-user")
        await asyncio.sleep(2)
        
        cookies = await browser.cookies()
        token = ""
        for c in cookies:
            if c["name"] == "XSRF-TOKEN":
                token = unquote(c["value"])
                
        level = 5
        group_id = "5214ecb2-bef1-4a86-9446-451cf430928e" # SULAWESI TENGAH
        parent_code_key = "level4FullCode"
        parent_code_val = "7201030017" # KOMBUTOKAN
        
        url = f"https://fasih-sm.bps.go.id/app/api/region/api/v1/region/level{level}?groupId={group_id}&{parent_code_key}={parent_code_val}"
        print(f"Fetching URL: {url}")
        
        res = await page.evaluate("""
            async ({url, token}) => {
                try {
                    const r = await fetch(url, {
                        method: "GET",
                        headers: { "X-XSRF-TOKEN": token, "Accept": "application/json" }
                    });
                    if (!r.ok) return { _error: `HTTP ${r.status}` };
                    return await r.json();
                } catch (e) {
                    return { _error: e.toString() };
                }
            }
        """, {"url": url, "token": token})
        
        print(f"Result: {res}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
