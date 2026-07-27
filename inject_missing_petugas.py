import asyncio
from playwright.async_api import async_playwright
import json
import csv
import datetime
import urllib.parse

async def main():
    print("[INFO] Memulai injeksi petugas yang hilang (Target=0)...")
    async with async_playwright() as p:
        # Gunakan profile yang berbeda agar tidak bentrok
        browser = await p.chromium.launch_persistent_context(
            user_data_dir="/Users/jihanmaisaroh/scrap_fasih/playwright_chrome_profile_w1",
            executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            headless=True
        )
        page = browser.pages[0]
        
        await page.goto("https://fasih-sm.bps.go.id/app/dashboard")
        await asyncio.sleep(2)
        
        cookies = await browser.cookies()
        token = ""
        for c in cookies:
            if c["name"] == "XSRF-TOKEN":
                token = urllib.parse.unquote(c["value"])
                break
        
        if not token:
            print("[ERROR] Token gagal didapat, pastikan sudah login di profile ini.")
            await browser.close()
            return
            
        print("[INFO] Mengambil Master Petugas dari Allocations API...")
        master_users = []
        page_idx = 0
        while True:
            url = f"https://fasih-sm.bps.go.id/app/api/survey-user/api/v1/allocations-view/by-user?surveyPeriodId=fd68e454-ba45-4b85-8205-f3bf777ded24&page={page_idx}&size=1000"
            res = await page.evaluate(f"""
                async (token) => {{
                    const r = await fetch("{url}", {{
                        headers: {{ "X-XSRF-TOKEN": token }}
                    }});
                    return await r.json();
                }}
            """, token)
            
            content = res.get("data", {}).get("content", [])
            if not content:
                break
            master_users.extend(content)
            
            total_pages = res.get("data", {}).get("totalPages", 1)
            if page_idx >= total_pages - 1:
                break
            page_idx += 1
            print(f"   -> Page {page_idx}/{total_pages} ditarik.")
            
        await browser.close()

    print(f"[INFO] Terkumpul {len(master_users)} petugas master.")
    
    # Load existing CSV
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    csv_file = f"/Users/jihanmaisaroh/scrap_fasih/fast_petugas_all_{today_str}.csv"
    existing_emails = set()
    try:
        with open(csv_file, "r") as f:
            reader = csv.DictReader(f)
            for r in reader:
                existing_emails.add(r["Email"].strip().lower())
    except Exception as e:
        print(f"[ERROR] CSV hari ini belum ada atau error: {e}")
        return

    # Injeksi ke CSV
    missing_count = 0
    with open(csv_file, "a", newline='') as f:
        writer = csv.writer(f)
        for u in master_users:
            email = u.get("username", "").strip().lower()
            if not email or email in existing_emails:
                continue
            
            # Cek apakah dia dari Sulteng (72...)
            regions = u.get("regions", [])
            reg_code = ""
            for reg in regions:
                code = reg.get("code") or reg.get("id")
                if code and str(code).startswith("72"):
                    reg_code = code
                    break
            
            if not reg_code:
                continue
                
            # Tambahkan ke CSV (Anggap target=0)
            writer.writerow([
                email, "Pencacah", reg_code, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
            ])
            existing_emails.add(email)
            missing_count += 1
            
    print(f"[SUCCESS] {missing_count} petugas yang nganggur (target=0) berhasil disuntikkan ke {csv_file}!")

if __name__ == "__main__":
    asyncio.run(main())
