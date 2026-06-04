import json
import logging
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

USER_DATA_DIR = "playwright_chrome_profile"
TARGET_URL = "https://fasih-sm.bps.go.id/app/surveys/ecddb52e-f392-403c-a963-47391f217010/37526b20-81c8-42f5-a895-6190137d7394/data"

def fetch_sample_email_logs():
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

        # Kita ambil salah satu ID dari response datatable
        # Dan coba panggil API email-schedule/datatable di browser context
        logging.info("Mencoba memanggil API email-schedule/datatable...")
        try:
            sample_js = """
            async () => {
                // 1. Fetch datatable-all-user-survey-periode untuk mendapatkan assignmentId
                const datatable_res = await fetch("https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        "start": 0,
                        "length": 5,
                        "columns": [{"data":"id"}],
                        "order": [],
                        "search": {"value":"","regex":false},
                        "assignmentExtraParam": {"surveyPeriodId":"37526b20-81c8-42f5-a895-6190137d7394","assignmentErrorStatusType":-1}
                    })
                });
                const datatable_json = await datatable_res.json();
                if (!datatable_json.searchData || datatable_json.searchData.length === 0) {
                    return { "error": "No assignment data found" };
                }

                // Cari yang punya email jika ada, atau pakai yang pertama
                const sample_company = datatable_json.searchData[0];
                const assignmentId = sample_company.id;

                // 2. Fetch email-schedule/datatable untuk assignmentId tersebut
                const email_res = await fetch("https://fasih-sm.bps.go.id/app/api/email/api/v1/email-schedule/datatable", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        "start": 1,
                        "pageNumber": 1,
                        "length": 5,
                        "search": {"value":"","regex":true},
                        "emailScheduleParam": {
                            "assignmentId": assignmentId,
                            "surveyPeriodId": "37526b20-81c8-42f5-a895-6190137d7394"
                        }
                    })
                });
                const email_json = await email_res.json();
                return {
                    "company": sample_company,
                    "email_logs": email_json
                };
            }
            """
            result = page.evaluate(sample_js)
            with open("scratch/email_log_sample.json", "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
            logging.info("Berhasil menyimpan sampel response ke scratch/email_log_sample.json")
            print(json.dumps(result, indent=2)[:800])
        except Exception as e:
            logging.error(f"Gagal mengambil sampel email logs: {e}")

        context.close()

import time
if __name__ == "__main__":
    fetch_sample_email_logs()
