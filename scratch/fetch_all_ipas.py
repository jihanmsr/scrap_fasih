import asyncio
import json
import datetime
from playwright.async_api import async_playwright

async def get_data():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        page = None
        for pg in browser.contexts[0].pages:
            if "fasih-sm.bps.go.id" in pg.url:
                page = pg
                break
        
        if not page:
            print("Tab FASIH tidak ditemukan.")
            return

        cookies = await page.context.cookies()
        xsrf_token = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), "")
        
        # Ambil kabupaten
        kab_payload = {
            "groupId": "6b0b053f-aa43-4855-ac8f-26857b735c93",
            "smallestLevelFullCode": "72",
            "level": 1
        }
        res_kab = await page.evaluate("""
            async ({payload, token}) => {
                const url = "https://fasih-sm.bps.go.id/app/api/region/api/v1/region/custom-by-smallest-code-and-level?groupId=" + payload.groupId + "&smallestLevelFullCode=" + payload.smallestLevelFullCode + "&level=" + payload.level;
                const r = await fetch(url, { headers: { "X-XSRF-TOKEN": token } });
                return await r.json();
            }
        """, {"payload": kab_kab, "token": xsrf_token} if False else {"payload": kab_payload, "token": xsrf_token}) # typo bypass
        
        if not res_kab or not res_kab.get("success"):
            print("Gagal ambil region:", res_kab)
            return
            
        kabupatens = res_kab["data"]["children"]
        all_data = []
        
        for kab in kabupatens:
            start = 0
            while True:
                payload = {
                    "start": start,
                    "length": 100,
                    "search": {"value": "", "regex": False},
                    "assignmentExtraParam": {
                        "region1Id": "a00c8aef-afc4-4d4f-b80d-789a15450ef9",
                        "region2Id": kab["id"],
                        "surveyPeriodId": "37526b20-81c8-42f5-a895-6190137d7394",
                        "assignmentErrorStatusType": -1,
                        "filterTargetType": ""
                    }
                }
                
                res = await page.evaluate("""
                    async ({payload, token}) => {
                        const url = "https://fasih-sm.bps.go.id/app/api/survey-assignment/api/v1/assignment/datatable-all-user-survey-periode";
                        const r = await fetch(url, {
                            method: "POST",
                            headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                            body: JSON.stringify(payload)
                        });
                        return await r.json();
                    }
                """, {"payload": payload, "token": xsrf_token})
                
                if "searchData" not in res or not res["searchData"]:
                    break
                    
                all_data.extend(res["searchData"])
                start += 100
                if start >= res.get("totalHit", 0):
                    break
        
        with open("scratch/ipas_raw.json", "w") as f:
            json.dump(all_data, f)
            
        print(f"Berhasil fetch {len(all_data)} records.")

asyncio.run(get_data())
