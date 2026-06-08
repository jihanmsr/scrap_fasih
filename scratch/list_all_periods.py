import asyncio
from playwright.async_api import async_playwright
import json

async def main():
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            print("Connected to Chrome.")
        except Exception as e:
            print("Failed to connect to Chrome:", e)
            return

        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()
        
        cookies = await context.cookies()
        token = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
        if not token:
            print("XSRF-TOKEN not found.")
            return
            
        from urllib.parse import unquote
        token = unquote(token)
        
        urls = [
            "https://fasih-sm.bps.go.id/app/api/survey/api/v1/survey-periods/my",
            "https://fasih-sm.bps.go.id/app/api/survey/api/v1/survey-periods",
            "https://fasih-sm.bps.go.id/app/api/survey/api/v1/users/myinfo"
        ]
        
        for url in urls:
            print(f"\nQuerying: {url}")
            res = await page.evaluate("""
                async ({url, token}) => {
                    try {
                        const r = await fetch(url, {
                            headers: { "X-XSRF-TOKEN": token }
                        });
                        return await r.json();
                    } catch (e) {
                        return { error: e.toString() };
                    }
                }
            """, {"url": url, "token": token})
            print(json.dumps(res, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
