import asyncio
import json
import re
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
                            "level_2_full_code",
                            "level_3_name",
                            "level_4_name",
                            "level_5_full_code", 
                            "level_5_name",
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
            return
            
        rows = res.get("result", [{}])[0].get("data", [])
        total = len(rows)
        resolved_count = 0
        unresolved_examples = []
        
        for r in rows:
            code = r.get("level_5_full_code")
            if code:
                resolved_count += 1
                continue
                
            # Try to resolve
            lvl2 = r.get("level_2_full_code") or ""
            lvl3_name = r.get("level_3_name") or ""
            lvl4_name = r.get("level_4_name") or ""
            lvl5_name = r.get("level_5_name") or ""
            
            m3 = re.search(r'\[(\d{3})\]', lvl3_name)
            m4 = re.search(r'\[(\d{3})\]', lvl4_name)
            m5 = re.search(r'\[(\d{4})\]', lvl5_name)
            
            if len(lvl2) == 4 and m3 and m4 and m5:
                resolved_code = lvl2 + m3.group(1) + m4.group(1) + m5.group(1)
                resolved_count += 1
            else:
                unresolved_examples.append(r)
                
        print(f"Total rows: {total}")
        print(f"Resolved successfully: {resolved_count} ({resolved_count/total*100:.2f}%)")
        print(f"Unresolved: {len(unresolved_examples)}")
        if unresolved_examples:
            print("Examples of unresolved:")
            for r in unresolved_examples[:10]:
                print(r)

if __name__ == "__main__":
    asyncio.run(main())
