import asyncio
import json
import httpx
from playwright.async_api import async_playwright
from scrape_granular_core import get_authenticated_context, DATATABLE_URL, check_session_valid

async def main():
    async with async_playwright() as p:
        browser, context, page = await get_authenticated_context(p)
        cookies = await context.cookies()
        cookie_dict = {c["name"]: c["value"] for c in cookies}
        token_raw = cookie_dict.get("XSRF-TOKEN", "")
        from urllib.parse import unquote
        token = unquote(token_raw) if token_raw else ""
        
        valid = await check_session_valid(page, token)
        if not valid:
            print("Session not valid")
            return
            
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
            
            # Query Kab Toli-Toli SE UMUM
            payload = {
                "start": 0, "length": 1,
                "columns": [{"data": "id"}], "order": [], "search": {"value": "", "regex": False},
                "assignmentExtraParam": {
                    "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e", # SE Umum
                    "region2Id": "d833fdce-ebfb-429b-a1bb-8966239fd8e4", # Toli-Toli
                    "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24",
                    "assignmentErrorStatusType": -1,
                    "filterTargetType": ""
                }
            }
            r = await client.post(DATATABLE_URL, json=payload)
            print("Toli-Toli SE Umum:", r.json().get("totalHit"))

            # Query Kab Toli-Toli SE UB
            payload_ub = {
                "start": 0, "length": 1,
                "columns": [{"data": "id"}], "order": [], "search": {"value": "", "regex": False},
                "assignmentExtraParam": {
                    "region1Id": "a00c8aef-afc4-4d4f-b80d-789a15450ef9", # SE UB
                    "region2Id": "d3a28bfa-b611-488b-8255-369da5cedbf7", # Toli-Toli UB
                    "surveyPeriodId": "37526b20-81c8-42f5-a895-6190137d7394",
                    "assignmentErrorStatusType": -1,
                    "filterTargetType": ""
                }
            }
            r_ub = await client.post(DATATABLE_URL, json=payload_ub)
            print("Toli-Toli SE UB:", r_ub.json().get("totalHit"))
            
if __name__ == "__main__":
    asyncio.run(main())
