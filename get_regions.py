import asyncio
import json
import os
import socket
from urllib.parse import unquote
from playwright.async_api import async_playwright

USER_DATA_DIR = "playwright_chrome_profile_mapping" # Pakai folder beda jika harus launch baru
PROV_ID = "5214ecb2-bef1-4a86-9446-451cf430928e" 

def check_port_open(port=9222):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
    except:
        return False

async def fetch_region_metadata(page, token, region_id):
    url = f"https://fasih-sm.bps.go.id/app/api/region/api/v1/region-metadata?id={region_id}"
    try:
        res = await page.evaluate("""
            async ({url, token}) => {
                const r = await fetch(url, {
                    headers: { "X-XSRF-TOKEN": token }
                });
                if (!r.ok) return null;
                return await r.json();
            }
        """, {"url": url, "token": token})
        return res
    except Exception as e:
        print(f"Error fetching region {region_id}: {e}")
        return None

async def main():
    async with async_playwright() as p:
        browser = None
        context = None
        page = None

        if check_port_open(9222):
            print("Terhubung ke Chrome yang sudah jalan di background...")
            browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            context = browser.contexts[0] if browser.contexts else await browser.new_context()
            page = context.pages[0] if context.pages else await context.new_page()
        else:
            print("Meluncurkan browser sementara...")
            browser = await p.chromium.launch_persistent_context(
                user_data_dir=os.path.abspath(USER_DATA_DIR),
                headless=False,
                args=["--no-first-run", "--no-default-browser-check"]
            )
            context = browser
            page = browser.pages[0] if browser.pages else await browser.new_page()
            
        # Cari tab fasih yang aktif
        for p_page in context.pages:
            if "fasih-sm.bps.go.id" in p_page.url:
                page = p_page
                break

        if "fasih-sm.bps.go.id" not in page.url:
            await page.goto("https://fasih-sm.bps.go.id/app/dashboard")
            await asyncio.sleep(3) 
        
        cookies = await context.cookies()
        token_raw = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
        
        if not token_raw:
            print("Gagal mendapatkan token. Pastikan tab FASIH sudah login, lalu jalankan ulang script ini.")
            return

        token = unquote(token_raw)
        print("Token didapat. Mulai mapping wilayah...")

        # 1. Ambil data Kabupaten di dalam Provinsi Sulteng
        prov_data = await fetch_region_metadata(page, token, PROV_ID)
        if not prov_data or 'children' not in prov_data:
            print("Gagal mengambil data provinsi.")
            return

        kab_list = prov_data['children']
        print(f"Ditemukan {len(kab_list)} Kabupaten.")

        full_map = {}
        
        # 2. Iterasi per Kabupaten untuk ambil Kecamatan
        for kab in kab_list:
            kab_id = kab['id']
            kab_name = kab.get('name', 'Unknown')
            print(f"  Memproses Kab: {kab_name}")
            
            kab_data = await fetch_region_metadata(page, token, kab_id)
            kec_list = kab_data.get('children', []) if kab_data else []
            
            kec_map = []
            for kec in kec_list:
                kec_map.append({
                    "id": kec['id'],
                    "name": kec.get('name', 'Unknown')
                })
            
            full_map[kab_id] = {
                "name": kab_name,
                "kecamatan": kec_map
            }
            await asyncio.sleep(0.5) 

        # Simpan hasilnya
        with open("region_map_sulteng.json", "w") as f:
            json.dump(full_map, f, indent=4)
            
        print("Pemetaan selesai. Tersimpan di region_map_sulteng.json")

if __name__ == "__main__":
    asyncio.run(main())