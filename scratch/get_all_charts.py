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
            print("CDP connection failed")
            return
            
        context = browser.contexts[0]
        page = await context.new_page()
        
        await page.goto("https://fasih-dashboard.bps.go.id/superset/dashboard/se2026/", timeout=30000, wait_until="domcontentloaded")
        
        # Get CSRF token
        csrf_token = await page.evaluate("""() => {
            const el = document.querySelector('input[name="csrf_token"]');
            if (el) return el.value;
            const bootstrapEl = document.getElementById('app');
            if (bootstrapEl) {
                const data = bootstrapEl.getAttribute('data-bootstrap');
                if (data) {
                    try {
                        return JSON.parse(data).csrf_token;
                    } catch(e) {}
                }
            }
            return '';
        }""")
        
        if not csrf_token:
            cookies = await context.cookies()
            csrf_token = next((c["value"] for c in cookies if c["name"] == "referrer" or c["name"] == "session"), "")
            
        print("Mengambil daftar semua chart dari Superset API...")
        
        charts_data = await page.evaluate("""
            async ({csrfToken}) => {
                const url = 'https://fasih-dashboard.bps.go.id/api/v1/chart/?q={"page_size":200}';
                try {
                    const r = await fetch(url, {
                        method: "GET",
                        headers: { "X-CSRFToken": csrfToken }
                    });
                    if (!r.ok) return { error: `HTTP ${r.status}` };
                    return await r.json();
                } catch (e) {
                    return { error: e.toString() };
                }
            }
        """, {"csrfToken": csrf_token})
        
        if "error" in charts_data:
            print("Error:", charts_data["error"])
        else:
            result = charts_data.get("result", [])
            with open("scratch/all_charts.json", "w") as f:
                json.dump(result, f, indent=2)
            
            print(f"Berhasil menemukan {len(result)} charts.")
            for c in result:
                name = c.get("slice_name", "")
                if "missing" in name.lower() or "value" in name.lower() or "r." in name.lower():
                    print(f"POTENTIAL MATCH -> ID: {c.get('id')}, Name: {name}, Viz: {c.get('viz_type')}")
                    
        await page.close()

asyncio.run(main())
