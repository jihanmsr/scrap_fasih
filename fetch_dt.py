import asyncio
import json
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = None
        for port in [9223, 9222]:
            try: browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}"); break
            except: pass
        if not browser: return
        context = browser.contexts[0]
        page = None
        for p_page in context.pages:
            if "fasih-sm.bps.go.id" in p_page.url: page = p_page; break
        if not page: return
        
        cookies = await context.cookies()
        token = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
        from urllib.parse import unquote
        if token: token = unquote(token)
        
        survey_period_id = "fd68e454-ba45-4b85-8205-f3bf777ded24"
        region1_id = "5214ecb2-bef1-4a86-9446-451cf430928e"
        url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode"
        
        # Get totalHit first
        payload = {
            "start": 0, "length": 1, "columns": [{"data": "id"}], "order": [], "search": {"value": "", "regex": False},
            "assignmentExtraParam": {"region1Id": region1_id, "surveyPeriodId": survey_period_id, "assignmentErrorStatusType": -1, "filterTargetType": ""}
        }
        res = await page.evaluate(f"fetch('{url}', {{ method: 'POST', headers: {{ 'Content-Type': 'application/json', 'X-XSRF-TOKEN': '{token}' }}, body: JSON.stringify({json.dumps(payload)}) }}).then(r => r.json())")
        total_hit = res.get("totalHit", 0)
        print("Total assignments:", total_hit)
        
        length = 10000
        starts = list(range(0, total_hit, length))
        
        sls_roles = {}
        sls_names = {}
        
        sem = asyncio.Semaphore(15)
        
        async def fetch_chunk(start):
            pld = {
                "start": start, "length": length, "columns": [{"data": "id"}], "order": [], "search": {"value": "", "regex": False},
                "assignmentExtraParam": {"region1Id": region1_id, "surveyPeriodId": survey_period_id, "assignmentErrorStatusType": -1, "filterTargetType": ""}
            }
            for attempt in range(3):
                try:
                    async with sem:
                        r = await page.evaluate(f"""
                            fetch('{url}', {{ method: 'POST', headers: {{ 'Content-Type': 'application/json', 'X-XSRF-TOKEN': '{token}' }}, body: JSON.stringify({json.dumps(pld)}) }}).then(r => r.json())
                        """)
                        return r.get("searchData", [])
                except Exception as e:
                    await asyncio.sleep(1)
            return []
            
        tasks = [fetch_chunk(s) for s in starts]
        completed = 0
        for future in asyncio.as_completed(tasks):
            chunk_data = await future
            completed += 1
            print(f"Progress: {completed}/{len(tasks)} chunks")
            for row in chunk_data:
                reg = row.get("region", {})
                l5 = reg.get("level1", {}).get("level2", {}).get("level3", {}).get("level4", {}).get("level5", {})
                sls_code = l5.get("fullCode")
                if not sls_code: continue
                sls_names[sls_code] = l5.get("name", "")
                
                if sls_code not in sls_roles:
                    sls_roles[sls_code] = set()
                
                # Check assignmentResponsibility
                resps = row.get("assignmentResponsibility", [])
                for resp in resps:
                    role_name = resp.get("currentSurveyRoleName", "").lower()
                    if "pencacah" in role_name: sls_roles[sls_code].add("pencacah")
                    elif "pengawas" in role_name: sls_roles[sls_code].add("pengawas")
                    
        pencacah_only = []
        pengawas_only = []
        
        for code, roles in sls_roles.items():
            if "pencacah" in roles and "pengawas" not in roles:
                pencacah_only.append((code, sls_names[code]))
            elif "pengawas" in roles and "pencacah" not in roles:
                pengawas_only.append((code, sls_names[code]))
                
        with open("selisih_31_wilayah.txt", "w") as f:
            f.write(f"=== {len(pencacah_only)} WILAYAH DI PENCACAH TAPI TIDAK ADA DI PENGAWAS ===\n")
            for c, n in sorted(pencacah_only): f.write(f"{c} - {n}\n")
            f.write(f"\n=== {len(pengawas_only)} WILAYAH DI PENGAWAS TAPI TIDAK ADA DI PENCACAH ===\n")
            for c, n in sorted(pengawas_only): f.write(f"{c} - {n}\n")
            
        print("DONE! Wrote to selisih_31_wilayah.txt")

asyncio.run(run())
