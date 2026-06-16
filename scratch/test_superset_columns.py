import asyncio
import json
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = None
        for port in [9223, 9222]:
            try:
                browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
                break
            except Exception:
                pass
        if not browser:
            print("Failed to connect to browser CDP")
            return
        
        context = browser.contexts[0]
        page = None
        for p_page in context.pages:
            if "fasih-dashboard.bps.go.id" in p_page.url:
                page = p_page
                break
        if not page:
            print("Dashboard page not found")
            return
            
        csrf_token = await page.evaluate("""() => {
            const el = document.querySelector('input[name="csrf_token"]');
            if (el) return el.value;
            const bootstrapEl = document.getElementById('app');
            if (bootstrapEl) {
                const data = bootstrapEl.getAttribute('data-bootstrap');
                if (data) {
                    try {
                        const parsed = JSON.parse(data);
                        return parsed.csrf_token;
                    } catch(e) {}
                }
            }
            return '';
        }""")
        
        js_code = """
            async ({csrfToken}) => {
                const url = 'https://fasih-dashboard.bps.go.id/api/v1/chart/data';
                
                const payload = {
                    "datasource": {"id": 7047, "type": "table"},
                    "force": false,
                    "queries": [{
                        "granularity": null,
                        "filters": [
                            {"col": "level_1_full_code", "op": "==", "val": "72"}
                        ],
                        "extras": {"time_grain_sqla": "P1D", "having": "", "where": ""},
                        "columns": [
                            "level_1_full_code", "level_1_name",
                            "level_2_full_code", "level_2_name",
                            "level_3_full_code", "level_3_name",
                            "level_4_full_code", "level_4_name",
                            "level_5_full_code", "level_5_name",
                            "assign",
                            "sync_count_pencacah"
                        ],
                        "metrics": [],
                        "row_limit": 50000,
                        "query_mode": "scan"
                    }],
                    "result_format": "json",
                    "result_type": "full"
                };

                try {
                    const r = await fetch(url, {
                        method: "POST",
                        headers: { 
                            "Content-Type": "application/json",
                            "X-CSRFToken": csrfToken
                        },
                        body: JSON.stringify(payload)
                    });
                    if (!r.ok) return { error: `HTTP ${r.status}: ${await r.text()}` };
                    return await r.json();
                } catch (e) {
                    return { error: e.toString() };
                }
            }
        """
        res = await page.evaluate(js_code, {"csrfToken": csrf_token})
        if "error" in res:
            print("Error:", res["error"])
        else:
            rows = res.get("result", [{}])[0].get("data", [])
            null_rows = [r for r in rows if r.get("level_5_full_code") is None]
            print(f"Total rows fetched: {len(rows)}")
            print(f"Total rows with null level_5_full_code: {len(null_rows)}")
            for idx, r in enumerate(null_rows[:20]):
                print(f"Null Row {idx+1}:")
                print(f"  level_1: {r.get('level_1_full_code')} - {r.get('level_1_name')}")
                print(f"  level_2: {r.get('level_2_full_code')} - {r.get('level_2_name')}")
                print(f"  level_3: {r.get('level_3_full_code')} - {r.get('level_3_name')}")
                print(f"  level_4: {r.get('level_4_full_code')} - {r.get('level_4_name')}")
                print(f"  level_5: {r.get('level_5_full_code')} - {r.get('level_5_name')}")
                print(f"  assign: {r.get('assign')}, sync: {r.get('sync_count_pencacah')}")

if __name__ == "__main__":
    asyncio.run(main())
