import asyncio
import json
from playwright.async_api import async_playwright

candidates = [
    "idsls",
    "sls_code",
    "kd_sls",
    "id_sls",
    "sls_id",
    "kode_sls",
    "level_5_id",
    "level_5_code",
    "level_5_fullcode",
    "level5_id",
    "level5_code",
    "level5_full_code",
    "level_4_full_code",
    "level_4_id",
    "level_4_code",
    "level_3_full_code",
    "level_3_id",
    "level_3_code",
    "level_2_full_code",
    "level_2_id",
    "level_2_code"
]

async def test_column(page, col_name):
    payload = {
        "datasource": {"id": 7047, "type": "table"},
        "force": False,
        "queries": [{
            "granularity": None if "time" not in col_name else "P1D",
            "filters": [],
            "extras": {"time_grain_sqla": "P1D", "having": "", "where": ""},
            "columns": [
                {"expressionType": "SQL", "label": "test_col", "sqlExpression": col_name}
            ],
            "metrics": [],
            "row_limit": 5
        }],
        "result_format": "json",
        "result_type": "full"
    }
    
    js_code = """
        async (payload) => {
            const url = 'https://fasih-dashboard.bps.go.id/api/v1/chart/data';
            try {
                const r = await fetch(url, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
                if (!r.ok) return { error: `HTTP ${r.status}: ${await r.text()}` };
                return await r.json();
            } catch (e) {
                return { error: e.toString() };
            }
        }
    """
    
    res = await page.evaluate(js_code, payload)
    return res

async def main():
    print("[START] Script discover_columns started", flush=True)
    async with async_playwright() as p:
        browser = None
        for port in [9222, 9223]:
            try:
                browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
                print(f"[SUCCESS] Connected to port {port}", flush=True)
                break
            except Exception as e:
                pass
        
        if not browser:
            print("[ERROR] Could not connect to Chrome on port 9222/9223.", flush=True)
            return

        try:
            context = browser.contexts[0]
            page = None
            for p_page in context.pages:
                if "fasih-dashboard.bps.go.id" in p_page.url:
                    page = p_page
                    break
            
            if not page:
                print("[INFO] BPS Dashboard page not open in Chrome. Opening new page...", flush=True)
                page = await context.new_page()
                try:
                    await page.goto("https://fasih-dashboard.bps.go.id/superset/dashboard/se2026/", timeout=60000, wait_until="domcontentloaded")
                except Exception as e:
                    print(f"[WARNING] Navigating to page slow: {e}", flush=True)
                await asyncio.sleep(5) # wait for load/login check

            print(f"[INFO] Connected to active BPS page: {page.url}", flush=True)
            
            for col in candidates:
                print(f"Testing column: {col}...", flush=True)
                res = await test_column(page, col)
                if "error" in res:
                    err_msg = res["error"]
                    print(f" -> Result: INVALID ({err_msg[:150]})", flush=True)
                elif "result" in res:
                    data = res["result"][0].get("data", [])
                    print(f" -> Result: VALID! Sample data: {json.dumps(data[:3])}", flush=True)
                else:
                    print(f" -> Result: UNKNOWN RESPONSE: {str(res)[:150]}", flush=True)

        except Exception as ex:
            print(f"[EXCEPTION] Error: {ex}", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
