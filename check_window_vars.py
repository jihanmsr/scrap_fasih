import asyncio
import json
from playwright.async_api import async_playwright

async def main():
    print("[START] Script check_window_vars started", flush=True)
    async with async_playwright() as p:
        browser = None
        for port in [9223, 9222]:
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
                print("[ERROR] BPS Dashboard page not open in Chrome.", flush=True)
                return

            print(f"[INFO] Connected to active BPS page: {page.url}", flush=True)
            
            # Let's inspect the global variables or HTML for dataset columns
            keys = await page.evaluate("""() => {
                const results = {};
                // Search for dataset details in common bootstrap elements
                const appEl = document.getElementById('app');
                if (appEl) {
                    results.app_data_bootstrap = appEl.getAttribute('data-bootstrap')?.substring(0, 1000);
                }
                
                // Search for any global objects related to superset
                results.global_keys = Object.keys(window).filter(k => 
                    k.toLowerCase().includes('bootstrap') || 
                    k.toLowerCase().includes('superset') || 
                    k.toLowerCase().includes('slice') ||
                    k.toLowerCase().includes('dashboard')
                );
                
                return results;
            }""")
            
            print("Detected variables/elements:", json.dumps(keys, indent=2), flush=True)

            # Let's check the bootstrap data specifically
            bootstrap_data = await page.evaluate("""() => {
                const appEl = document.getElementById('app');
                if (appEl) {
                    const data = appEl.getAttribute('data-bootstrap');
                    if (data) {
                        try {
                            const parsed = JSON.parse(data);
                            // Look for dashboard_info or slices/datasets metadata
                            return {
                                keys: Object.keys(parsed),
                                dashboard_title: parsed.dashboard_title,
                                common: parsed.common ? Object.keys(parsed.common) : null
                            };
                        } catch(e) {
                            return { error: e.toString() };
                        }
                    }
                }
                return null;
            }""")
            print("Bootstrap Data keys:", json.dumps(bootstrap_data, indent=2), flush=True)

            # Let's check window.__initialState__ or similar Redux state
            redux_keys = await page.evaluate("""() => {
                // Superset uses Redux, let's find the store state
                const store = window.store || window.__store__;
                if (store && typeof store.getState === 'function') {
                    const state = store.getState();
                    return {
                        store_keys: Object.keys(state),
                        slice_entities: state.sliceEntities ? Object.keys(state.sliceEntities) : null,
                        dashboard_info: state.dashboardInfo ? Object.keys(state.dashboardInfo) : null,
                        datasets: state.datasources ? Object.keys(state.datasources) : null
                    };
                }
                // Check initial state key
                const initial = window.__INITIAL_STATE__ || window.initialState;
                if (initial) {
                    return { initial_state_keys: Object.keys(initial) };
                }
                return null;
            }""")
            print("Redux State keys:", json.dumps(redux_keys, indent=2), flush=True)

        except Exception as ex:
            print(f"[EXCEPTION] Error: {ex}", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
