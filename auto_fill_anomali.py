import asyncio
import pandas as pd
from playwright.async_api import async_playwright
import sys
import glob

# Impor dari session_manager_petugas yang sudah ada untuk login
# Kita modifikasi sedikit agar cocok dengan async
from petugas.login import login_with_sso

async def fill_anomali(csv_file, keterangan_text):
    df = pd.read_csv(csv_file)
    if 'link_assignment' not in df.columns:
        print(f"Error: Tidak ada kolom 'link_assignment' di {csv_file}")
        return

    username = 'moh.syafrizal'
    password = 'Sulteng2025!'

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False) # Set True jika tidak ingin melihat browser
        context = await browser.new_context()
        page = await context.new_page()

        print(f"Melakukan login...")
        await page.goto("https://sso.bps.go.id/auth/realms/pegawai-bps/protocol/openid-connect/auth?client_id=fasih-kegiatan-vue&redirect_uri=https%3A%2F%2Ffasih-sm.bps.go.id%2Fapp%2Fauth&state=a4427506-69e5-4ba8-9d87-fb2d42777174&response_mode=fragment&response_type=code&scope=openid&nonce=bdfc2a69-65b1-4770-b97c-9b78297b812f")
        await page.fill('#username', username)
        await page.fill('#password', password)
        await page.click('#kc-login')
        
        # Tunggu sampai masuk dashboard FASIH
        await page.wait_for_url("**/app/dashboard", timeout=60000)
        print("Login berhasil!")

        for index, row in df.iterrows():
            link = row['link_assignment']
            if pd.isna(link):
                continue
                
            print(f"[{index+1}/{len(df)}] Membuka: {link}")
            await page.goto(link)
            
            # TODO: Ganti selector CSS di bawah ini sesuai dengan elemen asli di web FASIH
            # Misal tombol tambah catatan:
            # await page.click('button:has-text("Catatan")')
            
            # Misal kolom input teks catatan:
            # await page.fill('textarea[name="catatan"]', keterangan_text)
            
            # Misal tombol simpan:
            # await page.click('button:has-text("Simpan")')
            
            print(f" Berhasil mengisi keterangan: {keterangan_text}")
            await page.wait_for_timeout(2000) # Jeda antar request

        await browser.close()

if __name__ == "__main__":
    print("Script ini adalah kerangka dasar. Harap sesuaikan selector CSS pada bagian TODO sebelum dijalankan.")
    # Contoh penggunaan:
    # asyncio.run(fill_anomali('anomali/sqllab_untitled_query_20_20260819T090357.csv', 'Metadata masih salah'))
