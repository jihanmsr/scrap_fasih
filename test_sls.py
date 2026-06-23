import asyncio
import json
import httpx
from playwright.async_api import async_playwright
from scrape_granular_core import get_authenticated_context, DATATABLE_URL, check_session_valid

async def main():
    with open("region_map_sulteng_full.json", "r") as f:
        region_map = json.load(f)
    
    sls_list = region_map["kabupaten"]["7206"]["kecamatan"]["7206040"]["desa"]["7206040014"]["sls"]
    print("Desa 7206040014 has", len(sls_list), "SLS.")
    
    async with async_playwright() as p:
        browser, context, page = await get_authenticated_context(p)
        cookies = await context.cookies()
        token = [c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"][0]
        from urllib.parse import unquote
        token = unquote(token)
            
        async with httpx.AsyncClient(timeout=60.0) as client:
            client.headers.update({
                "Content-Type": "application/json",
                "X-XSRF-TOKEN": token,
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json, text/plain, */*"
            })
            for c in cookies:
                client.cookies.set(c['name'], c['value'], domain=c.get('domain', 'fasih-sm.bps.go.id'), path=c.get('path', '/'))
            
            # Query the Desa
            payload = {
                "start": 0, "length": 1,
                "columns": [{"data": "id"}], "order": [], "search": {"value": "", "regex": False},
                "assignmentExtraParam": {
                    "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e",
                    "region2Id": "d833fdce-ebfb-429b-a1bb-8966239fd8e4", # 7206
                    "region3Id": "f784e622-df3d-4c31-90be-e0c2f211822a", # 7206040
                    "region4Id": "060d4b96-6134-406a-a169-2a4c107198bb", # 7206040014
                    "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24",
                    "assignmentErrorStatusType": -1,
                    "filterTargetType": ""
                }
            }
            r = await client.post(DATATABLE_URL, json=payload)
            print("Total in Desa:", r.json().get("totalHit"))
            
            # Query SLS sum
            total_sls_sum = 0
            for sls in sls_list:
                payload["assignmentExtraParam"]["region5Id"] = sls["sls_id"]
                r_sls = await client.post(DATATABLE_URL, json=payload)
                hit = r_sls.json().get("totalHit", 0)
                total_sls_sum += hit
                
            print("Total in all SLS:", total_sls_sum)
            
if __name__ == "__main__":
    asyncio.run(main())
