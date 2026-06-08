import asyncio
import json
import datetime
import os
from playwright.async_api import async_playwright

async def generate_report():
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        except Exception as e:
            print("Gagal connect ke chrome:", e)
            return

        page = None
        for pg in browser.contexts[0].pages:
            if "fasih-sm.bps.go.id" in pg.url:
                page = pg
                break
        
        if not page:
            print("Tab FASIH tidak ditemukan.")
            return

        cookies = await page.context.cookies()
        xsrf_token = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), "")
        
        # Hardcode kabupatens for Sulawesi Tengah to save API call
        kabs = [
            {"id": "9c9b2d79-9fb1-4ce7-b0f1-6b7bb5511beb", "name": "[01] BANGGAI KEPULAUAN"},
            {"id": "34165dd5-372e-42fa-99c6-0cc19a9b4d0b", "name": "[02] BANGGAI"},
            {"id": "48c4e5d0-5525-41a8-a4ba-2cc38cd9c424", "name": "[03] MOROWALI"},
            {"id": "e18368ae-d1cd-4d43-a74d-5b9ddac5dd22", "name": "[04] POSO"},
            {"id": "c075c4b4-7eb0-4d72-9c16-5103088fb5eb", "name": "[05] DONGGALA"},
            {"id": "d3a28bfa-b611-488b-8255-369da5cedbf7", "name": "[06] TOLI-TOLI"},
            {"id": "dfe4c643-3282-40db-a5fd-cb288a4f592d", "name": "[07] BUOL"},
            {"id": "f18109d2-fc8b-4b9c-886a-dc242d21206e", "name": "[08] PARIGI MOUTONG"},
            {"id": "4d01eba1-5ae9-4603-82a6-2c831aea9905", "name": "[09] TOJO UNA-UNA"},
            {"id": "2a240d3a-67ee-45b2-ae78-4b4b3a909a90", "name": "[10] SIGI"},
            {"id": "288c5680-f6d5-4783-a946-d5a06f547c02", "name": "[11] BANGGAI LAUT"},
            {"id": "a5324f17-7a00-436f-b468-2fc59fcf605d", "name": "[12] MOROWALI UTARA"},
            {"id": "1acfedb4-276e-44d6-9e45-6d43588536d6", "name": "[71] PALU"}
        ]
        
        all_data = []
        for kab in kabs:
            start = 0
            while True:
                payload = {
                    "start": start,
                    "length": 100,
                    "search": {"value": "", "regex": False},
                    "assignmentExtraParam": {
                        "region1Id": "a00c8aef-afc4-4d4f-b80d-789a15450ef9",
                        "region2Id": kab["id"],
                        "surveyPeriodId": "37526b20-81c8-42f5-a895-6190137d7394",
                        "assignmentErrorStatusType": -1,
                        "filterTargetType": ""
                    }
                }
                
                res = await page.evaluate("""
                    async ({payload, token}) => {
                        const url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode";
                        const r = await fetch(url, {
                            method: "POST",
                            headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                            body: JSON.stringify(payload)
                        });
                        return await r.json();
                    }
                """, {"payload": payload, "token": xsrf_token})
                
                if "searchData" not in res or not res["searchData"]:
                    break
                    
                for item in res["searchData"]:
                    item["kab_name"] = kab["name"]
                    all_data.append(item)
                    
                start += 100
                if start >= res.get("totalHit", 0):
                    break
        
        print(f"Berhasil fetch {len(all_data)} records.")
        
        # Calculate progress
        today = datetime.datetime.now(datetime.timezone.utc).date()
        yesterday = today - datetime.timedelta(days=1)
        two_days_ago = today - datetime.timedelta(days=2)
        
        report = {}
        for kab in kabs:
            report[kab["name"]] = {
                "total_prelist": 0,
                "total_akhir": 0,
                "today_completed": 0,
                "yesterday_completed": 0,
                "last_2_days_completed": 0,
                "new_usaha_today": 0,
                "new_usaha_yesterday": 0
            }
            
        for d in all_data:
            kab_name = d["kab_name"]
            report[kab_name]["total_prelist"] += 1
            
            # Check completion
            if d.get("assignmentStatusAlias") == "SUBMITTED RESPONDENT" or d.get("assignmentStatusId") == 5:
                report[kab_name]["total_akhir"] += 1
                
                mod_date_str = d.get("dateModified")
                if mod_date_str:
                    try:
                        # Format: "2026-06-05T02:13:20.911+00:00"
                        mod_date = datetime.datetime.fromisoformat(mod_date_str.replace("Z", "+00:00")).date()
                        if mod_date == today:
                            report[kab_name]["today_completed"] += 1
                            report[kab_name]["last_2_days_completed"] += 1
                        elif mod_date == yesterday:
                            report[kab_name]["yesterday_completed"] += 1
                            report[kab_name]["last_2_days_completed"] += 1
                        elif mod_date == two_days_ago:
                            report[kab_name]["last_2_days_completed"] += 1
                    except Exception as e:
                        pass
                        
            # Check creation
            create_date_str = d.get("dateCreated")
            if create_date_str:
                try:
                    create_date = datetime.datetime.fromisoformat(create_date_str.replace("Z", "+00:00")).date()
                    if create_date == today:
                        report[kab_name]["new_usaha_today"] += 1
                    elif create_date == yesterday:
                        report[kab_name]["new_usaha_yesterday"] += 1
                except:
                    pass
                    
        # Calculate percentages and formatting
        final_report = []
        for kab_name, stats in report.items():
            prelist = stats["total_prelist"]
            completed = stats["total_akhir"]
            pct = round((completed / prelist * 100) if prelist > 0 else 0, 2)
            sisa = prelist - completed
            
            final_report.append({
                "kabupaten": kab_name,
                "total_prelist": prelist,
                "total_akhir": completed,
                "persentase": pct,
                "sisa_usaha": sisa,
                "today_completed": stats["today_completed"],
                "yesterday_completed": stats["yesterday_completed"],
                "last_2_days_completed": stats["last_2_days_completed"],
                "new_usaha_today": stats["new_usaha_today"],
                "new_usaha_yesterday": stats["new_usaha_yesterday"]
            })
            
        with open("ipas_data.json", "w", encoding="utf-8") as f:
            json.dump({"updated_at": datetime.datetime.now().isoformat(), "data": final_report}, f, indent=2)
            
        print("Data IPAS berhasil di-generate!")

if __name__ == "__main__":
    asyncio.run(generate_report())
