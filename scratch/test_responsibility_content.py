import asyncio
import json
import httpx
from playwright.async_api import async_playwright
from urllib.parse import unquote
from scrape_granular_core import get_authenticated_context, refresh_session_if_needed

async def main():
    async with async_playwright() as p:
        browser, context, page = await get_authenticated_context(p)
        cookies = await context.cookies()
        token_raw = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), "")
        token = unquote(token_raw) if token_raw else ""
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            client.headers.update({
                "Content-Type": "application/json",
                "X-XSRF-TOKEN": token,
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json, text/plain, */*"
            })
            for c in cookies:
                client.cookies.set(
                    c['name'], c['value'],
                    domain=c.get('domain', 'fasih-sm.bps.go.id'), path=c.get('path', '/')
                )
                
            print("Refreshing session if needed...")
            await refresh_session_if_needed(client, page, context)
            
            # Re-read token/cookies after potential refresh
            cookies = await context.cookies()
            cookie_dict = {c["name"]: c["value"] for c in cookies}
            token_raw = cookie_dict.get("XSRF-TOKEN", "")
            token = unquote(token_raw) if token_raw else ""
            
            url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/report-progress-by-responsibility"
            payload = {
                "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24", # SE Umum
                "surveyRoleId": "6d7d919a-45e5-4779-bb87-2905b49fd31a", # Pencacah
                "size": 10,
                "page": 0,
                "search": "",
                "target": "ALL",
                "region": {
                    "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e", # Sulteng
                    "region2Id": None,
                    "region3Id": None,
                    "region4Id": None,
                    "region5Id": None,
                    "region6Id": None,
                    "region7Id": None,
                    "region8Id": None,
                    "region9Id": None,
                    "region10Id": None
                },
                "regionSummaryLevel": 6
            }
            
            print("Evaluating fetch in page...")
            resp = await page.evaluate("""
                async ({url, payload, token}) => {
                    const r = await fetch(url, {
                        method: "POST",
                        headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                        body: JSON.stringify(payload)
                    });
                    if (!r.ok) return { _error: `HTTP ${r.status}` };
                    return await r.json();
                }
            """, {"url": url, "payload": payload, "token": token})
            
            if resp and isinstance(resp, dict) and "_error" not in resp:
                print("Success:", resp.get("success"))
                data = resp.get("data", {})
                print("Data top-level keys:", list(data.keys()) if isinstance(data, dict) else type(data))
                if isinstance(data, dict):
                    print("  totalPages:", data.get("totalPages"))
                    print("  totalElements:", data.get("totalElements"))
                    content = data.get("content", [])
                    print(f"  content length: {len(content)}")
                    if content:
                        print("  Sample first item keys:", list(content[0].keys()))
                        print("  Sample first item user:", content[0].get("username"), "role:", content[0].get("roleName"))
                        regions = content[0].get("regionSummary", [])
                        print(f"  Sample first item regions count: {len(regions)}")
                        if regions:
                            print("  Sample first regionCode:", regions[0].get("regionCode"))
            else:
                print("Error response:", resp)
                
        if browser:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
