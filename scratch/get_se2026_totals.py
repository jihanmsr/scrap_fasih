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
        
        print(f"{'Kabupaten/Kota':<30} | {'Total Prelist':<13} | {'Submitted':<10} | {'Draft':<8} | {'Open':<8}")
        print("-" * 78)
        
        sum_prelist = 0
        sum_submitted = 0
        sum_draft = 0
        sum_open = 0
        
        for kab in kabs:
            payload = {
                "start": 0, "length": 1, "columns": [{"data": "id"}], "order": [], "search": {"value": "", "regex": False},
                "assignmentExtraParam": {
                    "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e",
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
            
            agg = res.get("searchAggregation", [])
            
            # Map aggregation to counts
            counts = {"SUBMITTED RESPONDENT": 0, "DRAFT": 0, "OPEN": 0}
            for item in agg:
                key = item.get("keyAggregation")
                val = item.get("docCount", 0)
                if key in counts:
                    counts[key] = val
                else:
                    counts[key] = val
                    
            c_sub = counts.get("SUBMITTED RESPONDENT", 0)
            c_draft = counts.get("DRAFT", 0)
            c_open = counts.get("OPEN", 0)
            
            # Real total is the sum of all document counts in aggregation
            c_total = sum(item.get("docCount", 0) for item in agg)
            if c_total == 0:
                # Fallback to totalHit if searchAggregation is empty
                c_total = res.get("totalHit", 0)
            
            print(f"{kab['name']:<30} | {c_total:<13} | {c_sub:<10} | {c_draft:<8} | {c_open:<8}")
            
            sum_prelist += c_total
            sum_submitted += c_sub
            sum_draft += c_draft
            sum_open += c_open
            
        print("-" * 78)
        print(f"{'TOTAL':<30} | {sum_prelist:<13} | {sum_submitted:<10} | {sum_draft:<8} | {sum_open:<8}")

if __name__ == "__main__":
    asyncio.run(main())
