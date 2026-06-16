import asyncio
import json
from playwright.async_api import async_playwright

async def test_db_schema(page):
    # Ambil CSRF token
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
    
    payload = {
        "datasource": {"id": 7047, "type": "table"},
        "force": False,
        "queries": [{
            "granularity": None,
            "filters": [
                {"col": "level_1_full_code", "op": "==", "val": "72"}
            ],
            "extras": {"time_grain_sqla": "P1D", "having": "", "where": ""},
            "columns": [
                "level_1_full_code",
                "level_2_full_code",
                "level_3_full_code",
                "level_4_full_code",
                "level_5_full_code",
                "level_5_name"
            ],
            "metrics": [],
            "row_limit": 2000,
            "query_mode": "scan"
        }],
        "result_format": "json",
        "result_type": "full"
    }
    
    js_code = """
        async ({payload, token}) => {
            const url = 'https://fasih-dashboard.bps.go.id/api/v1/chart/data';
            try {
                const r = await fetch(url, {
                    method: "POST",
                    headers: { 
                        "Content-Type": "application/json",
                        "X-CSRFToken": token
                    },
                    body: JSON.stringify(payload)
                });
                return await r.json();
            } catch (e) {
                return { error: e.toString() };
            }
        }
    """
    
    return await page.evaluate(js_code, {"payload": payload, "token": csrf_token})

async def main():
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            context = browser.contexts[0]
            page = None
            for p_page in context.pages:
                if "fasih-dashboard.bps.go.id" in p_page.url:
                    page = p_page
                    break
            
            if not page:
                print("Dashboard page not open.")
                return
                
            res = await test_db_schema(page)
            if "result" in res:
                data = res["result"][0].get("data", [])
                print(f"Retrieved {len(data)} rows.")
                std_sls = [r for r in data if r.get("level_5_name", "").startswith("[00")]
                null_std_l5 = sum(1 for r in std_sls if r.get("level_5_full_code") is None)
                null_std_l4 = sum(1 for r in std_sls if r.get("level_4_full_code") is None)
                print(f"Standard SLS count: {len(std_sls)}")
                print(f"Null level_5_full_code: {null_std_l5}")
                print(f"Null level_4_full_code: {null_std_l4}")
                if std_sls:
                    print("Sample standard SLS:")
                    print(json.dumps(std_sls[:10], indent=2))
            else:
                print("Error:", res)
        except Exception as e:
            print("Error:", e)

if __name__ == "__main__":
    asyncio.run(main())
