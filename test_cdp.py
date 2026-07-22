import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import json

async def main():
    df = pd.read_excel('hasil_bpom_prov_72_kab01.xlsx')
    
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9223")
            contexts = browser.contexts
            if not contexts:
                print("No active browser contexts found!")
                return
            context = contexts[0]
            pages = context.pages
            if not pages:
                print("No active pages found!")
                return
            page = pages[0]
            print(f"Connected to page: {await page.title()}")
            
            statuses = []
            
            for idx, row in df.iterrows():
                # We search by nama_pengusaha if available, else nama_usaha
                nama = str(row['nama_pengusaha'])
                if pd.isna(row['nama_pengusaha']) or nama == 'nan':
                    nama = str(row['nama_usaha'])
                    
                # Clean up nama to just the name, strip anything in parentheses
                if '(' in nama:
                    nama = nama.split('(')[0].strip()
                    
                code = f"{int(row['kdprov']):02d}{int(row['kdkab']):02d}{int(row['kdkec']):03d}{int(row['kddesa']):03d}{int(row['kdsls']):04d}{int(row['kdsubsls']):02d}"
                assignment_id = str(row['assignment_id'])
                
                payload = {
                    "start": 0,
                    "length": 500,
                    "columns": [
                        {"data":"id","orderable":True},{"data":"codeIdentity","orderable":True},
                        {"data":"data1","orderable":True},{"data":"data2","orderable":True},
                        {"data":"data3","orderable":True},{"data":"data4","orderable":True}
                    ],
                    "order": [],
                    "search": {"value": code, "regex": False},
                    "assignmentExtraParam": {
                        "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e",
                        "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24",
                        "assignmentErrorStatusType": -1,
                        "filterTargetType": "TARGET_ONLY"
                    }
                }
                
                # Use page.evaluate to run fetch in the browser context!
                js_code = f"""
                async () => {{
                    const resp = await fetch('https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({json.dumps(payload)})
                    }});
                    return await resp.json();
                }}
                """
                
                try:
                    data = await page.evaluate(js_code)
                    hits = data.get('searchData', [])
                    
                    match_status = 'NOT_FOUND'
                    for hit in hits:
                        if hit.get('id') == assignment_id:
                            match_status = hit.get('assignmentStatusAlias', 'UNKNOWN_STATUS')
                            break
                    
                    if match_status == 'NOT_FOUND':
                        # Try searching by name as a fallback!
                        payload['search']['value'] = nama
                        js_code2 = f"""
                        async () => {{
                            const resp = await fetch('https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode', {{
                                method: 'POST',
                                headers: {{ 'Content-Type': 'application/json' }},
                                body: JSON.stringify({json.dumps(payload)})
                            }});
                            return await resp.json();
                        }}
                        """
                        data2 = await page.evaluate(js_code2)
                        hits2 = data2.get('searchData', [])
                        for hit in hits2:
                            if hit.get('id') == assignment_id:
                                match_status = hit.get('assignmentStatusAlias', 'UNKNOWN_STATUS')
                                break
                    
                    print(f"[{idx+1}/{len(df)}] ID: {assignment_id} | Code: {code} | Name: {nama} -> {match_status}")
                    statuses.append(match_status)
                except Exception as e:
                    print(f"Error fetching for {assignment_id}: {e}")
                    statuses.append('ERROR')
                
                await asyncio.sleep(0.5)
                
            df['status_cdp'] = statuses
            df.to_excel('hasil_bpom_prov_72_kab01_cdp.xlsx', index=False)
            print(f"Saved! Found: {len([s for s in statuses if s not in ('NOT_FOUND', 'ERROR')])} / {len(statuses)}")
        except Exception as e:
            print(f"Could not connect to CDP: {e}")

if __name__ == "__main__":
    asyncio.run(main())
