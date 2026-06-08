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
        
        kab_id = "bc32354f-1245-426f-b2cf-a5733e1295ad" # Banggai Kepulauan
        
        base_extra = {
            "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e",
            "region2Id": kab_id,
            "surveyPeriodId": period_id,
            "assignmentErrorStatusType": -1,
            "filterTargetType": ""
        }
        
        # We will try adding different keys to assignmentExtraParam
        candidate_params = [
            {"assignmentStatusId": 5}, # Submitted respondent
            {"assignmentStatusId": "5"},
            {"statusId": 5},
            {"statusId": "5"},
            {"assignmentStatusAlias": "SUBMITTED RESPONDENT"},
            {"statusAlias": "SUBMITTED RESPONDENT"},
            {"assignmentStatusName": "SUBMITTED RESPONDENT"},
            {"status": 5},
            {"status": "SUBMITTED RESPONDENT"},
            {"assignmentStatusId": 0}, # DRAFT
            {"assignmentStatusId": "0"},
            {"assignmentStatusAlias": "DRAFT"},
            {"filterTargetType": "TARGET_ONLY"}
        ]
        
        # Also let's try top level parameters
        # And let's get the base count first
        payload_base = {
            "start": 0,
            "length": 1,
            "columns": [{"data": "id"}],
            "order": [],
            "search": {"value": "", "regex": False},
            "assignmentExtraParam": base_extra
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
        base_hit = res_base.get("totalHit", 0)
        print(f"Base count (no status filter): {base_hit}")
        
        for param in candidate_params:
            extra = base_extra.copy()
            extra.update(param)
            payload = {
                "start": 0,
                "length": 1,
                "columns": [{"data": "id"}],
                "order": [],
                "search": {"value": "", "regex": False},
                "assignmentExtraParam": extra
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
            print(f"Filter {param} totalHit: {res.get('totalHit')} (Diff: {res.get('totalHit') - base_hit if res.get('totalHit') is not None else 'N/A'})")

if __name__ == "__main__":
    asyncio.run(main())
