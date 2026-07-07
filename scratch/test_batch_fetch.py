import asyncio
import json
import os
import sys
from urllib.parse import unquote
from playwright.async_api import async_playwright

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrape_granular_core import get_authenticated_context, SURVEY_CONFIGS

async def main():
    async with async_playwright() as p:
        print("Connecting to browser...")
        browser, context, page = await get_authenticated_context(p)
        if not page:
            print("Failed to connect.")
            return
            
        print("Active Page URL:", page.url)
        cookies = await context.cookies()
        token_raw = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), "")
        token = unquote(token_raw) if token_raw else ""
        
        url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/report-progress-assignment"
        
        # Compile payloads
        for config in SURVEY_CONFIGS:
            label = config["label"]
            survey_period_id = config["survey_period_id"]
            region1_id = config["region1_id"]
            kab_map = config["kab_region_map"]
            
            print(f"\nFetching batch for {label} ({len(kab_map)} kabupaten)...")
            payloads = []
            kab_ordered_codes = sorted(kab_map.keys())
            
            for code in kab_ordered_codes:
                kab_info = kab_map[code]
                payloads.append({
                    "surveyPeriodId": survey_period_id,
                    "assignmentStatusAlias": None,
                    "assignmentErrorStatusType": -1,
                    "data1": None, "data2": None, "data3": None, "data4": None, "data5": None,
                    "data6": None, "data7": None, "data8": None, "data9": None, "data10": None,
                    "regionId": None,
                    "region1Id": region1_id,
                    "region2Id": kab_info["id"],
                    "currentUserId": None,
                    "userIdResponsibility": None
                })
                
            results = await page.evaluate("""
                async ({url, payloads, token}) => {
                    const fetchOne = async (payload) => {
                        try {
                            const r = await fetch(url, {
                                method: "POST",
                                headers: {
                                    "Content-Type": "application/json",
                                    "X-XSRF-TOKEN": token
                                },
                                body: JSON.stringify(payload)
                            });
                            if (!r.ok) return { error: `HTTP ${r.status}` };
                            return await r.json();
                        } catch (e) {
                            return { error: e.toString() };
                        }
                    };
                    return await Promise.all(payloads.map(fetchOne));
                }
            """, {"url": url, "payloads": payloads, "token": token})
            
            # Print summary of results
            if results:
                print("Sample result type:", type(results[0]))
                print("Sample result keys/value:", results[0])
            for code, res in zip(kab_ordered_codes, results):
                kab_name = kab_map[code]["name"]
                if not isinstance(res, dict):
                    print(f"  [WARNING] {kab_name}: res is not dict: {res}")
                    continue
                if "error" in res:
                    print(f"  [ERROR] {kab_name}: {res['error']}")
                else:
                    data = res.get("data", [])
                    success = res.get("success", False)
                    if success and data:
                        item = data[0]
                        print(f"  [SUCCESS] {kab_name}: total={item.get('total')}, draft={item.get('draft')}, open={item.get('open')}, submittedPencacah={item.get('submittedPencacah')}, submittedRespondent={item.get('submittedRespondent')}")
                    else:
                        print(f"  [WARNING] {kab_name}: success={success}, data_length={len(data)}")
                        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
