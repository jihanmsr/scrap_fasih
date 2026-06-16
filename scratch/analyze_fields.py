import asyncio
import json
from playwright.async_api import async_playwright
from urllib.parse import unquote

async def main():
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9223")
            context = browser.contexts[0]
            page = None
            for p_page in context.pages:
                if "fasih-sm.bps.go.id" in p_page.url:
                    page = p_page
                    break
            if not page: return

            cookies = await page.context.cookies()
            xsrf_token = unquote(next(c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"))

            # Fetch 100 non-target records
            payload = {
                "start": 0, "length": 100, "columns": [{"data": "id"}], "order": [], "search": {"value": "", "regex": False},
                "assignmentExtraParam": {
                    "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e",
                    "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24",
                    "assignmentErrorStatusType": -1,
                    "filterTargetType": "non-target"
                }
            }

            res = await page.evaluate("""
                async ({payload, token}) => {
                    const r = await fetch("https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode", {
                        method: "POST",
                        headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                        body: JSON.stringify(payload)
                    });
                    return await r.json();
                }
            """, {"payload": payload, "token": xsrf_token})

            search_data = res.get("searchData", [])
            print(f"Total non-target records fetched: {len(search_data)}")
            
            # Let's count unique values of data fields
            field_values = {}
            for col in range(1, 11):
                field_key = f"data{col}"
                field_values[field_key] = set()
                
            for item in search_data:
                for col in range(1, 11):
                    field_key = f"data{col}"
                    val = item.get(field_key)
                    if val:
                        field_values[field_key].add(str(val))
            
            for field_key, val_set in field_values.items():
                if val_set:
                    print(f"\n{field_key} ({len(val_set)} unique values):")
                    # print sample of up to 10 unique values
                    print(list(val_set)[:10])

        except Exception as e:
            print("Error:", e)

if __name__ == "__main__":
    asyncio.run(main())
