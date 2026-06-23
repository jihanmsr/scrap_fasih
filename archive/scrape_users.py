import asyncio
import json
import os
import sys
from playwright.async_api import async_playwright

USER_DATA_DIR = "/Users/jihanmaisaroh/Library/Application Support/Google/Chrome"
SE_UMUM_PERIOD = "fd68e454-ba45-4b85-8205-f3bf777ded24"
SE_UB_PERIOD = "37526b20-81c8-42f5-a895-6190137d7394"

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
        
    print(f" ✅ Total {len(users)} petugas berhasil ditarik.")
    return users

async def main():
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            print("[INFO] Terhubung ke browser aktif.")
            context = browser.contexts[0]
            page = context.pages[0]
        except Exception:
            print("[ERROR] Chrome belum dibuka di port 9222!")
            return
        
        print("[INFO] Navigating to FASIH...")
        try:
            await page.goto("https://fasih-sm.bps.go.id/app/surveys", timeout=15000)
            await page.wait_for_load_state("networkidle", timeout=5000)
        except Exception as e:
            print(f"[WARNING] Navigation timeout/error: {e}")
            
        users_umum = await fetch_users(page, SE_UMUM_PERIOD, "SE Umum")
        users_ub = await fetch_users(page, SE_UB_PERIOD, "SE UB")
        
        # Build mapping ID -> {username, fullname}
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
            
        print(f"✅ Mapping {len(users_map)} user ID disimpan ke users_mapping.json")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
