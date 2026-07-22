import subprocess
import asyncio
import json
import os
import datetime
from playwright.async_api import async_playwright

REGION_MAP_PATH = "region_map_sulteng_full.json"
SE_UMUM_PERIOD = "fd68e454-ba45-4b85-8205-f3bf777ded24"
SE_UB_PERIOD = "37526b20-81c8-42f5-a895-6190137d7394"

async def ensure_login(page):
    print("[INFO] Membuka halaman login FASIH...")
    await page.goto("https://fasih-sm.bps.go.id/app/auth/login")
    try:
        import re
        await page.wait_for_url(re.compile(r".*survey.*"), timeout=5000)
        print("[INFO] Sudah login!")
    except:
        print("[INFO] Belum login. Silakan login di browser yang terbuka...")
        await page.wait_for_url(re.compile(r".*survey.*"), timeout=300000)
        print("[INFO] Berhasil login manual!")
    
    await page.goto("https://fasih-sm.bps.go.id/app/analytic/assignment/assignment-status")
    await page.wait_for_load_state("networkidle")
    return True

async def fetch_batch_desa(page, period_id, desa_list, batch_size=20):
    """
    desa_list = [
        {"kab_code": "7201", "kec_code": "...", "desa_code": "...", "desa_id": "...", "kab_id": "...", "kec_id": "..."}
    ]
    """
    results = []
    
    # Kumpulkan payload
    payloads = []
    for d in desa_list:
        payloads.append({
            "surveyPeriodId": period_id,
            "assignmentStatusAlias": None,
            "assignmentErrorStatusType": -1,
            "data1": None, "data2": None, "data3": None, "data4": None, "data5": None,
            "data6": None, "data7": None, "data8": None, "data9": None, "data10": None,
            "regionId": d['desa_id'],
            "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e", # Sulteng
            "region2Id": d['kab_id'],
            "region3Id": d['kec_id'],
            "region4Id": d['desa_id'],
            "currentUserId": None,
            "userIdResponsibility": None,
            "_meta": d # Titip meta data agar saat dikembalikan kita tahu ini desa apa
        })
    
    # Eksekusi per batch
    for i in range(0, len(payloads), batch_size):
        batch = payloads[i:i+batch_size]
        print(f"[FETCH] Memproses batch {i//batch_size + 1} / {(len(payloads)//batch_size) + 1} ({len(batch)} Desa)...")
        
        batch_res = await page.evaluate(f'''async (batchPayloads) => {{
            const fetchPromises = batchPayloads.map(async (p) => {{
                try {{
                    const req = await fetch('https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/report-user-assignment', {{
                        method: 'POST',
                        headers: {{
                            'content-type': 'application/json',
                            'accept': 'application/json, text/plain, */*'
                        }},
                        body: JSON.stringify(p)
                    }});
                    if (!req.ok) return {{ meta: p._meta, error: req.status }};
                    const data = await req.json();
                    return {{ meta: p._meta, data: data }};
                }} catch (e) {{
                    return {{ meta: p._meta, error: e.toString() }};
                }}
            }});
            return await Promise.all(fetchPromises);
        }}''', batch)
        
        results.extend(batch_res)
        await asyncio.sleep(0.5) # Jeda sedikit agar server tidak terlalu terbebani
        
    return results

def process_results(batch_results, region_map):
    # Struktur Master
    master = {}
    for res in batch_results:
        meta = res['meta']
        data = res.get('data')
        
        kab_code = meta['kab_code']
        kec_code = meta['kec_code']
        desa_code = meta['desa_code']
        
        kab_name = region_map['kabupaten'][kab_code]['kab_name']
        kec_name = region_map['kabupaten'][kab_code]['kecamatan'][kec_code]['kec_name']
        desa_name = region_map['kabupaten'][kab_code]['kecamatan'][kec_code]['desa'][desa_code]['desa_name']
        
        # Init struktur
        if kab_code not in master:
            master[kab_code] = {"name": kab_name, "total": 0, "assigned": 0, "unassigned": 0, "kecamatan": {}}
        if kec_code not in master[kab_code]['kecamatan']:
            master[kab_code]['kecamatan'][kec_code] = {"name": kec_name, "total": 0, "assigned": 0, "unassigned": 0, "desa": {}}
        if desa_code not in master[kab_code]['kecamatan'][kec_code]['desa']:
            master[kab_code]['kecamatan'][kec_code]['desa'][desa_code] = {"name": desa_name, "total": 0, "assigned": 0, "unassigned": 0, "sls": {}}
            
        desa_node = master[kab_code]['kecamatan'][kec_code]['desa'][desa_code]
        
        if not data:
            continue
            
        # Data berisi list SLS
        for sls_item in data:
            sls_full_code = sls_item['label']
            # Ambil 4 digit terakhir untuk kode SLS lokal
            sls_code = sls_full_code[-4:] if len(sls_full_code) >= 4 else sls_full_code
            
            # Cari nama SLS dari region_map
            sls_name = "N/A"
            sls_list = region_map['kabupaten'][kab_code]['kecamatan'][kec_code]['desa'][desa_code]['sls']
            for sls_obj in sls_list:
                if sls_obj['sls_full_code'] == sls_full_code:
                    sls_name = sls_obj['sls_name']
                    break
                    
            tot = assigned = havenot = 0
            for val in sls_item.get('values', []):
                if val['label'] == 'total': tot = val['value']
                elif val['label'] == 'assigned': assigned = val['value']
                elif val['label'] == 'have-not-assigned': havenot = val['value']
                
            desa_node['sls'][sls_code] = {
                "name": sls_name,
                "total": tot,
                "assigned": assigned,
                "unassigned": havenot
            }
            
            # Rollup (Akumulasi ke atas)
            desa_node['total'] += tot
            desa_node['assigned'] += assigned
            desa_node['unassigned'] += havenot
            
            master[kab_code]['kecamatan'][kec_code]['total'] += tot
            master[kab_code]['kecamatan'][kec_code]['assigned'] += assigned
            master[kab_code]['kecamatan'][kec_code]['unassigned'] += havenot
            
            master[kab_code]['total'] += tot
            master[kab_code]['assigned'] += assigned
            master[kab_code]['unassigned'] += havenot

    return master

