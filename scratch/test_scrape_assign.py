import asyncio
from playwright.async_api import async_playwright
import json

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        
        # Create a fresh new tab on BPS to ensure same-origin and cookies
        page = await context.new_page()
        await page.goto("https://fasih-sm.bps.go.id/app/dashboard")
        await page.wait_for_timeout(3000)

        cookies = await context.cookies("https://fasih-sm.bps.go.id")
        token = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
        from urllib.parse import unquote
        token = unquote(token) if token else ""
        
        print("XSRF-TOKEN:", token[:10] + "...")
        
        url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/report-user-assignment"
        payload = {
            "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24",
            "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e"
        }
        
        res = await page.evaluate("""
            async ({url, payload, token}) => {
                try {
                    const r = await fetch(url, {
                        method: "POST",
                        headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                        body: JSON.stringify(payload)
                    });
                    if (!r.ok) return { error: await r.text() };
                    return await r.json();
                } catch (e) {
                    return { error: e.toString() };
                }
            }
        """, {"url": url, "payload": payload, "token": token})
        
        print("Response type:", type(res))
        if isinstance(res, dict) and "error" in res:
            print("Error:", res["error"])
        else:
            print("Success! Got", len(res), "elements.")
            
        await page.close()

if __name__ == "__main__":
    asyncio.run(main())
