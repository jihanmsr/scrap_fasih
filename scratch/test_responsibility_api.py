import asyncio
import json
import httpx
from playwright.async_api import async_playwright
from urllib.parse import unquote
from scrape_granular_core import get_authenticated_context, check_session_valid

async def main():
    async with async_playwright() as p:
        browser, context, page = await get_authenticated_context(p)
        cookies = await context.cookies()
        cookie_dict = {c["name"]: c["value"] for c in cookies}
        token_raw = cookie_dict.get("XSRF-TOKEN", "")
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
                
            from scrape_granular_core import refresh_session_if_needed
            await refresh_session_if_needed(client, page, context)
            
            # Re-read token/cookies after potential refresh
            cookies = await context.cookies()
            cookie_dict = {c["name"]: c["value"] for c in cookies}
            token_raw = cookie_dict.get("XSRF-TOKEN", "")
            token = unquote(token_raw) if token_raw else ""
            
            # Target endpoint
            url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/report-progress-by-responsibility"
            
            payload_pencacah = {
                "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24", # SE Umum
                "surveyRoleId": "6d7d919a-45e5-4779-bb87-2905b49fd31a", # Pencacah
                "size": 2,
                "page": 0,
                "search": "",
                "target": "ALL", # Try ALL
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

            payload_pengawas = {
                "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24", # SE Umum
                "surveyRoleId": "93bcf446-c4c1-4462-8ed0-4b0f7ae89e52", # Pengawas
                "size": 2,
                "page": 0,
                "search": "",
                "target": "TARGET_ONLY",
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
            
            print("Evaluating fetch Pencacah (target: ALL) in browser...")
            res_pencacah = await page.evaluate("""
                async ({url, payload, token}) => {
                    try {
                        const r = await fetch(url, {
                            method: "POST",
                            headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                            body: JSON.stringify(payload)
                        });
                        if (!r.ok) return { _error: `HTTP ${r.status}` };
                        return await r.json();
                    } catch (e) {
                        return { _error: e.toString() };
                    }
                }
            """, {"url": url, "payload": payload_pencacah, "token": token})
            
            print("Pencacah (target: ALL) response:")
            print(json.dumps(res_pencacah, indent=2)[:2000])

            print("\nEvaluating fetch Pengawas in browser...")
            res_pengawas = await page.evaluate("""
                async ({url, payload, token}) => {
                    try {
                        const r = await fetch(url, {
                            method: "POST",
                            headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                            body: JSON.stringify(payload)
                        });
                        if (!r.ok) return { _error: `HTTP ${r.status}` };
                        return await r.json();
                    } catch (e) {
                        return { _error: e.toString() };
                    }
                }
            """, {"url": url, "payload": payload_pengawas, "token": token})
            
            print("Pengawas response:")
            print(json.dumps(res_pengawas, indent=2)[:2000])
                
        if browser:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
