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
        print("Membuka halaman dashboard...")
        await page.goto("https://fasih-dashboard.bps.go.id/superset/dashboard/se2026/", timeout=60000, wait_until="networkidle")
        
        data = await page.evaluate("""() => {
            const store = window.store || window.__store__;
            if (!store) return { error: "No Redux store found" };
            const state = store.getState();
            
            const slices = state.sliceEntities?.slices || {};
            const result = [];
            for (const id in slices) {
                const sl = slices[id];
                result.push({
                    slice_id: sl.slice_id,
                    slice_name: sl.slice_name,
                    viz_type: sl.viz_type,
                    datasource: sl.datasource
                });
            }
            return result;
        }""")
        
        print("DAFTAR WIDGET DI DASHBOARD:")
        for item in data:
            print(item)
            
        await page.close()

asyncio.run(main())
