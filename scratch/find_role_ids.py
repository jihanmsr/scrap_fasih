import asyncio
import json
from playwright.async_api import async_playwright
from urllib.parse import unquote
from scrape_granular_core import get_authenticated_context

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
            print(f"\n--- Finding Role IDs for {label} (Period: {period_id}) ---")
            url = f"https://fasih-sm.bps.go.id/app/api/survey-user/api/v1/allocations-view/by-user?surveyPeriodId={period_id}&page=0&size=50"
            
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
            
            if res and "data" in res and "content" in res["data"]:
                content = res["data"]["content"]
                found_roles = {}
                for u in content:
                    # check structure
                    # print(list(u.keys()))
                    role_name = u.get("roleName")
                    role_id = u.get("roleId") or u.get("currentSurveyRoleId")
                    if not role_id and "surveyRole" in u:
                        role_id = u["surveyRole"].get("id")
                        role_name = u["surveyRole"].get("name")
                    if role_name and role_id:
                        found_roles[role_name] = role_id
                print(f"Roles found for {label}:")
                for k, v in found_roles.items():
                    print(f"  {k}: {v}")
            else:
                print(f"Could not retrieve user content for {label}:", res)
                
        if browser:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
