import asyncio
import os
import json
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        user_data_dir = os.path.abspath("playwright_chrome_profile_w2")
        chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        
        print("Connecting to Chrome profile...")
        try:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=True,
                executable_path=chrome_path,
                ignore_default_args=["--enable-automation"],
                args=["--no-first-run", "--no-default-browser-check", "--disable-blink-features=AutomationControlled"]
            )
        except Exception as e:
            print(f"[ERROR] Gagal meluncurkan Chrome (mungkin lock file masih aktif): {e}")
            print("Harap pastikan reject_bot.py di terminal Anda sudah di-stop (Ctrl+C)!")
            return
            
        page = context.pages[0] if context.pages else await context.new_page()
        
        # Cari token XSRF dari cookie
        print("Navigasi ke surveys untuk memuat session...")
        await page.goto("https://fasih-sm.bps.go.id/app/surveys", wait_until="domcontentloaded")
        await asyncio.sleep(3)
        
        cookies = await context.cookies()
        xsrf_token = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
        
        if not xsrf_token:
            print("[ERROR] Token session XSRF tidak ditemukan. Silakan login terlebih dahulu.")
            await context.close()
            return
            
        # Target IDs to inspect
        target_ids = [
            "3208777a-d127-4787-b9ca-edbdaf5dddc1", # Failed (DAMIANUS SERAN)
            "e1682c11-9c77-4f92-8550-38d0dccad36f", # Succeeded (BALTHASAR BOUK)
            "007a6993-1fbe-47b6-8df8-9ac53e184017", # Failed (PETRONELA LURUK)
        ]
        
        print("\nQuerying status from FASIH API...")
        for tid in target_ids:
            payload = {
                "start": 0,
                "length": 1,
                "columns": [{"data": "id"}],
                "order": [],
                "search": {"value": tid, "regex": False},
                "assignmentExtraParam": {
                    "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24"
                }
            }
            
            res = await page.evaluate("""
                async ({payload, token}) => {
                    try {
                        const r = await fetch("https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode", {
                            method: "POST",
                            headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                            body: JSON.stringify(payload)
                        });
                        return await r.json();
                    } catch (e) {
                        return { error: e.toString() };
                    }
                }
            """, {"payload": payload, "token": xsrf_token})
            
            if "data" in res and res["data"]:
                record = res["data"][0]
                # Print interesting status fields
                print(f"\nTarget ID: {tid}")
                print(f"  Nama: {record.get('namaTarget')}")
                print(f"  Kec: {record.get('namaKec')}")
                print(f"  Desa: {record.get('namaDesa')}")
                print(f"  Status BPS: {record.get('assignmentStatus')}")
                print(f"  Status Desc: {record.get('assignmentStatusDescription')}")
                print(f"  Role Pembuat: {record.get('createdByRoleName')}")
            else:
                print(f"\nTarget ID: {tid} - Tidak ditemukan di API atau Error: {res}")
                
        await context.close()

if __name__ == "__main__":
    asyncio.run(main())
