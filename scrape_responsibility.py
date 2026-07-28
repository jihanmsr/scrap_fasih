import subprocess
import asyncio
import json
import csv
from playwright.async_api import async_playwright
import os

DATATABLE_URL = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/report-progress-by-responsibility"

PAYLOAD_TEMPLATE = {
    "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24",
    "size": 10,
    "page": 0,
    "search": "",
    "target": "ALL",
    "region": {
        "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e",
        "region2Id": "4ab6ca2f-7952-4e8e-a94d-b6dd933e5d44",
        "region3Id": None,
        "region4Id": None,
        "region5Id": None,
        "region6Id": None,
        "region7Id": None,
        "region8Id": None,
        "region9Id": None,
        "region10Id": None
    },
    "regionSummaryLevel": 6
}

ROLES = {
    "Pencacah": "6d7d919a-45e5-4779-bb87-2905b49fd31a",
    "Pengawas": "93bcf446-c4c1-4462-8ed0-4b0f7ae89e52"
}

async def run():
    print("[INFO] Memulai tarikan RESPONSIBILITY dengan Playwright untuk bypass F5...")
    async with async_playwright() as p:
        abs_user_data_dir = os.path.abspath(os.environ.get("CHROME_PROFILE_DIR", "playwright_chrome_profile"))
        chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        
        context = await p.chromium.launch_persistent_context(
            user_data_dir=abs_user_data_dir,
            executable_path=chrome_path,
            headless=False,
            ignore_default_args=["--enable-automation"],
            args=["--no-first-run", "--no-default-browser-check", "--disable-blink-features=AutomationControlled"]
        )
        
        page = context.pages[0] if context.pages else await context.new_page()
        
        print("[INFO] Mengakses FASIH...")
        await page.goto("https://fasih-sm.bps.go.id/app/auth/login", timeout=120000)
        
        import re
        try:
            # Menggunakan regex baru karena URL BPS sudah berubah menjadi /app/surveys/...
            await page.wait_for_url(re.compile(r".*surveys.*"), timeout=5000)
            print("[INFO] Sudah login!")
        except:
            print("[WARNING] Anda belum login!")
            print("=========================================================================")
            print("  Silakan login ke web FASIH di jendela Chrome yang baru saja terbuka.")
            print("  Skrip ini akan otomatis menunggu sampai Anda berhasil login...")
            print("=========================================================================")
            
            try:
                await page.wait_for_url(re.compile(r".*surveys.*"), timeout=300000)
                print("[INFO] Berhasil login manual!")
                # Arahkan langsung ke URL dasbor baru untuk memastikan cookies F5 beres
                await page.goto("https://fasih-sm.bps.go.id/app/surveys/a0429e96-51a5-477b-a415-485f9c153004/fd68e454-ba45-4b85-8205-f3bf777ded24", timeout=120000)
                await page.wait_for_load_state("networkidle")
            except Exception as login_err:
                print(f"[ERROR] Gagal menunggu login manual: {login_err}")
                print("[ERROR] Waktu login habis atau halaman ditutup. Silakan ulangi.")
                await context.close()
                return

        await page.goto("https://fasih-sm.bps.go.id/app/analytic/assignment/assignment-status", timeout=120000)
        await page.wait_for_load_state("networkidle")
        
        cookies = await context.cookies()
        token = ""
        for c in cookies:
            if c["name"] == "XSRF-TOKEN":
                from urllib.parse import unquote
                token = unquote(c["value"])
                break

        if not token:
            print("[ERROR] Gagal mendapatkan token setelah login. Menghentikan skrip.")
            await context.close()
            return
            
        print(f"[INFO] Token berhasil didapatkan! Mulai menyedot data...")

        with open("/Users/jihanmaisaroh/scrap_fasih/region_map_sulteng_full.json", "r") as f:
            region_map = json.load(f)
            
        kabupaten_list = region_map.get("kabupaten", {})
        print(f"[INFO] Ditemukan {len(kabupaten_list)} Kabupaten/Kota untuk ditarik datanya.")

        all_results = []
        
        for role_name, role_id in ROLES.items():
            for kab_code, kab_info in kabupaten_list.items():
                kab_id = kab_info["kab_id"]
                kab_name = kab_info["kab_name"]
                
                current_page = 0
                print(f"\n======================================")
                print(f"Menarik Data Role: {role_name} - {kab_name}")
                print(f"======================================")
                retries = 0
                max_retries = 35
                
                while True:
                    print(f"    -> Mengambil halaman {current_page}...")
                    # Payload PERSIS seperti yang dikirim Chrome (semua region = null, size = 10)
                    payload = {
                        "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24",
                        "surveyRoleId": role_id,
                        "size": 10,
                        "page": current_page,
                        "search": "",
                        "target": "ALL",
                        "region": {
                            "region1Id": None, "region2Id": kab_id, "region3Id": None, 
                            "region4Id": None, "region5Id": None, "region6Id": None, 
                            "region7Id": None, "region8Id": None, "region9Id": None, "region10Id": None
                        },
                        "regionSummaryLevel": 6
                    }
                
                    try:
                        # Kita gunakan httpx sama seperti scrape_granular_core.py yang terbukti sukses menembus F5!
                        import httpx
                    
                        # Ambil cookies dari Playwright
                        cookies = await page.context.cookies()
                        token = ""
                        cookie_dict = {}
                        for c in cookies:
                            cookie_dict[c["name"]] = c["value"]
                            if c["name"] == "XSRF-TOKEN":
                                import urllib.parse
                                token = urllib.parse.unquote(c["value"])
                            
                        headers = {
                            "Accept": "*/*",
                            "Accept-Language": "en-US,en;q=0.9,id-ID;q=0.8,id;q=0.7",
                            "Content-Type": "application/json",
                            "Origin": "https://fasih-sm.bps.go.id",
                            "Priority": "u=1, i",
                            "Sec-CH-UA": '"Not;A=Brand";v="8", "Chromium";v="150", "Google Chrome";v="150"',
                            "Sec-CH-UA-Mobile": "?0",
                            "Sec-CH-UA-Platform": '"macOS"',
                            "Sec-Fetch-Dest": "empty",
                            "Sec-Fetch-Mode": "cors",
                            "Sec-Fetch-Site": "same-origin",
                            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/150.0.0.0",
                            "X-XSRF-TOKEN": token
                        }
                    
                        async with httpx.AsyncClient(http2=True, verify=False, timeout=60.0) as client:
                            # Set cookies manual
                            for k, v in cookie_dict.items():
                                client.cookies.set(k, v, domain="fasih-sm.bps.go.id")
                            
                            # Dump JSON tanpa spasi persis seperti browser
                            payload_str = json.dumps(payload, separators=(',', ':'))
                        
                            r = await client.post(DATATABLE_URL, content=payload_str, headers=headers)
                        
                            if r.status_code == 200:
                                # BUG FIX: r.json() ALREADY has "data" key!
                                res = {"api_response": r.json(), "status": 200}
                            else:
                                res = {"_error": f"HTTP {r.status_code} - {r.text}", "status": r.status_code}
                            
                    except Exception as e:
                        err_msg = repr(e)
                        print(f"[ERROR] Exception dari httpx: {err_msg}")
                        res = {"_error": err_msg or "Unknown Error", "status": 0}
                    
                    if res and "_error" in res:
                        retries += 1
                        print(f"[ERROR] Gagal mengambil halaman {current_page} (Percobaan {retries}/{max_retries}): {res.get('_error')}")
                    
                        if "504" not in res.get('_error', '') and "502" not in res.get('_error', ''):
                            print("[INFO] Terdeteksi blokir F5 WAF / Sesi mati. Memuat ulang halaman dasbor untuk mendapat cookie baru...")
                            try:
                                # URL baru dasbor survei (URL lama assignment-status sudah 404)
                                await page.goto("https://fasih-sm.bps.go.id/app/surveys/a0429e96-51a5-477b-a415-485f9c153004/fd68e454-ba45-4b85-8205-f3bf777ded24", timeout=120000)
                                await page.wait_for_load_state("networkidle")
                                cookies = await page.context.cookies()
                                for c in cookies:
                                    if c["name"] == "XSRF-TOKEN":
                                        from urllib.parse import unquote
                                        token = unquote(c["value"])
                                        print("[INFO] Token baru berhasil didapatkan!")
                                        break
                            except Exception as refr_e:
                                print(f"[ERROR] Gagal refresh token: {refr_e}")
                        
                        if retries >= max_retries:
                            print(f"[WARNING] Gagal total setelah {max_retries} percobaan di halaman {current_page}. Melewati halaman ini secara paksa agar script bisa lanjut!")
                            # --- AUTO-LOG MISSING PAGE ---
                            missing_log_file = "/Users/jihanmaisaroh/scrap_fasih/missing_pages_log.json"
                            missing_data = []
                            if os.path.exists(missing_log_file):
                                try:
                                    with open(missing_log_file, 'r') as mf:
                                        missing_data = json.load(mf)
                                except: pass
                            
                            new_entry = {"role": role_name, "kab_name": kab_name, "page": current_page}
                            if new_entry not in missing_data:
                                missing_data.append(new_entry)
                                with open(missing_log_file, 'w') as mf:
                                    json.dump(missing_data, mf, indent=4)
                            # -----------------------------
                            current_page += 1
                            retries = 0
                            continue
                        
                        wait_time = 15 if retries < 5 else 30
                        print(f"[INFO] Menunggu {wait_time} detik lalu mengulang...")
                        await asyncio.sleep(wait_time)
                        continue
                    
                    retries = 0 
                
                    # BUG FIX: extract from api_response -> data -> content
                    content = res.get("api_response", {}).get("data", {}).get("content", [])
                    if not content:
                        print(f"    [INFO] Selesai! Tidak ada data lagi setelah halaman {current_page-1}.")
                        break
                    
                    print(f"    [INFO] Sukses menarik {len(content)} data pada halaman {current_page}.")
                    for c in content:
                        c["assigned_role"] = role_name
                    all_results.extend(content)
                    current_page += 1
                    
                    # Tambah jeda 3 detik tiap halaman agar tidak dianggap SPAM oleh server
                    await asyncio.sleep(3.0)
            
                # --- PROGRESIF SAVE ---
                # Kita simpan CSV dan JS setiap kali selesai 1 Role, agar kalau error datanya tidak hilang!
                import datetime
                today_str = datetime.datetime.now().strftime("%Y-%m-%d")
                csv_file = f"/Users/jihanmaisaroh/scrap_fasih/fast_petugas_all_{today_str}.csv"
                with open(csv_file, mode='w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Email", "Role", "Region Code", "Total Target", "OPEN", "DRAFT", "SUBMITTED BY Pencacah", "SUBMITTED RESPONDENT", "APPROVED BY Pengawas", "REJECTED BY Pengawas", "REVOKED BY Pengawas", "EDITED BY Pengawas", "EDITED BY Admin Kabupaten", "REJECTED BY Admin Kabupaten", "COMPLETED BY Admin Kabupaten"])
                
                    for row in all_results:
                        email = row.get("email", "")
                        role = row.get("assigned_role", "")
                        for r_sum in row.get("regionSummary", []):
                            reg_code = r_sum.get("regionCode", "")
                            status_breakdown = r_sum.get("statusBreakdown", [])
                        
                            counts = { "OPEN": 0, "DRAFT": 0, "SUBMITTED BY PENCACAH": 0, "SUBMITTED RESPONDENT": 0, "APPROVED BY PENGAWAS": 0, "REJECTED BY PENGAWAS": 0, "REVOKED BY PENGAWAS": 0, "EDITED BY PENGAWAS": 0, "EDITED BY ADMIN KABUPATEN": 0, "REJECTED BY ADMIN KABUPATEN": 0, "COMPLETED BY ADMIN KABUPATEN": 0 }
                            total = r_sum.get("total", 0)
                            for st in status_breakdown:
                                st_name = st.get("status", "").upper()
                                if st_name in counts: counts[st_name] = st.get("count", 0)
                                else: counts[st_name] = st.get("count", 0)
                                
                            writer.writerow([ email, role, reg_code, total, counts.get("OPEN",0), counts.get("DRAFT",0), counts.get("SUBMITTED BY PENCACAH",0), counts.get("SUBMITTED RESPONDENT",0), counts.get("APPROVED BY PENGAWAS",0), counts.get("REJECTED BY PENGAWAS",0), counts.get("REVOKED BY PENGAWAS",0), counts.get("EDITED BY PENGAWAS",0), counts.get("EDITED BY ADMIN KABUPATEN",0), counts.get("REJECTED BY ADMIN KABUPATEN",0), counts.get("COMPLETED BY ADMIN KABUPATEN",0) ])
                        
                petugas_map = { "Pencacah": {}, "Pengawas": {} }
                for row in all_results:
                    email = row.get("email", "").strip().lower()
                    role = row.get("assigned_role", "")
                    if not email or not role: continue
                
                    if email not in petugas_map[role]:
                        petugas_map[role][email] = { "target": 0, "submitted_pencacah": 0, "submitted_respondent": 0, "approved": 0, "rejected": 0, "draft": 0, "open": 0, "revoked": 0, "edited_pengawas": 0, "edited_admin": 0, "completed_admin": 0, "sls_details": {} }
                    
                    for r_sum in row.get("regionSummary", []):
                        reg_code = r_sum.get("regionCode", "")
                        petugas_map[role][email]["target"] += r_sum.get("total", 0)
                    
                        if "sls_details" not in petugas_map[role][email]:
                            petugas_map[role][email]["sls_details"] = {}
                        if reg_code not in petugas_map[role][email]["sls_details"]:
                            petugas_map[role][email]["sls_details"][reg_code] = {"total": 0, "status": {}}
                        petugas_map[role][email]["sls_details"][reg_code]["total"] += r_sum.get("total", 0)

                        for st in r_sum.get("statusBreakdown", []):
                            s_name = st.get("status", "").upper()
                            s_count = st.get("count", 0)
                        
                            petugas_map[role][email]["sls_details"][reg_code]["status"][s_name] = petugas_map[role][email]["sls_details"][reg_code]["status"].get(s_name, 0) + s_count
                        
                            if s_name == "OPEN": petugas_map[role][email]["open"] += s_count
                            elif s_name == "DRAFT": petugas_map[role][email]["draft"] += s_count
                            elif s_name == "SUBMITTED BY PENCACAH": petugas_map[role][email]["submitted_pencacah"] += s_count
                            elif s_name == "SUBMITTED RESPONDENT": petugas_map[role][email]["submitted_respondent"] += s_count
                            elif "APPROVED" in s_name: petugas_map[role][email]["approved"] += s_count
                            elif "REJECTED BY ADMIN" in s_name: petugas_map[role][email]["rejected"] += s_count
                            elif "REJECTED" in s_name: petugas_map[role][email]["rejected"] += s_count
                            elif "REVOKED" in s_name: petugas_map[role][email]["revoked"] += s_count
                            elif "EDITED BY PENGAWAS" in s_name: petugas_map[role][email]["edited_pengawas"] += s_count
                            elif "EDITED BY ADMIN" in s_name: petugas_map[role][email]["edited_admin"] += s_count
                            elif "COMPLETED BY ADMIN" in s_name: petugas_map[role][email]["completed_admin"] += s_count

                import datetime, re
                history_file = "/Users/jihanmaisaroh/scrap_fasih/fast_petugas_history.js"
                history_map = {}
                if os.path.exists(history_file):
                    try:
                        with open(history_file, 'r') as f:
                            content = f.read()
                            start = content.find('{')
                            end = content.rfind('}') + 1
                            if start != -1 and end != 0: history_map = json.loads(content[start:end])
                    except Exception as e:
                        pass

                today_str = datetime.datetime.now().strftime("%Y-%m-%d")
                history_map[today_str] = petugas_map
            
                with open(history_file, "w", encoding='utf-8') as f: f.write(f"window.PETUGAS_HISTORY_MAP = {json.dumps(history_map, indent=4)};\n")
                with open("/Users/jihanmaisaroh/scrap_fasih/fast_petugas_progress.js", "w") as f: f.write(f"window.PETUGAS_PROGRESS_MAP = {json.dumps(petugas_map, indent=4)};\n")
            
                # --- START REGION MAP SAVE ---
                region_map = {}
                for row in all_results:
                    email = row.get("email", "").strip().lower()
                    role = row.get("assigned_role", "")
                    if not email or not role: continue
                
                    if email not in region_map:
                        region_map[email] = []
                    
                    for r_sum in row.get("regionSummary", []):
                        reg_code = r_sum.get("regionCode", "")
                        if reg_code and reg_code not in region_map[email]:
                            region_map[email].append(reg_code)
            
                with open("/Users/jihanmaisaroh/scrap_fasih/petugas_region_map.js", "w", encoding='utf-8') as f:
                    f.write(f"window.PETUGAS_REGION_MAP = {json.dumps(region_map)};\n")
                # --- END REGION MAP SAVE ---
            
                print(f"    [INFO] Auto-save progresif berhasil. Data aman.")
                # --- END PROGRESIF SAVE ---

        print(f"\n[SUCCESS] Berhasil ditarik semua!")

        # (Progressive save sudah menghandle CSV dan History JS)
        
        
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
    asyncio.run(run())
