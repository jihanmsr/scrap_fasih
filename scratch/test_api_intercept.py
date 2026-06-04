import time
import logging
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

USER_DATA_DIR = "playwright_chrome_profile"
TARGET_URL = "https://fasih-sm.bps.go.id/app/surveys/ecddb52e-f392-403c-a963-47391f217010/37526b20-81c8-42f5-a895-6190137d7394/data"

def intercept_api():
    with sync_playwright() as p:
        logging.info("Membuka browser...")
        context = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,
            viewport={"width": 1280, "height": 800}
        )
        page = context.pages[0] if context.pages else context.new_page()

        api_calls = []

        def handle_request(request):
            url = request.url
            if "datatable-all-user-survey-periode" in url or "assignment" in url or "api/v2" in url:
                logging.info(f"API Request Terdeteksi: {request.method} {url}")
                try:
                    post_data = request.post_data
                    if post_data:
                        logging.info(f"  Payload: {post_data}")
                except Exception:
                    pass

        def handle_response(response):
            url = response.url
            if "datatable-all-user-survey-periode" in url:
                logging.info(f"API Response Terdeteksi: {response.status} {url}")
                try:
                    text = response.text()
                    logging.info(f"  Response Data (first 500 chars): {text[:500]}")
                    # Save response to a file
                    with open("scratch/api_response.json", "w", encoding="utf-8") as f:
                        f.write(text)
                    logging.info("Response lengkap telah disimpan ke scratch/api_response.json")
                except Exception as e:
                    logging.warning(f"Gagal membaca body response: {e}")

        page.on("request", handle_request)
        page.on("response", handle_response)

        logging.info(f"Membuka halaman target: {TARGET_URL}")
        try:
            page.goto(TARGET_URL, timeout=60000, wait_until="domcontentloaded")
        except Exception as e:
            logging.warning(f"Timeout/Error: {e}")

        print("\n" + "="*70)
        print("Tunggu halaman selesai memuat data dan periksa terminal ini.")
        print("Tekan ENTER di terminal ini jika sudah selesai memeriksa.")
        print("="*70 + "\n")
        input("Tekan ENTER untuk menutup browser...")
        context.close()

if __name__ == "__main__":
    intercept_api()
