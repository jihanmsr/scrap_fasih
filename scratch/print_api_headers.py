import time
import logging
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

USER_DATA_DIR = "playwright_chrome_profile"
TARGET_URL = "https://fasih-sm.bps.go.id/app/surveys/ecddb52e-f392-403c-a963-47391f217010/37526b20-81c8-42f5-a895-6190137d7394/data"

def print_headers():
    with sync_playwright() as p:
        logging.info("Membuka browser...")
        context = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,
            viewport={"width": 1280, "height": 800}
        )
        page = context.pages[0] if context.pages else context.new_page()

        # Inject script to override window.fetch and log API requests/responses
        page.add_init_script("""
            const originalFetch = window.fetch;
            window.fetch = async function(...args) {
                const url = args[0];
                const options = args[1] || {};
                console.log(`[FETCH REQUEST] URL: ${url} | Method: ${options.method || 'GET'}`);
                if (options.body) {
                    console.log(`[FETCH REQUEST BODY]: ${options.body}`);
                }
                const response = await originalFetch.apply(this, args);
                const clone = response.clone();
                try {
                    const json = await clone.json();
                    console.log(`[FETCH RESPONSE] URL: ${url} | JSON:`, JSON.stringify(json).substring(0, 1000));
                } catch (e) {
                    try {
                        const text = await clone.text();
                        console.log(`[FETCH RESPONSE] URL: ${url} | Text:`, text.substring(0, 200));
                    } catch (err) {}
                }
                return response;
            };
        """)

        # Listen to browser console logs and print them in Python log
        page.on("console", lambda msg: logging.info(f"BROWSER CONSOLE: {msg.text}"))

        logging.info(f"Membuka halaman target: {TARGET_URL}")
        try:
            page.goto(TARGET_URL, timeout=120000, wait_until="domcontentloaded")
        except Exception as e:
            logging.warning(f"Timeout/Error saat navigasi: {e}")

        print("\n" + "="*80)
        print("Tunggu sampai halaman termuat sempurna.")
        print("Silakan klik tombol filter, pilih Provinsi SULAWESI TENGAH, lalu klik dropdown Kabupaten/Kota.")
        print("Perhatikan log console BROWSER CONSOLE di bawah untuk melihat response fetch wilayah!")
        print("Tekan ENTER di sini jika sudah selesai untuk menutup browser.")
        print("="*80 + "\n")
        input("Tekan ENTER...")

        context.close()

if __name__ == "__main__":
    print_headers()



