import json
import logging
import time
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

USER_DATA_DIR = "playwright_chrome_profile"

def probe_endpoints():
    with sync_playwright() as p:
        logging.info("Membuka browser...")
        context = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False
        )
        page = context.pages[0] if context.pages else context.new_page()

        # Buka page
        page.goto("https://fasih-sm.bps.go.id/app/surveys/ecddb52e-f392-403c-a963-47391f217010/37526b20-81c8-42f5-a895-6190137d7394/data", wait_until="domcontentloaded")
        time.sleep(5)

        # Probing JS
        js_code = """
        async () => {
            const tokenCookie = document.cookie.split('; ').find(row => row.startsWith('XSRF-TOKEN='));
            const token = tokenCookie ? decodeURIComponent(tokenCookie.split('=')[1]) : "";
            
            const endpoints = [
                "https://fasih-sm.bps.go.id/app/api/region/api/v1/regions?groupId=6b0b053f-aa43-4855-ac8f-26857b735c93&level=2&parentCode=72",
                "https://fasih-sm.bps.go.id/app/api/region/api/v1/regions?groupId=6b0b053f-aa43-4855-ac8f-26857b735c93&level=2&parentFullCode=72",
                "https://fasih-sm.bps.go.id/app/api/region/api/v1/region/custom-by-smallest-code-and-level?groupId=6b0b053f-aa43-4855-ac8f-26857b735c93&level=2",
                "https://fasih-sm.bps.go.id/app/api/region/api/v1/region/custom-by-smallest-code-and-level?groupId=6b0b053f-aa43-4855-ac8f-26857b735c93&smallestLevelFullCode=72&level=2",
                "https://fasih-sm.bps.go.id/app/api/region/api/v1/region?groupId=6b0b053f-aa43-4855-ac8f-26857b735c93&level=2&parentCode=72",
                "https://fasih-sm.bps.go.id/app/api/region/api/v1/regions/level/2?parentCode=72",
                "https://fasih-sm.bps.go.id/app/api/region/api/v1/regions/level/2?parentFullCode=72",
                "https://fasih-sm.bps.go.id/app/api/region/api/v1/regions/level/2?groupId=6b0b053f-aa43-4855-ac8f-26857b735c93"
            ];
            
            const results = {};
            for (const url of endpoints) {
                try {
                    const res = await fetch(url, {
                        headers: { "X-XSRF-TOKEN": token }
                    });
                    results[url] = {
                        status: res.status,
                        json: await res.json()
                    };
                } catch (e) {
                    results[url] = { error: e.message };
                }
            }
            return results;
        }
        """
        try:
            results = page.evaluate(js_code)
            with open("scratch/endpoints_probe.json", "w", encoding="utf-8") as f:
                json.dump(results, f, indent=4)
            logging.info("Probing selesai, hasil disimpan ke scratch/endpoints_probe.json")
        except Exception as e:
            logging.error(f"Gagal probing: {e}")

        context.close()

if __name__ == "__main__":
    probe_endpoints()
