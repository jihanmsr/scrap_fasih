import json
import logging
import time
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

USER_DATA_DIR = "playwright_chrome_profile"

def fetch_level2_regions():
    with sync_playwright() as p:
        logging.info("Membuka browser...")
        context = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False
        )
        page = context.pages[0] if context.pages else context.new_page()

        # Buka page
        page.goto("https://fasih-sm.bps.go.id/app/surveys/ecddb52e-f392-403c-a963-47391f217010/37526b20-81c8-42f5-a895-6190137d7394/data", wait_until="domcontentloaded")
        
        print("\n" + "="*80)
        print("Tunggu sampai halaman utama muncul.")
        print("Tekan ENTER di terminal ini jika sudah login dan data tampil.")
        print("="*80 + "\n")
        input("Tekan ENTER...")

        # Ambil region list menggunakan fetch di browser dengan level=2
        js_code = """
        async () => {
            const tokenCookie = document.cookie.split('; ').find(row => row.startsWith('XSRF-TOKEN='));
            const token = tokenCookie ? decodeURIComponent(tokenCookie.split('=')[1]) : "";
            const url = "https://fasih-sm.bps.go.id/app/api/region/api/v1/region/custom-by-smallest-code-and-level?groupId=6b0b053f-aa43-4855-ac8f-26857b735c93&smallestLevelFullCode=72&level=2";
            const res = await fetch(url, {
                headers: {
                    "X-XSRF-TOKEN": token
                }
            });
            return await res.json();
        }
        """
        try:
            regions_data = page.evaluate(js_code)
            with open("scratch/regions_level2_dump.json", "w", encoding="utf-8") as f:
                json.dump(regions_data, f, indent=4)
            logging.info("Berhasil menyimpan data wilayah level 2 ke scratch/regions_level2_dump.json")
        except Exception as e:
            logging.error(f"Gagal mengambil wilayah level 2: {e}")

        context.close()

if __name__ == "__main__":
    fetch_level2_regions()
