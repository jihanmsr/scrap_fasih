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
        
        datatable_url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode"
        period_id = "37526b20-81c8-42f5-a895-6190137d7394" # Sensus Ekonomi UB PENDATAAN
        
        # We mapped Group 2 (6b0b053f-aa43-4855-ac8f-26857b735c93) kabupaten IDs:
        ub_kabs = [
            {"code": "01", "name": "[01] BANGGAI KEPULAUAN", "id": "9c9b2d79-9fb1-4ce7-b0f1-6b7bb5511beb"},
            {"code": "02", "name": "[02] BANGGAI", "id": "34165dd5-372e-42fa-99c6-0cc19a9b4d0b"},
            {"code": "03", "name": "[03] MOROWALI", "id": "48c4e5d0-5525-41a8-a4ba-2cc38cd9c424"},
            {"code": "04", "name": "[04] POSO", "id": "e18368ae-d1cd-4d43-a74d-5b9ddac5dd22"},
            {"code": "05", "name": "[05] DONGGALA", "id": "c075c4b4-7eb0-4d72-9c16-5103088fb5eb"},
            {"code": "06", "name": "[06] TOLI-TOLI", "id": "d3a28bfa-b611-488b-8255-369da5cedbf7"},
            {"code": "07", "name": "[07] BUOL", "id": "dfe4c643-3282-40db-a5fd-cb288a4f592d"},
            {"code": "08", "name": "[08] PARIGI MOUTONG", "id": "f18109d2-fc8b-4b9c-886a-dc242d21206e"},
            {"code": "09", "name": "[09] TOJO UNA-UNA", "id": "4d01eba1-5ae9-4603-82a6-2c831aea9905"},
            {"code": "10", "name": "[10] SIGI", "id": "2a240d3a-67ee-45b2-ae78-4b4b3a909a90"},
            {"code": "11", "name": "[11] BANGGAI LAUT", "id": "288c5680-f6d5-4783-a946-d5a06f547c02"},
            {"code": "12", "name": "[12] MOROWALI UTARA", "id": "a5324f17-7a00-436f-b468-2fc59fcf605d"},
            {"code": "71", "name": "[71] PALU", "id": "1acfedb4-276e-44d6-9e45-6d43588536d6"}
        ]
        
        prov_id = "a00c8aef-afc4-4d4f-b80d-789a15450ef9" # Sulawesi Tengah for Sensus Ekonomi UB
        
        print(f"{'Kabupaten/Kota':<30} | {'Prelist':<8} | {'Submitted':<9} | {'Draft':<8}")
        print("-" * 65)
        
        for kab in ub_kabs:
            payload = {
                "start": 0, "length": 1, "columns": [{"data": "id"}], "order": [], "search": {"value": "", "regex": False},
                "assignmentExtraParam": {
                    "region1Id": prov_id,
                    "region2Id": kab["id"],
                    "surveyPeriodId": period_id,
                    "assignmentErrorStatusType": -1,
                    "filterTargetType": ""
                }
            }
            res = await page.evaluate("""
                async ({url, payload, token}) => {
                    const r = await fetch(url, {
                        method: "POST",
                        headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                        body: JSON.stringify(payload)
                    });
                    return await r.json();
                }
            """, {"url": datatable_url, "payload": payload, "token": token})
            
            total = res.get("totalHit", 0)
            agg = res.get("searchAggregation", [])
            draft = 0
            open_count = 0
            submitted = 0
            
            for item in agg:
                key = item.get("keyAggregation", "")
                count = item.get("docCount", 0)
                if key == "DRAFT":
                    draft += count
                elif key == "OPEN":
                    open_count += count
                elif "SUBMITTED" in key:
                    submitted += count
                    
            print(f"{kab['name']:<30} | {total:<8} | {submitted:<9} | {draft:<8}")

if __name__ == "__main__":
    asyncio.run(main())
