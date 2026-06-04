import time
import logging
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

USER_DATA_DIR = "playwright_chrome_profile"
TARGET_URL = "https://fasih-sm.bps.go.id/app/surveys/ecddb52e-f392-403c-a963-47391f217010/37526b20-81c8-42f5-a895-6190137d7394/data"

def test_csrf_api():
    with sync_playwright() as p:
        logging.info("Membuka browser...")
        context = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,
            viewport={"width": 1280, "height": 800}
        )
        page = context.pages[0] if context.pages else context.new_page()

        logging.info(f"Membuka halaman target: {TARGET_URL}")
        try:
            page.goto(TARGET_URL, timeout=60000, wait_until="domcontentloaded")
            time.sleep(5)
        except Exception as e:
            logging.warning(f"Timeout/Error: {e}")

        cookies = context.cookies()
        xsrf_token = None
        for cookie in cookies:
            if cookie['name'] == 'XSRF-TOKEN':
                xsrf_token = cookie['value']
                logging.info(f"XSRF-TOKEN Cookie Terdeteksi: {xsrf_token}")
                break

        if xsrf_token:
            logging.info("Mencoba panggil API dengan X-XSRF-TOKEN header...")
            try:
                js_fetch = f"""
                async () => {{
                    const token = "{xsrf_token}";
                    const datatable_res = await fetch("https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode", {{
                        method: "POST",
                        headers: {{ 
                            "Content-Type": "application/json",
                            "X-XSRF-TOKEN": decodeURIComponent(token)
                        }},
                        body: JSON.stringify({{
                            "start": 0,
                            "length": 5,
                            "columns": [{{"data":"id"}}],
                            "order": [],
                            "search": {{"value":"","regex":false}},
                            "assignmentExtraParam": {{"surveyPeriodId":"37526b20-81c8-42f5-a895-6190137d7394","assignmentErrorStatusType":-1}}
                        }})
                    }});
                    const body = await datatable_res.text();
                    return {{
                        status: datatable_res.status,
                        body: body
                    }};
                }}
                """
                res = page.evaluate(js_fetch)
                logging.info(f"API Response Status: {res['status']}")
                logging.info(f"API Response Body: {res['body'][:500]}")
            except Exception as e:
                logging.error(f"Gagal memanggil API: {e}")
        else:
            logging.error("XSRF-TOKEN tidak ditemukan.")

        context.close()

if __name__ == "__main__":
    test_csrf_api()
