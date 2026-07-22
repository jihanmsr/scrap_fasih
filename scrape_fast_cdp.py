import subprocess
import asyncio
import json
import csv
import os
from playwright.async_api import async_playwright

DATATABLE_URL = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/report-progress-by-responsibility"

PAYLOAD_TEMPLATE = {
    "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24",
    "size": 100,
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
    print("[INFO] Membuka Chrome khusus scraping untuk bypass F5...")
    async with async_playwright() as p:
        abs_user_data_dir = os.path.abspath(os.environ.get("CHROME_PROFILE_DIR", "playwright_chrome_profile"))
        chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        
        context = await p.chromium.launch_persistent_context(
            user_data_dir=abs_user_data_dir, 
            headless=False, 
            executable_path=chrome_path,
            ignore_default_args=["--enable-automation"],
            args=["--no-first-run", "--no-default-browser-check", "--disable-blink-features=AutomationControlled"]
        )
            
        page = context.pages[0] if context.pages else await context.new_page()
        
        print("[INFO] Mengakses FASIH...")
        await page.goto("https://fasih-sm.bps.go.id/app/dashboard", timeout=60000, wait_until="domcontentloaded")
        await asyncio.sleep(3)
        
        while True:
            cookies = await context.cookies()
            token = ""
            for c in cookies:
                if c["name"] == "XSRF-TOKEN":
                    from urllib.parse import unquote
                    token = unquote(c["value"])
                    break
            if not token:
                print("\n[WARNING] Anda belum login. Silakan login ke FASIH di Chrome yang terbuka.")
                await asyncio.sleep(5)
                continue
            break

        all_results = []
        
        for role_name, role_id in ROLES.items():
            current_page = 0
            print(f"\n======================================")
            print(f"Menarik Data Role: {role_name}")
            print(f"======================================")
            
            while True:
                print(f" -> Mengambil halaman {current_page}...")
                payload = PAYLOAD_TEMPLATE.copy()
                payload["surveyRoleId"] = role_id
                payload["page"] = current_page
                
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
                            if (!r.ok) return { _error: `HTTP ${r.status}` };
                            return await r.json();
                        } catch (e) {
                            return { _error: e.toString() };
                        }
                    }
                """, {"url": DATATABLE_URL, "payload": payload, "token": token})
                
                if not res or "_error" in res:
                    print(f"[ERROR] Gagal mengambil halaman {current_page}:", res.get("_error", "Unknown error"))
                    print("[WARNING] Sesi kedaluwarsa. Harap refresh halaman FASIH dan tunggu 10 detik.")
                    await asyncio.sleep(10)
                    continue
                    
                content = res.get("data", {}).get("content", [])
                if not content:
                    print(f"[INFO] Role {role_name} selesai di halaman {current_page}.")
                    break
                    
                for c in content:
                    c["assigned_role"] = role_name
                all_results.extend(content)
                current_page += 1
                await asyncio.sleep(1.0)
            
        csv_file = "/Users/jihanmaisaroh/scrap_fasih/fast_petugas_palu.csv"
        with open(csv_file, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Email", "Role", "Region Code", "Total Target", "OPEN", "DRAFT", "SUBMITTED BY Pencacah", "APPROVED BY Pengawas", "REJECTED BY Pengawas"])
            
            for row in all_results:
                email = row.get("email", "")
                role = row.get("assigned_role", "")
                for r_sum in row.get("regionSummary", []):
                    reg_code = r_sum.get("regionCode", "")
                    status_breakdown = r_sum.get("statusBreakdown", [])
                    counts = {"OPEN": 0, "DRAFT": 0, "SUBMITTED BY PENCACAH": 0, "APPROVED BY PENGAWAS": 0, "REJECTED BY PENGAWAS": 0}
                    total = r_sum.get("total", 0)
                    for st in status_breakdown:
                        st_name = st.get("status", "").upper()
                        counts[st_name] = st.get("count", 0)
                    writer.writerow([email, role, reg_code, total, counts.get("OPEN",0), counts.get("DRAFT",0), counts.get("SUBMITTED BY PENCACAH",0), counts.get("APPROVED BY PENGAWAS",0), counts.get("REJECTED BY PENGAWAS",0)])
                    
        print(f"\n[SUCCESS] Berhasil! Data CSV tersimpan di {csv_file}")
        
        petugas_map = {}
        for row in all_results:
            email = row.get("email", "").strip().lower()
            if not email: continue
            
            if email not in petugas_map:
                petugas_map[email] = {
                    "target": 0, "submitted_pencacah": 0, "submitted_respondent": 0,
                    "approved": 0, "rejected": 0, "draft": 0, "open": 0
                }
                
            for r_sum in row.get("regionSummary", []):
                petugas_map[email]["target"] += r_sum.get("total", 0)
                for st in r_sum.get("statusBreakdown", []):
                    s_name = st.get("status", "").upper()
                    s_count = st.get("count", 0)
                    if s_name == "OPEN": petugas_map[email]["open"] += s_count
                    elif s_name == "DRAFT": petugas_map[email]["draft"] += s_count
                    elif s_name == "SUBMITTED BY PENCACAH": petugas_map[email]["submitted_pencacah"] += s_count
                    elif s_name == "SUBMITTED RESPONDENT": petugas_map[email]["submitted_respondent"] += s_count
                    elif "APPROVED" in s_name: petugas_map[email]["approved"] += s_count
                    elif "REJECTED" in s_name: petugas_map[email]["rejected"] += s_count

        js_file = "/Users/jihanmaisaroh/scrap_fasih/fast_petugas_progress.js"
        with open(js_file, "w") as f:
            f.write(f"window.PETUGAS_PROGRESS_MAP = {json.dumps(petugas_map, indent=4)};\n")
        print(f"[SUCCESS] Javascript map disimpan di {js_file}")
        
        
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
