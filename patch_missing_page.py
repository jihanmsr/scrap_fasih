import subprocess
import asyncio
import json
import csv
from playwright.async_api import async_playwright
import os
import datetime
import re

DATATABLE_URL = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/report-progress-by-responsibility"

ROLES = {
    "Pencacah": "6d7d919a-45e5-4779-bb87-2905b49fd31a",
    "Pengawas": "93bcf446-c4c1-4462-8ed0-4b0f7ae89e52"
}

def parse_log_for_missing_pages(log_file_path):
    missing_targets = []
    if not os.path.exists(log_file_path):
        return missing_targets

    with open(log_file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    current_role = None
    current_kab = None
    
    for line in lines:
        # Cari baris yang menunjukkan sedang memproses Role & Kab apa
        # Contoh: Menarik Data Role: Pencacah - Banggai
        match_role = re.search(r'Menarik Data Role:\s+(Pencacah|Pengawas)\s+-\s+(.+)', line)
        if match_role:
            current_role = match_role.group(1).strip()
            current_kab = match_role.group(2).strip()
            
        # Cari baris yang menunjukkan gagal di halaman tertentu
        # Contoh: [WARNING] Gagal total setelah 35 percobaan di halaman 5.
        match_fail = re.search(r'Gagal total setelah \d+ percobaan di halaman (\d+)', line)
        if match_fail and current_role and current_kab:
            page = int(match_fail.group(1))
            missing_targets.append({
                "role": current_role,
                "kab_name": current_kab,
                "page": page
            })
            
    return missing_targets

def rebuild_js_from_csv(csv_file):
    petugas_map = { "Pencacah": {}, "Pengawas": {} }
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            email = row.get("Email", "").strip().lower()
            role = row.get("Role", "")
            if not email or not role or role not in petugas_map: continue
            
            reg_code = row.get("Region Code", "")
            total = int(row.get("Total Target", 0))
            
            if email not in petugas_map[role]:
                petugas_map[role][email] = { "target": 0, "submitted_pencacah": 0, "submitted_respondent": 0, "approved": 0, "rejected": 0, "draft": 0, "open": 0, "revoked": 0, "edited_pengawas": 0, "edited_admin": 0, "completed_admin": 0, "sls_details": {} }
            
            petugas_map[role][email]["target"] += total
            
            if "sls_details" not in petugas_map[role][email]:
                petugas_map[role][email]["sls_details"] = {}
            if reg_code not in petugas_map[role][email]["sls_details"]:
                petugas_map[role][email]["sls_details"][reg_code] = {"total": 0, "status": {}}
                
            petugas_map[role][email]["sls_details"][reg_code]["total"] += total
            
            statuses = ["OPEN", "DRAFT", "SUBMITTED BY Pencacah", "SUBMITTED RESPONDENT", "APPROVED BY Pengawas", "REJECTED BY Pengawas", "REVOKED BY Pengawas", "EDITED BY Pengawas", "EDITED BY Admin Kabupaten", "REJECTED BY Admin Kabupaten", "COMPLETED BY Admin Kabupaten"]
            
            for s in statuses:
                val = int(row.get(s, 0))
                s_name = s.upper()
                if val > 0:
                    petugas_map[role][email]["sls_details"][reg_code]["status"][s_name] = petugas_map[role][email]["sls_details"][reg_code]["status"].get(s_name, 0) + val
                    if s_name == "OPEN": petugas_map[role][email]["open"] += val
                    elif s_name == "DRAFT": petugas_map[role][email]["draft"] += val
                    elif "SUBMITTED BY PENCACAH" in s_name: petugas_map[role][email]["submitted_pencacah"] += val
                    elif "SUBMITTED RESPONDENT" in s_name: petugas_map[role][email]["submitted_respondent"] += val
                    elif "APPROVED" in s_name: petugas_map[role][email]["approved"] += val
                    elif "REJECTED BY ADMIN" in s_name: petugas_map[role][email]["rejected"] += val
                    elif "REJECTED" in s_name: petugas_map[role][email]["rejected"] += val
                    elif "REVOKED" in s_name: petugas_map[role][email]["revoked"] += val
                    elif "EDITED BY PENGAWAS" in s_name: petugas_map[role][email]["edited_pengawas"] += val
                    elif "EDITED BY ADMIN" in s_name: petugas_map[role][email]["edited_admin"] += val
                    elif "COMPLETED BY ADMIN" in s_name: petugas_map[role][email]["completed_admin"] += val
                    
    history_file = "/Users/jihanmaisaroh/scrap_fasih/fast_petugas_history.js"
    history_map = {}
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r') as f:
                content = f.read()
                start = content.find('{')
                end = content.rfind('}') + 1
                if start != -1 and end != 0: history_map = json.loads(content[start:end])
        except Exception:
            pass

    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    history_map[today_str] = petugas_map

    with open(history_file, "w", encoding='utf-8') as f: f.write(f"window.PETUGAS_HISTORY_MAP = {json.dumps(history_map, indent=4)};\n")
    with open("/Users/jihanmaisaroh/scrap_fasih/fast_petugas_progress.js", "w") as f: f.write(f"window.PETUGAS_PROGRESS_MAP = {json.dumps(petugas_map, indent=4)};\n")
    print(f"[INFO] File .js berhasil diupdate dengan data terbaru!")

async def run():
    print("[INFO] Memulai auto-patching untuk halaman yang bolong...")
    
    log_file = "/Users/jihanmaisaroh/scrap_fasih/terminal_log.txt"
    missing_targets = parse_log_for_missing_pages(log_file)
    
    if not missing_targets:
        print(f"[WARNING] Tidak ada data halaman yang bolong ditemukan!")
        print(f"Pastikan Anda sudah meng-copy teks dari terminal dan mem-paste ke dalam file: {log_file}")
        return
        
    print(f"[INFO] Ditemukan {len(missing_targets)} halaman bolong dari file log:")
    for mt in missing_targets:
        print(f"       - Role: {mt['role']}, Kab: {mt['kab_name']}, Halaman: {mt['page']}")
        
    with open("/Users/jihanmaisaroh/scrap_fasih/region_map_sulteng_full.json", "r") as f:
        region_map = json.load(f)
        
    kabupaten_list = region_map.get("kabupaten", {})
    
    targets = []
    for t in missing_targets:
        role_name = t["role"]
        kab_name_target = t["kab_name"].upper()
        page_target = t["page"]
        
        kab_id = None
        for kab_code, kab_info in kabupaten_list.items():
            if kab_info["kab_name"].upper() == kab_name_target:
                kab_id = kab_info["kab_id"]
                break
        
        if not kab_id:
            print(f"[ERROR] Kabupaten '{kab_name_target}' tidak ditemukan di region_map! Lewati...")
            continue
            
        role_id = ROLES.get(role_name)
        if not role_id:
            continue
            
        targets.append({
            "role_name": role_name,
            "role_id": role_id,
            "kab_name": kab_name_target,
            "kab_id": kab_id,
            "page": page_target
        })
        
    if not targets:
        return

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
        
        try:
            await page.wait_for_url(re.compile(r".*surveys.*"), timeout=5000)
            print("[INFO] Sudah login!")
        except:
            print("[WARNING] Anda belum login! Silakan login...")
            try:
                await page.wait_for_url(re.compile(r".*surveys.*"), timeout=300000)
                await page.goto("https://fasih-sm.bps.go.id/app/surveys/a0429e96-51a5-477b-a415-485f9c153004/fd68e454-ba45-4b85-8205-f3bf777ded24", timeout=120000)
                await page.wait_for_load_state("networkidle")
            except Exception as e:
                print(f"[ERROR] Gagal login: {e}")
                await context.close()
                return

        await page.goto("https://fasih-sm.bps.go.id/app/analytic/assignment/assignment-status", timeout=120000)
        await page.wait_for_load_state("networkidle")
        
        all_results = []
        
        for target in targets:
            role_name = target["role_name"]
            role_id = target["role_id"]
            kab_name = target["kab_name"]
            kab_id = target["kab_id"]
            current_page = target["page"]
            
            print(f"\n======================================")
            print(f"Menarik PATCH: {role_name} - {kab_name} (Halaman {current_page})")
            print(f"======================================")
            
            retries = 0
            max_retries = 35
            
            while True:
                print(f"    -> Mengambil halaman {current_page}...")
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
                    import httpx
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
                        for k, v in cookie_dict.items():
                            client.cookies.set(k, v, domain="fasih-sm.bps.go.id")
                        
                        payload_str = json.dumps(payload, separators=(',', ':'))
                        r = await client.post(DATATABLE_URL, content=payload_str, headers=headers)
                    
                        if r.status_code == 200:
                            res = {"api_response": r.json(), "status": 200}
                        else:
                            res = {"_error": f"HTTP {r.status_code} - {r.text}", "status": r.status_code}
                        
                except Exception as e:
                    res = {"_error": repr(e), "status": 0}
                
                if res and "_error" in res:
                    retries += 1
                    print(f"[ERROR] Gagal mengambil halaman {current_page} (Percobaan {retries}/{max_retries}): {res.get('_error')}")
                
                    if "504" not in res.get('_error', '') and "502" not in res.get('_error', ''):
                        try:
                            await page.goto("https://fasih-sm.bps.go.id/app/surveys/a0429e96-51a5-477b-a415-485f9c153004/fd68e454-ba45-4b85-8205-f3bf777ded24", timeout=120000)
                            await page.wait_for_load_state("networkidle")
                        except:
                            pass
                    
                    if retries >= max_retries:
                        print(f"[WARNING] Gagal total setelah {max_retries} percobaan di halaman {current_page}. PATCH GAGAL!")
                        break
                    
                    wait_time = 5 if retries < 5 else 15
                    await asyncio.sleep(wait_time)
                    continue
                
                content = res.get("api_response", {}).get("data", {}).get("content", [])
                if not content:
                    print(f"    [INFO] Halaman {current_page} kosong.")
                    break
                
                print(f"    [INFO] Sukses menarik {len(content)} data pada halaman {current_page}.")
                for c in content:
                    c["assigned_role"] = role_name
                all_results.extend(content)
                break
                
        if not all_results:
            print("\n[WARNING] Tidak ada data yang berhasil ditambal.")
            await context.close()
            return
            
        print(f"\n[INFO] Menambahkan {len(all_results)} data ke file CSV yang sudah ada...")
        today_str = datetime.datetime.now().strftime("%Y-%m-%d")
        csv_file = f"/Users/jihanmaisaroh/scrap_fasih/fast_petugas_all_{today_str}.csv"
        
        with open(csv_file, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
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
                
        print(f"✅ Penambalan selesai. Data bolong berhasil disisipkan ke {csv_file}")
        
        print("\n🚀 Memperbarui file .js agar langsung tampil di dashboard...")
        rebuild_js_from_csv(csv_file)
        
        print("\n🚀 Mengunggah perubahan ke GitHub...")
        try:
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", "Patch missing data via log parser"], check=True)
            subprocess.run(["git", "push", "origin", "main"], check=True)
            print("✅ Berhasil push ke GitHub!")
        except Exception as e:
            print(f"⚠️ Gagal push ke GitHub: {e}")

        await context.close()

if __name__ == "__main__":
    asyncio.run(run())
