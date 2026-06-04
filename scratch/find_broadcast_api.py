import time
import logging
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

USER_DATA_DIR = "playwright_chrome_profile"
TARGET_URL = "https://fasih-sm.bps.go.id/app/surveys/ecddb52e-f392-403c-a963-47391f217010/37526b20-81c8-42f5-a895-6190137d7394/data"

def intercept_broadcast_api():
    with sync_playwright() as p:
        logging.info("Membuka browser...")
        context = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,
            viewport={"width": 1280, "height": 800}
        )
        page = context.pages[0] if context.pages else context.new_page()

        def handle_request(request):
            url = request.url
            if "broadcast" in url or "history" in url or "log" in url or "mail" in url or "api" in url:
                # Kita filter agar tidak mencetak terlalu banyak url asset static
                if not any(ext in url for ext in [".js", ".css", ".png", ".jpg", ".svg", ".woff"]):
                    logging.info(f"REQUEST: {request.method} {url}")
                    try:
                        if request.post_data:
                            logging.info(f"  Payload: {request.post_data}")
                    except Exception:
                        pass

        def handle_response(response):
            url = response.url
            if "broadcast" in url or "history" in url or "log" in url:
                logging.info(f"RESPONSE ({response.status}): {url}")
                try:
                    text = response.text()
                    logging.info(f"  Response Data (first 300 chars): {text[:300]}")
                except Exception:
                    pass

        page.on("request", handle_request)
        page.on("response", handle_response)

        logging.info(f"Membuka halaman target: {TARGET_URL}")
        try:
            page.goto(TARGET_URL, timeout=60000, wait_until="domcontentloaded")
        except Exception as e:
            logging.warning(f"Timeout/Error: {e}")

        print("\n" + "="*80)
        print("PETUNJUK:")
        print("1. Tunggu halaman daftar data termuat sempurna.")
        print("2. Klik tombol tiga titik (⋮) di salah satu baris perusahaan.")
        print("3. Pilih menu 'Riwayat Broadcast'.")
        print("4. Perhatikan terminal ini untuk melihat API yang terdeteksi.")
        print("="*80 + "\n")
        
        input("Tekan ENTER di sini jika sudah selesai untuk menutup browser...")
        context.close()

if __name__ == "__main__":
    intercept_broadcast_api()
