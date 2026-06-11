import asyncio
import json
import os
import socket
from urllib.parse import unquote
from playwright.async_api import async_playwright

PROV_GROUP_ID = "a45adac1-e711-4c15-b3f9-1f30fc151565"

# Daftar Kode Kabupaten di Sulteng
KAB_CODES = {
    "7201": "[01] BANGGAI KEPULAUAN",
    "7202": "[02] BANGGAI",
    "7203": "[03] MOROWALI",
    "7204": "[04] POSO",
    "7205": "[05] DONGGALA",
    "7206": "[06] TOLI-TOLI",
    "7207": "[07] BUOL",
    "7208": "[08] PARIGI MOUTONG",
    "7209": "[09] TOJO UNA-UNA",
    "7210": "[10] SIGI",
    "7211": "[11] BANGGAI LAUT",
    "7212": "[12] MOROWALI UTARA",
    "7271": "[71] PALU"
}

def check_port_open(port=9222):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
    except:
        return False

async def fetch_kecamatan(page, token, kab_code):
    url = f"https://fasih-sm.bps.go.id/app/api/region/api/v1/region/level3?groupId={PROV_GROUP_ID}&level2FullCode={kab_code}"
    try:
        res = await page.evaluate("""
            async ({url, token}) => {
                try {
                    const r = await fetch(url, { headers: { "X-XSRF-TOKEN": token } });
                    if (!r.ok) return { _error: `HTTP ${r.status}` };
                    return await r.json();
                } catch (err) {
                    return { _error: err.toString() };
                }
            }
        """, {"url": url, "token": token})
        return res
    except Exception as e:
        return {"_error": str(e)}

async def main():
    async with async_playwright() as p:
        if not check_port_open(9222):
            print("[ERROR] Chrome tidak terdeteksi di port 9222.")
            print("Pastikan script scrape utamamu sedang jalan atau jalankan Chrome dengan remote debugging.")
            return

        print("Terhubung ke Chrome yang sudah jalan di background...")
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0] if browser.contexts else await browser.new_context()
        page = context.pages[0] if context.pages else await context.new_page()

        # Cari tab fasih yang aktif
        for p_page in context.pages:
            if "fasih-sm.bps.go.id" in p_page.url:
                page = p_page
                break

        if "fasih-sm.bps.go.id" not in page.url:
            await page.goto("https://fasih-sm.bps.go.id/app/dashboard")

        # Ambil Token
        cookies = await context.cookies()
        token_raw = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
        
        if not token_raw:
            print("\n[WARNING] Token tidak ditemukan. Pastikan kamu sudah login ke FASIH di Chrome.")
            return

        token = unquote(token_raw)
        print("\n[INFO] Token valid! Mulai menarik data Kecamatan...")

        full_map = {}

        for code, name in KAB_CODES.items():
            print(f"  -> Menarik Kecamatan untuk {name}...")
            data = await fetch_kecamatan(page, token, code)
            
            if data and "_error" not in data:
                # Menangani berbagai kemungkinan format response JSON
                kecamatan_list = []
                raw_list = data.get('data', []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
                
                for kec in raw_list:
                    kecamatan_list.append({
                        "id": kec.get("id"),
                        "name": kec.get("name")
                    })
                
                full_map[code] = {
                    "kab_name": name,
                    "kecamatan": kecamatan_list
                }
            else:
                print(f"     [GAGAL] {data.get('_error', 'Unknown Error')}")
            
            await asyncio.sleep(0.5) # Jeda sopan santun ke server

        with open("region_map_sulteng.json", "w") as f:
            json.dump(full_map, f, indent=4)
            
        print("\n✅ SELESAI! Data berhasil disimpan di region_map_sulteng.json")
        
        # Print sedikit contoh hasilnya biar kita bisa lihat bareng
        print("\n[DEBUG] Contoh hasil (Kabupaten 7201):")
        print(json.dumps(full_map.get("7201", {}), indent=2)[:500])

if __name__ == "__main__":
    asyncio.run(main())