import time
from playwright.sync_api import sync_playwright

def inspect():
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        print(f"Total pages: {len(context.pages)}")
        for idx, page in enumerate(context.pages):
            print(f"Page {idx}: URL={page.url} | Title={page.title()}")
            # Ambil screenshot halaman saat ini
            try:
                screenshot_path = f"scratch/page_inspect_{idx}.png"
                page.screenshot(path=screenshot_path)
                print(f"  Screenshot saved to {screenshot_path}")
            except Exception as e:
                print(f"  Gagal mengambil screenshot: {e}")

if __name__ == "__main__":
    inspect()