async def main():
    if not os.path.exists(REGION_MAP_PATH):
        print(f"[ERROR] File {REGION_MAP_PATH} tidak ditemukan!")
        return
        
    with open(REGION_MAP_PATH, "r", encoding="utf-8") as f:
        region_map = json.load(f)
    
    # Siapkan daftar seluruh desa
    desa_list = []
    for kab_code, kab_info in region_map['kabupaten'].items():
        kab_id = kab_info['kab_id']
        for kec_code, kec_info in kab_info['kecamatan'].items():
            kec_id = kec_info['kec_id']
            for desa_code, desa_info in kec_info['desa'].items():
                desa_id = desa_info['desa_id']
                if not desa_id or desa_id == "-": continue
                
                desa_list.append({
                    "kab_code": kab_code,
                    "kec_code": kec_code,
                    "desa_code": desa_code,
                    "kab_id": kab_id,
                    "kec_id": kec_id,
                    "desa_id": desa_id
                })
                
    print(f"[INFO] Ditemukan {len(desa_list)} Desa untuk ditarik datanya.")
    
    async with async_playwright() as p:
        abs_user_data_dir = os.path.abspath("playwright_chrome_profile")
        chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        
        context = await p.chromium.launch_persistent_context(
            user_data_dir=abs_user_data_dir,
            executable_path=chrome_path,
            headless=False,
            ignore_default_args=["--enable-automation"],
            args=["--no-first-run", "--no-default-browser-check", "--disable-blink-features=AutomationControlled"]
        )
        page = context.pages[0] if context.pages else await context.new_page()
        
        logged_in = await ensure_login(page)
        if not logged_in:
            
        # Auto-push ke GitHub agar Vercel otomatis update
        print("\n🚀 Mengunggah data terbaru ke GitHub untuk update Vercel...")
        try:
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", "Auto-update data dari scraper"], check=True)
            subprocess.run(["git", "push", "origin", "main"], check=True)
            print("✅ Berhasil push ke GitHub! Website Vercel akan otomatis terupdate dalam ~30 detik.")
        except Exception as e:
            print(f"⚠️ Gagal push ke GitHub (Mungkin tidak ada perubahan data atau error git): {e}")
            
        print("\n🎉 PEMBARUAN SELESAI SECARA INSTAN!")

        await context.close()
            return
            
        print("\n[INFO] === MENARIK DATA SE UMUM ===")
        res_umum = await fetch_batch_desa(page, SE_UMUM_PERIOD, desa_list, batch_size=20)
        master_umum = process_results(res_umum, region_map)
        
        print("\n[INFO] === MENARIK DATA SE UB ===")
        res_ub = await fetch_batch_desa(page, SE_UB_PERIOD, desa_list, batch_size=20)
        master_ub = process_results(res_ub, region_map)
        
        # Simpan
        js_content = f"window.ASSIGN_SLS_DATA_UMUM = {json.dumps(master_umum, indent=4)};\n"
        js_content += f"window.ASSIGN_SLS_DATA_UB = {json.dumps(master_ub, indent=4)};\n"
        
        with open("fast_master_assign_sls.js", "w", encoding="utf-8") as f:
            f.write(js_content)
            
        print("\n[INFO] Hasil berhasil disimpan ke 'fast_master_assign_sls.js'")
        
        # Auto-push ke GitHub agar Vercel otomatis update
        print("\n🚀 Mengunggah data terbaru ke GitHub untuk update Vercel...")
        try:
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", "Auto-update data dari scraper"], check=True)
            subprocess.run(["git", "push", "origin", "main"], check=True)
            print("✅ Berhasil push ke GitHub! Website Vercel akan otomatis terupdate dalam ~30 detik.")
        except Exception as e:
            print(f"⚠️ Gagal push ke GitHub (Mungkin tidak ada perubahan data atau error git): {e}")
            
        print("\n🎉 PEMBARUAN SELESAI SECARA INSTAN!")

        await context.close()

if __name__ == "__main__":
    asyncio.run(main())
