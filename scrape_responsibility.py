import asyncio
import json
import csv
from playwright.async_api import async_playwright
import os

DATATABLE_URL = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/report-progress-by-responsibility"

PAYLOAD_TEMPLATE = {
    "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24",
    "size": 5,
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
    "Pencacah": "93bcf446-c4c1-4462-8ed0-4b0f7ae89e52",
    "Pengawas": "6d7d919a-45e5-4779-bb87-2905b49fd31a"
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
        await page.goto("https://fasih-sm.bps.go.id/app/dashboard", timeout=60000, wait_until="domcontentloaded")
        await asyncio.sleep(5)
        
        cookies = await context.cookies()
        token = ""
        for c in cookies:
            if c["name"] == "XSRF-TOKEN":
                from urllib.parse import unquote
                token = unquote(c["value"])
                break
                
        if not token:
            print("[WARNING] Anda belum login!")
            print("=========================================================================")
            print("  Silakan login ke web FASIH di jendela Chrome yang baru saja terbuka.")
            print("  Skrip ini akan otomatis menunggu sampai Anda berhasil login...")
            print("=========================================================================")
            
            # Wait until the URL changes to surveys or dashboard after login
            try:
                await page.wait_for_url("**/surveys**", timeout=120000) # wait up to 2 minutes
                await asyncio.sleep(5)
                # re-fetch cookies after login
                cookies = await context.cookies()
                for c in cookies:
                    if c["name"] == "XSRF-TOKEN":
                        from urllib.parse import unquote
                        token = unquote(c["value"])
                        break
            except Exception as e:
                print("[ERROR] Waktu login habis (2 menit) atau halaman ditutup. Silakan ulangi.")
                await context.close()
                return

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
                                        return { _error: `HTTP ${r.status}: ${text}`, status: r.status };
                                    }
                                    return await r.json();
                                } catch (e) {
                                    return { _error: e.toString(), status: 0 };
                                }
                            }
                        """, {"url": DATATABLE_URL, "payload": payload, "token": token})
                    except Exception as e:
                        print(f"[ERROR] Exception dari Python Playwright: {e}")
                        res = {"_error": str(e), "status": 0}
                    
                    if not res or "_error" in res:
                        err_msg = res.get("_error", "Unknown error")
                        status = res.get("status", 0)
                        print(f"[ERROR] Gagal mengambil halaman {current_page}: HTTP {status} - {err_msg[:100]}")
                        
                        # Status 0 berarti masalah koneksi lokal/Chrome, 502/503/504 BPS Down. Semuanya kita RETRY.
                        if status in [0, 502, 503, 504]:
                            print("[INFO] Error koneksi / Server BPS sibuk. Menunggu 5 detik lalu mengulang halaman ini secara otomatis...")
                            await asyncio.sleep(5)
                            continue # Ulangi halaman yang sama
                        else:
                            print("[ERROR] Error ditolak (seperti 400 atau 401). Menghentikan.")
                            break
                        
                    content = res.get("data", {}).get("content", [])
                    if not content:
                        print(f"    [INFO] Selesai di halaman {current_page}.")
                        break
                        
                    for c in content:
                        c["assigned_role"] = role_name
                    all_results.extend(content)
                    current_page += 1
                    await asyncio.sleep(1.0)
            
        csv_file = "/Users/jihanmaisaroh/scrap_fasih/fast_petugas_all.csv"
        with open(csv_file, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Email", "Role", "Region Code", "Total Target", "OPEN", "DRAFT", "SUBMITTED BY Pencacah", "SUBMITTED RESPONDENT", "APPROVED BY Pengawas", "REJECTED BY Pengawas", "REVOKED BY Pengawas", "EDITED BY Pengawas", "EDITED BY Admin Kabupaten", "REJECTED BY Admin Kabupaten", "COMPLETED BY Admin Kabupaten"])
            
            for row in all_results:
                email = row.get("email", "")
                role = row.get("assigned_role", "")
                for r_sum in row.get("regionSummary", []):
                    reg_code = r_sum.get("regionCode", "")
                    status_breakdown = r_sum.get("statusBreakdown", [])
                    
                    counts = {
                        "OPEN": 0, "DRAFT": 0, "SUBMITTED BY PENCACAH": 0, "SUBMITTED RESPONDENT": 0,
                        "APPROVED BY PENGAWAS": 0, "REJECTED BY PENGAWAS": 0, "REVOKED BY PENGAWAS": 0,
                        "EDITED BY PENGAWAS": 0, "EDITED BY ADMIN KABUPATEN": 0,
                        "REJECTED BY ADMIN KABUPATEN": 0, "COMPLETED BY ADMIN KABUPATEN": 0
                    }
                    total = r_sum.get("total", 0)
                    for st in status_breakdown:
                        st_name = st.get("status", "").upper()
                        if st_name in counts:
                            counts[st_name] = st.get("count", 0)
                        else:
                            counts[st_name] = st.get("count", 0) # just in case there are others
                            
                    writer.writerow([
                        email, role, reg_code, total,
                        counts.get("OPEN",0), counts.get("DRAFT",0),
                        counts.get("SUBMITTED BY PENCACAH",0), counts.get("SUBMITTED RESPONDENT",0),
                        counts.get("APPROVED BY PENGAWAS",0), counts.get("REJECTED BY PENGAWAS",0),
                        counts.get("REVOKED BY PENGAWAS",0), counts.get("EDITED BY PENGAWAS",0),
                        counts.get("EDITED BY ADMIN KABUPATEN",0), counts.get("REJECTED BY ADMIN KABUPATEN",0),
                        counts.get("COMPLETED BY ADMIN KABUPATEN",0)
                    ])
                    
        print(f"\n[SUCCESS] Berhasil! Data CSV tersimpan di {csv_file}")
        
        petugas_map = {
            "Pencacah": {},
            "Pengawas": {}
        }
        for row in all_results:
            email = row.get("email", "").strip().lower()
            role = row.get("assigned_role", "")
            if not email or not role: continue
            
            if email not in petugas_map[role]:
                petugas_map[role][email] = {
                    "target": 0, "submitted_pencacah": 0, "submitted_respondent": 0,
                    "approved": 0, "rejected": 0, "draft": 0, "open": 0
                }
                
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
                    elif "REJECTED" in s_name: petugas_map[role][email]["rejected"] += s_count

        js_file = "/Users/jihanmaisaroh/scrap_fasih/fast_petugas_progress.js"
        with open(js_file, "w") as f:
            f.write(f"window.PETUGAS_PROGRESS_MAP = {json.dumps(petugas_map, indent=4)};\n")
        print(f"[SUCCESS] Javascript map disimpan di {js_file}")
        
        await context.close()

if __name__ == "__main__":
    asyncio.run(run())
