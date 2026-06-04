import json
import logging
import time
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

USER_DATA_DIR = "playwright_chrome_profile"

def inspect_attributes():
    with sync_playwright() as p:
        logging.info("Membuka browser...")
        context = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False
        )
        page = context.pages[0] if context.pages else context.new_page()

        logging.info("Navigasi ke halaman target...")
        page.goto("https://fasih-sm.bps.go.id/app/surveys/ecddb52e-f392-403c-a963-47391f217010/37526b20-81c8-42f5-a895-6190137d7394/data")
        
        logging.info("Menunggu halaman masuk/login dan tombol filter tampil (maksimal 90 detik)...")
        try:
            filter_btn = page.locator("button").filter(has=page.locator("svg.tabler-icon-filter")).first
            filter_btn.wait_for(state="visible", timeout=90000)
            logging.info("Tombol filter terdeteksi! Melanjutkan analisis...")
            time.sleep(2)
        except Exception as e:
            logging.error(f"Gagal mendeteksi tombol filter: {e}")
            context.close()
            return

        try:
            # 1. Buka filter
            filter_btn.click(force=True)
            time.sleep(2)

            # Helper function to select dropdown option
            def select_dropdown_option(target_text):
                page.wait_for_selector("[cmdk-item], div[role='option']", timeout=30000)
                options = page.locator("[cmdk-item], div[role='option']").all()
                for opt in options:
                    opt_text = opt.inner_text().strip()
                    if target_text.upper() in opt_text.upper():
                        opt.click(force=True)
                        return True
                return False

            # 2. Klik dropdown Provinsi (index 0) dan pilih SULAWESI TENGAH
            dropdown_buttons = page.locator("div[role='dialog'] button.f\\:justify-between, [data-radix-portal] button.f\\:justify-between").all()
            dropdown_buttons[0].click(force=True)
            time.sleep(1.5)
            select_dropdown_option("SULAWESI TENGAH")
            time.sleep(2)

            # 3. Klik dropdown Kabupaten/Kota (index 1)
            dropdown_buttons = page.locator("div[role='dialog'] button.f\\:justify-between, [data-radix-portal] button.f\\:justify-between").all()
            dropdown_buttons[1].click(force=True)
            page.wait_for_selector("[cmdk-item], div[role='option']", timeout=30000)
            time.sleep(1.5)

            # 4. Ambil semua opsi dan kumpulkan semua atributnya
            kab_options = page.locator("div[role='option'], [cmdk-item]").all()
            attributes_data = []
            for opt in kab_options:
                attrs = opt.evaluate("""
                    el => {
                        const obj = {};
                        for (let attr of el.attributes) {
                            obj[attr.name] = attr.value;
                        }
                        return {
                            innerHTML: el.innerHTML,
                            innerText: el.innerText,
                            attributes: obj
                        };
                    }
                """)
                attributes_data.append(attrs)

            with open("scratch/options_attrs.json", "w", encoding="utf-8") as f:
                json.dump(attributes_data, f, indent=4)
            logging.info("Berhasil menyimpan data atribut ke scratch/options_attrs.json")
        except Exception as e:
            logging.error(f"Gagal inspect atribut: {e}")

        context.close()

if __name__ == "__main__":
    inspect_attributes()
