import asyncio
import json
import os
import sys
import time
import socket
from urllib.parse import unquote
from playwright.async_api import async_playwright

PROV_GROUP_ID = "a45adac1-e711-4c15-b3f9-1f30fc151565"
PROV_CODE = "72"  # Sulawesi Tengah
OUTPUT_FILE = "region_map_sulteng_full.json"
CONCURRENCY_LIMIT = 15

# Static Kabupaten map for naming consistency
KAB_NAMES = {
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

def check_port_open(port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1.0)
            return s.connect_ex(('127.0.0.1', port)) == 0
    except Exception:
        return False

async def fetch_api(sem, page, token, url):
    async with sem:
        for attempt in range(4):
            try:
                res = await page.evaluate("""
                    async ({url, token}) => {
                        try {
                            const r = await fetch(url, { headers: { "X-XSRF-TOKEN": token } });
                            if (!r.ok) return { _error: `HTTP ${r.status}` };
                            const json = await r.ok ? await r.json() : null;
                            return json && json.success ? json.data : { _error: "Invalid JSON response structure" };
                        } catch (e) {
                            return { _error: e.toString() };
                        }
                    }
                """, {"url": url, "token": token})
                
                if res and isinstance(res, dict) and "_error" in res:
                    # Retry on error
                    await asyncio.sleep(0.5 * (attempt + 1))
                    continue
                return res
            except Exception as e:
                await asyncio.sleep(0.5 * (attempt + 1))
        return None

async def main():
    # 1. Detect open Chrome debugging port
    port = None
    for p in [9223, 9222]:
        if check_port_open(p):
            port = p
            break
            
    if not port:
        print("[ERROR] Chrome remote debugging tidak terdeteksi pada port 9222 maupun 9223.")
        print("Pastikan Chrome sudah terbuka dengan flag debugging.")
        sys.exit(1)
        
    print(f"[INFO] Terhubung ke Chrome pada port {port}...")
    
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
        context = browser.contexts[0]
        
        # Cari tab fasih yang aktif
        page = None
        for p_page in context.pages:
            if "fasih-sm.bps.go.id" in p_page.url:
                page = p_page
                break
                
        if not page:
            page = context.pages[0] if context.pages else await context.new_page()
            await page.goto("https://fasih-sm.bps.go.id/app/dashboard")
            
        # Dapatkan token XSRF
        cookies = await context.cookies()
        token_raw = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
        
        if not token_raw:
            print("[ERROR] XSRF-TOKEN tidak ditemukan. Silakan login ke FASIH di browser terlebih dahulu.")
            await browser.close()
            sys.exit(1)
            
        token = unquote(token_raw)
        print("[INFO] Token berhasil diambil. Memulai proses scraping...")
        
        sem = asyncio.Semaphore(CONCURRENCY_LIMIT)
        
        # --- LANGKAH 1: Ambil Kabupaten ---
        print("\n[1/4] Mengambil daftar Kabupaten/Kota di Sulawesi Tengah...")
        kab_url = f"https://fasih-sm.bps.go.id/app/api/region/api/v1/region/level2?groupId={PROV_GROUP_ID}&level1FullCode={PROV_CODE}"
        kab_data = await fetch_api(sem, page, token, kab_url)
        
        if not kab_data:
            print("[ERROR] Gagal mengambil data Kabupaten/Kota.")
            await browser.close()
            sys.exit(1)
            
        print(f"      Ditemukan {len(kab_data)} Kabupaten/Kota.")
        
        # Inisialisasi struktur
        region_tree = {
            "prov_code": PROV_CODE,
            "prov_name": "SULAWESI TENGAH",
            "kabupaten": {}
        }
        
        # --- LANGKAH 2: Ambil Kecamatan (Level 3) ---
        print("\n[2/4] Mengambil daftar Kecamatan untuk setiap Kabupaten/Kota...")
        kec_tasks = []
        kab_mapping = {}
        for kab in kab_data:
            kab_code = kab["fullCode"]
            kab_name = KAB_NAMES.get(kab_code, kab["name"])
            kab_mapping[kab_code] = {"name": kab_name, "id": kab["id"]}
            
            kec_url = f"https://fasih-sm.bps.go.id/app/api/region/api/v1/region/level3?groupId={PROV_GROUP_ID}&level2FullCode={kab_code}"
            kec_tasks.append(fetch_api(sem, page, token, kec_url))
            
        kec_results = await asyncio.gather(*kec_tasks)
        
        total_kec_count = 0
        kec_to_fetch = []  # List of (kab_code, kec_code, kec_name, kec_id)
        
        for kab_code, k_res in zip(kab_mapping.keys(), kec_results):
            if not k_res:
                print(f"      [WARNING] Gagal mengambil kecamatan untuk Kab. {kab_code}")
                continue
                
            kab_info = kab_mapping[kab_code]
            region_tree["kabupaten"][kab_code] = {
                "kab_id": kab_info["id"],
                "kab_name": kab_info["name"],
                "kecamatan": {}
            }
            
            for kec in k_res:
                kec_code = kec["fullCode"]
                region_tree["kabupaten"][kab_code]["kecamatan"][kec_code] = {
                    "kec_id": kec["id"],
                    "kec_name": kec["name"],
                    "desa": {}
                }
                kec_to_fetch.append((kab_code, kec_code, kec["name"], kec["id"]))
                total_kec_count += 1
                
        print(f"      Ditemukan total {total_kec_count} Kecamatan.")
        
        # --- LANGKAH 3: Ambil Desa (Level 4) ---
        print("\n[3/4] Mengambil daftar Desa/Kelurahan untuk setiap Kecamatan...")
        desa_tasks = []
        for kab_code, kec_code, kec_name, kec_id in kec_to_fetch:
            desa_url = f"https://fasih-sm.bps.go.id/app/api/region/api/v1/region/level4?groupId={PROV_GROUP_ID}&level3FullCode={kec_code}"
            desa_tasks.append(fetch_api(sem, page, token, desa_url))
            
        # Jalankan parallel
        desa_results = []
        completed_count = 0
        
        # Agar monitoring progress lebih smooth, kita kumpulkan progress
        print(f"      Progress: 0/{len(kec_to_fetch)} Kecamatan selesai...")
        
        # Fetch chunked to show progress
        chunk_size = 30
        for i in range(0, len(desa_tasks), chunk_size):
            chunk = desa_tasks[i:i+chunk_size]
            chunk_res = await asyncio.gather(*chunk)
            desa_results.extend(chunk_res)
            completed_count += len(chunk)
            print(f"      Progress: {completed_count}/{len(kec_to_fetch)} Kecamatan selesai ({completed_count/len(kec_to_fetch)*100:.1f}%)")
            
        total_desa_count = 0
        desa_to_fetch = []  # List of (kab_code, kec_code, desa_code, desa_name, desa_id)
        
        for (kab_code, kec_code, kec_name, kec_id), d_res in zip(kec_to_fetch, desa_results):
            if not d_res:
                # Gagal fetch desa untuk kec ini
                continue
            for desa in d_res:
                desa_code = desa["fullCode"]
                region_tree["kabupaten"][kab_code]["kecamatan"][kec_code]["desa"][desa_code] = {
                    "desa_id": desa["id"],
                    "desa_name": desa["name"],
                    "sls": []
                }
                desa_to_fetch.append((kab_code, kec_code, desa_code, desa["name"], desa["id"]))
                total_desa_count += 1
                
        print(f"      Ditemukan total {total_desa_count} Desa/Kelurahan.")
        
        # --- LANGKAH 4: Ambil SLS (Level 5) ---
        print("\n[4/4] Mengambil daftar SLS untuk setiap Desa/Kelurahan...")
        sls_tasks = []
        for kab_code, kec_code, desa_code, desa_name, desa_id in desa_to_fetch:
            sls_url = f"https://fasih-sm.bps.go.id/app/api/region/api/v1/region/level5?groupId={PROV_GROUP_ID}&level4FullCode={desa_code}"
            sls_tasks.append(fetch_api(sem, page, token, sls_url))
            
        sls_results = []
        completed_desa = 0
        total_sls_count = 0
        
        print(f"      Progress: 0/{len(desa_to_fetch)} Desa selesai...")
        
        # Fetch chunked to show progress
        chunk_size = 50
        for i in range(0, len(sls_tasks), chunk_size):
            chunk = sls_tasks[i:i+chunk_size]
            chunk_res = await asyncio.gather(*chunk)
            sls_results.extend(chunk_res)
            completed_desa += len(chunk)
            print(f"      Progress: {completed_desa}/{len(desa_to_fetch)} Desa selesai ({completed_desa/len(desa_to_fetch)*100:.1f}%)")
            
        # Masukkan hasil SLS ke tree
        for (kab_code, kec_code, desa_code, desa_name, desa_id), s_res in zip(desa_to_fetch, sls_results):
            if not s_res:
                continue
            
            sls_list = []
            for sls in s_res:
                sls_list.append({
                    "sls_id": sls["id"],
                    "sls_code": sls["code"],
                    "sls_name": sls["name"],
                    "sls_full_code": sls["fullCode"]
                })
                total_sls_count += 1
                
            region_tree["kabupaten"][kab_code]["kecamatan"][kec_code]["desa"][desa_code]["sls"] = sls_list
            
        # Simpan ke file JSON
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(region_tree, f, indent=4, ensure_ascii=False)
            
        print(f"\n✅ DATA SCRAPING SELESAI!")
        print(f"💾 File hasil disimpan ke: {os.path.abspath(OUTPUT_FILE)}")
        print(f"📊 Ringkasan Statistik Sulteng:")
        print(f"   - Total Kabupaten/Kota: {len(region_tree['kabupaten'])}")
        print(f"   - Total Kecamatan     : {total_kec_count}")
        print(f"   - Total Desa          : {total_desa_count}")
        print(f"   - Total SLS           : {total_sls_count}")
        
        # Print breakdown tabel per kab
        print("\n" + "="*80)
        print(f"{'KABUPATEN/KOTA':<35} | {'KEC':<6} | {'DESA':<8} | {'SLS COUNT':<10}")
        print("-"*80)
        for kab_code, kab in sorted(region_tree["kabupaten"].items()):
            import re
            clean_name = re.sub(r'\[\d+\]\s*', '', kab["kab_name"]).strip()
            
            kec_count = len(kab["kecamatan"])
            desa_count = sum(len(kec["desa"]) for kec in kab["kecamatan"].values())
            sls_count = sum(
                sum(len(desa.get("sls", [])) for desa in kec["desa"].values())
                for kec in kab["kecamatan"].values()
            )
            print(f"{clean_name:<35} | {kec_count:<6} | {desa_count:<8} | {sls_count:<10}")
        print("="*80)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
