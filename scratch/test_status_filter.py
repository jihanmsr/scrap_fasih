import asyncio
import os
import json
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
                
        # KOMBUTOKAN
        region_id = "fbdb6ceb-c553-488f-b985-703666d926fb"
        
        columns_payload = [
            {"data": "id"}, {"data": "codeIdentity"}, {"data": "data1"},
            {"data": "assignmentStatusAlias", "name": "", "searchable": True, "orderable": True, "search": {"value": "OPEN", "regex": False}}, 
            {"data": "currentUserUsername"},
            {"data": "currentUserFullname"}, {"data": "dateCreated"},
            {"data": "dateModified"}, {"data": "region"}, {"data": "assignmentResponsibility"}
        ]
        
        payload = {
            "start": 0, "length": 10, "columns": columns_payload, "order": [], "search": {"value": "", "regex": False},
            "assignmentExtraParam": {
                "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e", "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24",
                "assignmentErrorStatusType": -1, "filterTargetType": "", "region4Id": region_id
            }
        }
        
        url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode"
        
        res = await page.evaluate("""
            async ({url, payload, token}) => {
                try {
                    const r = await fetch(url, {
                        method: "POST",
                        headers: { "X-XSRF-TOKEN": token, "Content-Type": "application/json" },
                        body: JSON.stringify(payload)
                    });
                    if (!r.ok) return { _error: `HTTP ${r.status}` };
                    return await r.json();
                } catch (e) {
                    return { _error: e.toString() };
                }
            }
        """, {"url": url, "payload": payload, "token": token})
        
        print(f"Result: {res}")
        if "searchData" in res and len(res["searchData"]) > 0:
            print(f"Sample status: {res['searchData'][0].get('assignmentStatusAlias')}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
