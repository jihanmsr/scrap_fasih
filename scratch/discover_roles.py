import asyncio
import json
from playwright.async_api import async_playwright
from urllib.parse import unquote
from scrape_granular_core import get_authenticated_context, check_session_valid

async def main():
    async with async_playwright() as p:
        browser, context, page = await get_authenticated_context(p)
        cookies = await context.cookies()
        token_raw = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
        token = unquote(token_raw) if token_raw else ""
        
        periods = {
            "SE Umum": "fd68e454-ba45-4b85-8205-f3bf777ded24",
            "SE UB": "37526b20-81c8-42f5-a895-6190137d7394"
        }
        
        for label, period_id in periods.items():
            print(f"\n--- Roles for {label} (Period: {period_id}) ---")
            url = f"https://fasih-sm.bps.go.id/app/api/survey-role/api/v1/roles?surveyPeriodId={period_id}"
            
            res = await page.evaluate("""
                async ({url, token}) => {
                    try {
                        const r = await fetch(url, {
                            headers: { "X-XSRF-TOKEN": token }
                        });
                        return await r.json();
                    } catch(e) {
                        return { error: e.toString() };
                    }
                }
            """, {"url": url, "token": token})
            
            print(json.dumps(res, indent=2))
            
        if browser:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
