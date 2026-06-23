import asyncio
import json
import os
import time
from playwright.async_api import async_playwright
import traceback
import subprocess
from report_progress_petugas import main as generate_report

# Impor fungsi inti dari core (jangan dipanggil via CLI)
from scrape_granular_core import scrape_all_granular, get_authenticated_context
from merge_granulars import merge_granulars

USER_DATA_DIR = "playwright_chrome_profile"
SE_UMUM_PERIOD = "fd68e454-ba45-4b85-8205-f3bf777ded24"
SE_UB_PERIOD = "37526b20-81c8-42f5-a895-6190137d7394"

REGIONS = [
    "7201", "7202", "7203", "7204", "7205", 
    "7206", "7207", "7208", "7209", "7210", 
    "7211", "7212", "7271"
]

async def fetch_users(page, survey_period_id, role_name):
    print(f"[INFO] Fetching users for {role_name}...")
    users = []
    page_idx = 0
    size = 1000
    while True:
        url = f"https://fasih-sm.bps.go.id/app/api/survey-user/api/v1/allocations-view/by-user?surveyPeriodId={survey_period_id}&page={page_idx}&size={size}"
        try:
            resp = await page.evaluate(f'''() => fetch("{url}").then(r => r.json())''')
        except Exception as e:
            print(f"Error fetching users page {page_idx}: {e}")
            break
            
        content = resp.get("data", {}).get("content", [])
        if not content:
            break
            
        users.extend(content)
        total_pages = resp.get("data", {}).get("totalPages", 1)
        if page_idx >= total_pages - 1:
            break
        page_idx += 1
        
    print(f" ✅ Total {len(users)} petugas berhasil ditarik untuk {role_name}.")
    return users

async def main():
    print("==============================================")
    print("   UNIFIED SCRAPER - FASIH SULAWESI TENGAH")
    print("==============================================")
    
    # 1. Pastikan Chrome berjalan di port 9222
    async with async_playwright() as p:
        try:
            browser, browser_context, page = await get_authenticated_context(p)
            print("[INFO] Chrome berhasil terhubung/diluncurkan.")
        except Exception as e:
            print(f"[ERROR] Gagal meluncurkan/menghubungkan Chrome: {e}")
            return
        
        print("[INFO] Navigating to FASIH...")
        try:
            if "fasih-sm.bps.go.id" not in page.url:
                await page.goto("https://fasih-sm.bps.go.id/app/surveys", timeout=15000)
                await page.wait_for_load_state("networkidle", timeout=5000)
        except Exception as e:
            print(f"[WARNING] Navigation timeout/error: {e}")
            
        # 2. Fetch Users Mapping
        users_umum = await fetch_users(page, SE_UMUM_PERIOD, "SE Umum")
        users_ub = await fetch_users(page, SE_UB_PERIOD, "SE UB")
        
        users_map = {}
        for u in users_umum + users_ub:
            uid = u.get("id")
            if uid:
                users_map[uid] = {
                    "username": u.get("username", "-"),
                    "fullname": u.get("fullname", "-")
                }
                
        with open("users_mapping.json", "w", encoding="utf-8") as f:
            json.dump(users_map, f, indent=2)
        print(f"✅ Mapping {len(users_map)} user ID tersimpan.")
        
        # Cleanup page / context without closing shared browser
        try:
            if browser:
                await page.close()
                await browser.disconnect()
            else:
                await browser_context.close()
        except Exception as ce:
            print(f"[WARNING] Gagal menutup browser/context: {ce}")
    
    # 3. Looping Scrape Semua Kabkot
    # Karena scrape_granular_core.py punya arsitektur connect Chrome sendiri (asyncio.run() di dalamnya), 
    # kita panggil fungsinya secara berurutan.
    for region in REGIONS:
        print(f"\n>>> Memulai Scraping SE UMUM - Kabkot {region}")
        try:
            await scrape_all_granular("se_umum", region)
        except Exception as e:
            print(f"[ERROR] Gagal scrape SE UMUM {region}: {e}")
            
    print(f"\\n>>> Memulai Scraping SE UB")
    try:
        await scrape_all_granular("se_ub", None)
    except Exception as e:
        print(f"[ERROR] Gagal scrape SE UB: {e}")
            
    # 4. Merge Semua Data JSON
    print("\\n>>> Menggabungkan Partisi Data...")
    merge_granulars()
    
    # 5. Generate Laporan Excel
    print("\\n>>> Membuat Laporan Excel & Update Data Dashboard...")
    generate_report()
    
    print("\\n🎉 PROSES SELESAI SECARA MENYELURUH!")

if __name__ == "__main__":
    asyncio.run(main())
