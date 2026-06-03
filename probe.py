import os
import json
import logging
import time
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

USER_DATA_DIR = "playwright_chrome_profile"

def run_probe():
    with sync_playwright() as p:
        logging.info("Membuka browser dengan profil lokal...")
        context = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False
        )
        page = context.pages[0] if context.pages else context.new_page()
        
        # Intercept network responses to log API traffic
        def handle_response(response):
            try:
                url = response.url
                if "fasih-sm.bps.go.id" in url and "api" in url:
                    status = response.status
                    content_type = response.headers.get("content-type", "")
                    if "application/json" in content_type:
                        try:
                            data = response.json()
                            logging.info(f"API Response: {url} (Status: {status})")
                            # Save a sample response to a file to inspect keys
                            filename = f"sample_{url.split('/')[-1].split('?')[0]}.json"
                            with open(filename, "w", encoding="utf-8") as f:
                                json.dump(data, f, indent=2, ensure_ascii=False)
                            logging.info(f"Saved sample JSON response to {filename}")
                        except Exception as e:
                            pass
            except Exception as e:
                pass

        page.on("response", handle_response)
        
        # Go to fasih-sm
        target_url = "https://fasih-sm.bps.go.id"
        logging.info(f"Navigasi ke {target_url}...")
        page.goto(target_url)
        
        print("\n" + "="*70)
        print("SILAKAN LOGIN & MASUK KE HALAMAN DATA UB (SENSUS EKONOMI 2026 - UB -> PENDATAAN -> DATA).")
        print("Ketika tabel data sudah muncul di layar browser,")
        print("kembali ke terminal ini dan tekan ENTER untuk mengakhiri probe.")
        print("="*70 + "\n")
        
        input(">>> TEKAN ENTER DI SINI UNTUK SELESAI PROBING... <<<")
        
        context.close()

if __name__ == "__main__":
    run_probe()
