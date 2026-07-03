import asyncio
import os
import json
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        abs_user_data_dir = os.path.abspath("playwright_chrome_profile")
        
        # Unlock profile
        lock_file = os.path.join(abs_user_data_dir, "SingletonLock")
        if os.path.exists(lock_file) or os.path.islink(lock_file):
            try: os.unlink(lock_file)
            except: pass
        socket_file = os.path.join(abs_user_data_dir, "SingletonSocket")
        if os.path.exists(socket_file) or os.path.islink(socket_file):
            try: os.unlink(socket_file)
            except: pass
            
        chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        extra_args = ["--no-first-run", "--no-default-browser-check", "--disable-blink-features=AutomationControlled"]
        
        context = await p.chromium.launch_persistent_context(
            user_data_dir=abs_user_data_dir, headless=True, executable_path=chrome_path,
            ignore_default_args=["--enable-automation"],
            args=extra_args
        )
        page = context.pages[0] if context.pages else await context.new_page()
        
        print("Membuka dashboard BPS...")
        await page.goto("https://fasih-sm.bps.go.id/app/dashboard", timeout=45000)
        await asyncio.sleep(2)
        
        # Load survey config
        survey_cfg = {
            "period_id": "fd68e454-ba45-4b85-8205-f3bf777ded24",
            "prov_id": "5214ecb2-bef1-4a86-9446-451cf430928e",
            "kabs": [
                {"name": "[01] BANGGAI KEPULAUAN", "id": "bc32354f-1245-426f-b2cf-a5733e1295ad"},
                {"name": "[02] BANGGAI", "id": "530e9ca5-86ba-434e-9b04-405102e6d900"},
                {"name": "[03] MOROWALI", "id": "9783f0c1-f047-477f-8840-11eae7cf70e2"},
                {"name": "[04] POSO", "id": "fb9cd9f0-c4c0-4a37-9041-57190693f625"},
                {"name": "[05] DONGGALA", "id": "289f1ff3-a6ad-4c9b-a49f-7b454d03a33f"},
                {"name": "[06] TOLI-TOLI", "id": "d833fdce-ebfb-429b-a1bb-8966239fd8e4"},
                {"name": "[07] BUOL", "id": "c523694a-2e72-4570-9489-da2d7b119fe7"},
                {"name": "[08] PARIGI MOUTONG", "id": "25c59fd9-afd5-4c1a-9dfb-42bb697a7434"},
                {"name": "[09] TOJO UNA-UNA", "id": "736c4c22-51d1-44be-8b2c-aa197d9459a4"},
                {"name": "[10] SIGI", "id": "0061da62-2a47-4dee-b8d0-239b33e2c59d"},
                {"name": "[11] BANGGAI LAUT", "id": "eed1a3e7-b81d-4fc7-b0d6-61257c1449b2"},
                {"name": "[12] MOROWALI UTARA", "id": "d05ef8fd-b5e4-414f-9a83-8cdea03e0767"},
                {"name": "[71] PALU", "id": "4ab6ca2f-7952-4e8e-a94d-b6dd933e5d44"}
            ]
        }
        
        js_fetch_script = """
            async (payload) => {
                const res = await fetch("/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
                if (res.ok) {
                    return await res.json();
                }
                return null;
            }
        """
        
        total_live = 0
        total_nontarget_live = 0
        
        for kab in survey_cfg["kabs"]:
            payload = {
                "start": 0, "length": 1, "columns": [{"data": "id"}], "order": [], "search": {"value": "", "regex": False},
                "assignmentExtraParam": {
                    "region1Id": survey_cfg["prov_id"],
                    "region2Id": kab["id"],
                    "surveyPeriodId": survey_cfg["period_id"],
                    "assignmentErrorStatusType": -1,
                    "filterTargetType": "target"
                }
            }
            payload_nontarget = {
                "start": 0, "length": 1, "columns": [{"data": "id"}], "order": [], "search": {"value": "", "regex": False},
                "assignmentExtraParam": {
                    "region1Id": survey_cfg["prov_id"],
                    "region2Id": kab["id"],
                    "surveyPeriodId": survey_cfg["period_id"],
                    "assignmentErrorStatusType": -1,
                    "filterTargetType": "non-target"
                }
            }
            
            res = await page.evaluate(js_fetch_script, payload)
            res_nt = await page.evaluate(js_fetch_script, payload_nontarget)
            
            target_hits = res.get("totalHit", 0) if res else 0
            nontarget_hits = res_nt.get("totalHit", 0) if res_nt else 0
            total_live += target_hits
            total_nontarget_live += nontarget_hits
            
            print(f"  {kab['name']}: target={target_hits}, non-target={nontarget_hits}")
            
        print(f"\nLive Target Sum: {total_live}")
        print(f"Live Non-Target Sum: {total_nontarget_live}")
        print(f"Combined Total: {total_live + total_nontarget_live}")
        
        await context.close()

if __name__ == "__main__":
    asyncio.run(main())
