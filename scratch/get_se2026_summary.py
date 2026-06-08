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
        period_id = "fd68e454-ba45-4b85-8205-f3bf777ded24" # SE2026 PENDATAAN
        
        kabs = [
            {"id": "bc32354f-1245-426f-b2cf-a5733e1295ad", "name": "[01] BANGGAI KEPULAUAN"},
            {"id": "530e9ca5-86ba-434e-9b04-405102e6d900", "name": "[02] BANGGAI"},
            {"id": "9783f0c1-f047-477f-8840-11eae7cf70e2", "name": "[03] MOROWALI"},
            {"id": "fb9cd9f0-c4c0-4a37-9041-57190693f625", "name": "[04] POSO"},
            {"id": "289f1ff3-a6ad-4c9b-a49f-7b454d03a33f", "name": "[05] DONGGALA"},
            {"id": "d833fdce-ebfb-429b-a1bb-8966239fd8e4", "name": "[06] TOLI-TOLI"},
            {"id": "c523694a-2e72-4570-9489-da2d7b119fe7", "name": "[07] BUOL"},
            {"id": "25c59fd9-afd5-4c1a-9dfb-42bb697a7434", "name": "[08] PARIGI MOUTONG"},
            {"id": "736c4c22-51d1-44be-8b2c-aa197d9459a4", "name": "[09] TOJO UNA-UNA"},
            {"id": "0061da62-2a47-4dee-b8d0-239b33e2c59d", "name": "[10] SIGI"},
            {"id": "eed1a3e7-b81d-4fc7-b0d6-61257c1449b2", "name": "[11] BANGGAI LAUT"},
            {"id": "d05ef8fd-b5e4-414f-9a83-8cdea03e0767", "name": "[12] MOROWALI UTARA"},
            {"id": "4ab6ca2f-7952-4e8e-a94d-b6dd933e5d44", "name": "[71] PALU"}
        ]
        
        print(f"{'Kabupaten/Kota':<30} | {'Prelist':<8} | {'Submitted':<9} | {'Draft':<8}")
        print("-" * 65)
        
        total_prelist = 0
        total_submitted = 0
        total_draft = 0
        
        for kab in kabs:
            # Get prelist count
            payload_base = {
                "start": 0, "length": 1, "columns": [{"data": "id"}], "order": [], "search": {"value": "", "regex": False},
                "assignmentExtraParam": {
                    "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e",
                    "region2Id": kab["id"],
                    "surveyPeriodId": period_id,
                    "assignmentErrorStatusType": -1,
                    "filterTargetType": ""
                }
            }
            
            # Get submitted count
            payload_sub = {
                "start": 0, "length": 1, "columns": [{"data": "id"}], "order": [], "search": {"value": "", "regex": False},
                "assignmentExtraParam": {
                    "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e",
                    "region2Id": kab["id"],
                    "surveyPeriodId": period_id,
                    "assignmentStatusAlias": "SUBMITTED RESPONDENT",
                    "assignmentErrorStatusType": -1,
                    "filterTargetType": ""
                }
            }
            
            # Get draft count
            payload_draft = {
                "start": 0, "length": 1, "columns": [{"data": "id"}], "order": [], "search": {"value": "", "regex": False},
                "assignmentExtraParam": {
                    "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e",
                    "region2Id": kab["id"],
                    "surveyPeriodId": period_id,
                    "assignmentStatusAlias": "DRAFT",
                    "assignmentErrorStatusType": -1,
                    "filterTargetType": ""
                }
            }
            
            res_base = await page.evaluate("""
                async ({url, payload, token}) => {
                    const r = await fetch(url, {
                        method: "POST",
                        headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                        body: JSON.stringify(payload)
                    });
                    return await r.json();
                }
            """, {"url": datatable_url, "payload": payload_base, "token": token})
            
            res_sub = await page.evaluate("""
                async ({url, payload, token}) => {
                    const r = await fetch(url, {
                        method: "POST",
                        headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                        body: JSON.stringify(payload)
                    });
                    return await r.json();
                }
            """, {"url": datatable_url, "payload": payload_sub, "token": token})
            
            res_draft = await page.evaluate("""
                async ({url, payload, token}) => {
                    const r = await fetch(url, {
                        method: "POST",
                        headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                        body: JSON.stringify(payload)
                    });
                    return await r.json();
                }
            """, {"url": datatable_url, "payload": payload_draft, "token": token})
            
            c_base = res_base.get("totalHit", 0)
            c_sub = res_sub.get("totalHit", 0)
            c_draft = res_draft.get("totalHit", 0)
            
            print(f"{kab['name']:<30} | {c_base:<8} | {c_sub:<9} | {c_draft:<8}")
            
            total_prelist += c_base
            total_submitted += c_sub
            total_draft += c_draft
            
        print("-" * 65)
        print(f"{'TOTAL':<30} | {total_prelist:<8} | {total_submitted:<9} | {total_draft:<8}")

if __name__ == "__main__":
    asyncio.run(main())
