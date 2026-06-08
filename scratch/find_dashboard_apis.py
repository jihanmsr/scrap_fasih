import asyncio
import json
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            contexts = browser.contexts
            if not contexts:
                print("Tidak ada context aktif.")
                return
            context = contexts[0]
            pages = context.pages
            if not pages:
                print("Tidak ada tab aktif.")
                return
            
            # Cari tab FASIH
            page = None
            for pg in pages:
                if "fasih-sm.bps.go.id" in pg.url:
                    page = pg
                    break
            
            if not page:
                print("Tab FASIH tidak ditemukan.")
                return
            
            print(f"Menggunakan tab: {page.url}")
            
            # Kita bisa menjalankan script di console untuk mendapatkan request fetch dari performance observer
            entries = await page.evaluate("""() => {
                const p = performance.getEntriesByType("resource");
                return p.filter(e => e.name.includes("api")).map(e => e.name);
            }""")
            
            print("API yang dipanggil di halaman ini:")
            for e in set(entries):
                print("-", e)
                
        except Exception as e:
            print("Error:", e)

asyncio.run(main())
