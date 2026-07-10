import asyncio
import json
import os
import datetime
from playwright.async_api import async_playwright

REGION_MAP_PATH = "region_map_sulteng_full.json"
SE_UMUM_PERIOD = "fd68e454-ba45-4b85-8205-f3bf777ded24"
SE_UB_PERIOD = "37526b20-81c8-42f5-a895-6190137d7394"

async def ensure_login(page):
    """Pastikan user sudah login ke FASIH."""
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
    
    print("[INFO] Mengambil token sesi...")
    cookies = await page.context.cookies()
    token = next((c['value'] for c in cookies if c['name'] == 'XSRF-TOKEN'), None)
    if not token:
        print("[ERROR] XSRF-TOKEN tidak ditemukan!")
        return None
    return token

async def fetch_api(page, period_id, region1_id, region2_id=None, region3_id=None, region4_id=None):
    """Melakukan request fetch lewat evaluasi JS di dalam browser untuk menghindari anti-bot."""
    
    payload = {
        "surveyPeriodId": period_id,
        "assignmentStatusAlias": None,
        "assignmentErrorStatusType": -1,
        "data1": None, "data2": None, "data3": None, "data4": None, "data5": None,
        "data6": None, "data7": None, "data8": None, "data9": None, "data10": None,
        "regionId": region2_id,
        "region1Id": region1_id,
        "currentUserId": None,
        "userIdResponsibility": None
    }
    
    if region2_id: payload["region2Id"] = region2_id
    if region3_id: payload["region3Id"] = region3_id
    if region4_id: payload["region4Id"] = region4_id

    result = await page.evaluate(f'''async (payload) => {{
        const req = await fetch('https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/report-user-assignment', {{
            method: 'POST',
            headers: {{
                'content-type': 'application/json',
                'accept': 'application/json, text/plain, */*'
            }},
            body: JSON.stringify(payload)
        }});
        if (!req.ok) return null;
        return await req.json();
    }}''', payload)
    
    return result

async def main():
    if not os.path.exists(REGION_MAP_PATH):
        print(f"[ERROR] File {REGION_MAP_PATH} tidak ditemukan!")
        return
        
    with open(REGION_MAP_PATH, "r", encoding="utf-8") as f:
        region_map = json.load(f)
    
    SULTENG_ID = "5214ecb2-bef1-4a86-9446-451cf430928e" # UUID Provinsi Sulteng (Hardcoded for now, assuming standard)
    
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
        
        token = await ensure_login(page)
        if not token:
            await context.close()
            return
            
        print("[INFO] Memulai penarikan data MASTER ALOKASI (Kabupaten Level) secara cepat...")
        
        assign_data_umum = []
        assign_data_ub = []
        
        # Iterasi setiap Kabupaten
        for kab_code, kab_info in region_map['kabupaten'].items():
            kab_id = kab_info['kab_id']
            kab_name = kab_info['kab_name']
            
            print(f"  -> Mengambil total untuk Kabupaten: {kab_name} ({kab_code})")
            
            # --- SE UMUM ---
            res_umum = await fetch_api(page, SE_UMUM_PERIOD, SULTENG_ID, region2_id=kab_id)
            tot_umum = assigned_umum = havenot_umum = 0
            if res_umum:
                # res_umum berisi list kecamatan. Kita jumlahkan semuanya untuk dapat total Kabupaten
                for item in res_umum:
                    for val in item.get('values', []):
                        if val['label'] == 'total': tot_umum += val['value']
                        elif val['label'] == 'assigned': assigned_umum += val['value']
                        elif val['label'] == 'have-not-assigned': havenot_umum += val['value']
            
            assign_data_umum.append({
                "kode_kab": kab_code,
                "nama_kab": kab_name,
                "total": tot_umum,
                "assigned": assigned_umum,
                "have_not_assigned": havenot_umum,
                "timestamp": datetime.datetime.now().isoformat()
            })
            
            # --- SE UB ---
            res_ub = await fetch_api(page, SE_UB_PERIOD, SULTENG_ID, region2_id=kab_id)
            tot_ub = assigned_ub = havenot_ub = 0
            if res_ub:
                for item in res_ub:
                    for val in item.get('values', []):
                        if val['label'] == 'total': tot_ub += val['value']
                        elif val['label'] == 'assigned': assigned_ub += val['value']
                        elif val['label'] == 'have-not-assigned': havenot_ub += val['value']
                        
            assign_data_ub.append({
                "kode_kab": kab_code,
                "nama_kab": kab_name,
                "total": tot_ub,
                "assigned": assigned_ub,
                "have_not_assigned": havenot_ub,
                "timestamp": datetime.datetime.now().isoformat()
            })
            
            # Beri sedikit jeda agar tidak terlalu agresif
            await asyncio.sleep(0.5)
            
        print("[INFO] Selesai menarik Master Alokasi!")
        
        # Simpan ke file baru yang aman, tidak menimpa file aslinya
        js_content = f"window.ASSIGN_DATA_UMUM = {json.dumps(assign_data_umum, indent=4)};\n"
        js_content += f"window.ASSIGN_DATA_UB = {json.dumps(assign_data_ub, indent=4)};\n"
        
        with open("fast_master_assign_data.js", "w", encoding="utf-8") as f:
            f.write(js_content)
            
        print("[INFO] Hasil berhasil disimpan ke 'fast_master_assign_data.js'")
        print("[INFO] Jika Jihan ingin menarik sampai level Desa/SLS, kodenya bisa diperluas untuk me-loop ke level Desa.")
        
        await context.close()

if __name__ == "__main__":
    asyncio.run(main())
