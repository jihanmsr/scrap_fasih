import os
import time
import logging
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

USER_DATA_DIR = "playwright_chrome_profile"

def run_inspect():
    with sync_playwright() as p:
        logging.info("Membuka browser...")
        context = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False
        )
        page = context.pages[0] if context.pages else context.new_page()
        
        page.goto("https://fasih-sm.bps.go.id/app/surveys/ecddb52e-f392-403c-a963-47391f217010/37526b20-81c8-42f5-a895-6190137d7394/data")
        
        print("\n" + "="*70)
        print("SILAKAN LOGIN SSO & NAVIGASI SAMPAI HALAMAN DATA TAMPIL.")
        print("Setelah itu, silakan KLIK tombol filter wilayah di browser.")
        print("Setelah filter terbuka, kembali ke sini dan tekan ENTER.")
        print("="*70 + "\n")
        
        input(">>> Tekan ENTER setelah filter wilayah dibuka di browser... <<<")
        
        # Ambil HTML popover/dialog yang sedang aktif
        logging.info("Mengambil HTML popover/dialog...")
        
        # Kita cari elemen dialog atau popover
        popovers = page.locator("div[role='dialog'], div[role='menu'], div.f\\:popover, [data-state='open']").all()
        logging.info(f"Ditemukan {len(popovers)} elemen popover/dialog terbuka.")
        for idx, pop in enumerate(popovers):
            print(f"\n--- POPOVER {idx+1} ---")
            print("Tag name:", pop.evaluate("el => el.tagName"))
            print("Class list:", pop.evaluate("el => el.className"))
            print("Inner HTML (first 2000 chars):")
            print(pop.inner_html()[:2000])
            
        context.close()

if __name__ == "__main__":
    run_inspect()
