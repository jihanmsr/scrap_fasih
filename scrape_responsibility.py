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
    "target": "TARGET_ONLY",
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
        await page.goto("https://fasih-sm.bps.go.id/app/auth/login")
        
        import re
        try:
            await page.wait_for_url(re.compile(r".*survey.*"), timeout=5000)
            print("[INFO] Sudah login!")
        except:
            print("[WARNING] Anda belum login!")
            print("=========================================================================")
            print("  Silakan login ke web FASIH di jendela Chrome yang baru saja terbuka.")
            print("  Skrip ini akan otomatis menunggu sampai Anda berhasil login...")
            print("=========================================================================")
            try:
                await page.wait_for_url(re.compile(r".*survey.*"), timeout=300000)
                print("[INFO] Berhasil login manual!")
            except Exception as e:
                print("[ERROR] Waktu login habis atau halaman ditutup. Silakan ulangi.")
                await context.close()
                return

        await page.goto("https://fasih-sm.bps.go.id/app/analytic/assignment/assignment-status")
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
        
        for kab_code, kab_data in kabupaten_list.items():
            kab_name = kab_data.get("kab_name")
            kab_id = kab_data.get("kab_id")
            
            print(f"\n======================================")
            print(f"Menarik Data Kabupaten: {kab_name}")
            print(f"======================================")
            
            for role_name, role_id in ROLES.items():
                current_page = 0
                print(f" -> Role: {role_name}")
                retries = 0
                max_retries = 35 # Increase retries but allow skip after this
                
                while True:
                    print(f"    -> Mengambil halaman {current_page}...")
                    payload = PAYLOAD_TEMPLATE.copy()
                    payload["surveyRoleId"] = role_id
                    payload["page"] = current_page
                    payload["region"]["region2Id"] = kab_id
                    
                    res = None
                    try:
                        res = await page.evaluate("""
                            async ({url, payload, token}) => {
                                try {
                                    const r = await fetch(url, {
                                        method: "POST",
                                        headers: { 
                                            "Content-Type": "application/json", 
                                            "X-XSRF-TOKEN": token,
                                            "Accept": "application/json, text/plain, */*"
                                        },
                                        body: JSON.stringify(payload)
                                    });
                                    if (!r.ok) {
                                        const text = await r.text();
                                        return { _error: `HTTP ${r.status}: ${text.substring(0, 200)}`, status: r.status };
                                    }
                                    const text = await r.text();
                                    try {
                                        return JSON.parse(text);
                                    } catch (e) {
                                        return { _error: `HTML Response (Bukan JSON): ${text.substring(0, 200)}...`, status: r.status };
                                    }
                                } catch (e) {
                                    return { _error: e.toString(), status: 0 };
                                }
                            }
                        """, {"url": DATATABLE_URL, "payload": payload, "token": token})
                    except Exception as e:
                        print(f"[ERROR] Exception dari Python Playwright: {e}")
                        res = {"_error": str(e), "status": 0}
                    
                    if res and res.get("_error"):
                        retries += 1
                        print(f"[ERROR] Gagal mengambil halaman {current_page} (Percobaan {retries}/{max_retries}): {res.get('_error')}")
                        
                        if "HTML Response" in res.get('_error') or "Unauthenticated" in res.get('_error'):
                            print("[INFO] Terdeteksi sesi/token mati. Mencoba refresh halaman untuk mengambil token baru...")
                            try:
                                await page.goto("https://fasih-sm.bps.go.id/app/analytic/assignment/assignment-status")
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
                            current_page += 1
                            retries = 0
                            continue
                        
                        wait_time = 5 if retries < 5 else 15
                        print(f"[INFO] Menunggu {wait_time} detik lalu mengulang...")
                        await asyncio.sleep(wait_time)
                        continue
                    
                    retries = 0 
                        
                    content = res.get("data", {}).get("content", [])
                    if not content:
                        print(f"    [INFO] Selesai! Tidak ada data lagi setelah halaman {current_page-1}.")
                        break
                        
                    for c in content:
                        c["assigned_role"] = role_name
                    all_results.extend(content)
                    current_page += 1
                    await asyncio.sleep(1.0)
            
            # --- PROGRESIF SAVE ---
            # Kita simpan CSV dan JS setiap kali selesai 1 Kabupaten, agar kalau error datanya tidak hilang!
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
                    petugas_map[role][email] = { "target": 0, "submitted_pencacah": 0, "submitted_respondent": 0, "approved": 0, "rejected": 0, "draft": 0, "open": 0, "revoked": 0, "edited_pengawas": 0, "edited_admin": 0, "completed_admin": 0 }
                    
                for r_sum in row.get("regionSummary", []):
                    petugas_map[role][email]["target"] += r_sum.get("total", 0)
                    for st in r_sum.get("statusBreakdown", []):
                        s_name = st.get("status", "").upper()
                        s_count = st.get("count", 0)
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
            
            with open(history_file, "w", encoding='utf-8') as f: f.write(f"window.PETUGAS_HISTORY_MAP = {json.dumps(history_map, indent=4)};\\n")
            with open("/Users/jihanmaisaroh/scrap_fasih/fast_petugas_progress.js", "w") as f: f.write(f"window.PETUGAS_PROGRESS_MAP = {json.dumps(petugas_map, indent=4)};\\n")
            print(f"    [INFO] Auto-save progresif berhasil untuk {kab_name}. Data aman.")
            # --- END PROGRESIF SAVE ---

        print(f"\\n[SUCCESS] Berhasil ditarik semua!")

        # (Progressive save sudah menghandle CSV dan History JS)
        
        await context.close()

if __name__ == "__main__":
    asyncio.run(run())
