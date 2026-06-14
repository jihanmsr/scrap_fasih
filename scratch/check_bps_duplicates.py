import os
import json
import time
import requests
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

def check_bps_duplicates():
    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp("http://localhost:9223")
            context = browser.contexts[0]
            page = context.pages[0]
            print("Connected to page:", page.url)
            
            cookies = context.cookies()
            xsrf_token = None
            for cookie in cookies:
                if cookie['name'] == 'XSRF-TOKEN':
                    xsrf_token = unquote(cookie['value'])
                    break
            
            if not xsrf_token:
                print("Error: XSRF-TOKEN not found.")
                return
            
            session = requests.Session()
            for c in cookies:
                session.cookies.set(
                    c['name'],
                    c['value'],
                    domain=c.get('domain', 'fasih-sm.bps.go.id'),
                    path=c.get('path', '/')
                )
            headers = {
                "Content-Type": "application/json",
                "X-XSRF-TOKEN": xsrf_token,
                "User-Agent": "Mozilla/5.0"
            }
            session.headers.update(headers)
            
            # Get regions
            print("Fetching regions...")
            kab_map = {}
            kab_codes = ["7201", "7202", "7203", "7204", "7205", "7206", "7207", "7208", "7209", "7210", "7211", "7212", "7271"]
            for code in kab_codes:
                url = f"https://fasih-sm.bps.go.id/app/api/region/api/v1/region/custom-by-smallest-code-and-level?groupId=6b0b053f-aa43-4855-ac8f-26857b735c93&smallestLevelFullCode={code}&level=2"
                try:
                    res = session.get(url, timeout=30)
                    if res.status_code == 200:
                        json_data = res.json()
                        if json_data and json_data.get("success") and json_data.get("data"):
                            level2 = json_data["data"].get("level1", {}).get("level2")
                            if level2:
                                kab_map[level2["name"]] = level2["id"]
                except Exception as e:
                    print(f"Error fetching region UUID {code}: {e}")
            
            print("Resolved regions:", list(kab_map.keys()))
            
            datatable_url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode"
            survey_period_id = "37526b20-81c8-42f5-a895-6190137d7394"
            
            all_companies = []
            for name, kid in kab_map.items():
                print(f"Fetching for {name}...")
                start = 0
                while True:
                    payload = {
                        "start": start,
                        "length": 100,
                        "columns": [{"data": "id"}],
                        "order": [],
                        "search": {"value": "", "regex": False},
                        "assignmentExtraParam": {
                            "region1Id": "a00c8aef-afc4-4d4f-b80d-789a15450ef9",
                            "region2Id": kid,
                            "surveyPeriodId": survey_period_id,
                            "assignmentErrorStatusType": -1,
                            "filterTargetType": ""
                        }
                    }
                    res = session.post(datatable_url, json=payload, timeout=30)
                    if res.status_code != 200:
                        print(f"Failed to fetch for {name}, status: {res.status_code}")
                        break
                    res_json = res.json()
                    data_part = res_json.get("searchData", [])
                    total_hit = res_json.get("totalHit", 0)
                    all_companies.extend(data_part)
                    start += 100
                    if start >= total_hit:
                        break
            
            print("Total companies returned by API:", len(all_companies))
            
            ids = []
            code_identities = []
            names = []
            for c in all_companies:
                ids.append(c.get("id"))
                code_identities.append(c.get("codeIdentity"))
                names.append(c.get("data1"))
            
            # Duplication analysis
            unique_ids = set(ids)
            unique_codes = set(code_identities)
            unique_names = set(names)
            
            print(f"Unique IDs: {len(unique_ids)}")
            print(f"Unique Code Identities: {len(unique_codes)}")
            print(f"Unique Names: {len(unique_names)}")
            
            # Check duplicate IDs
            id_counts = {}
            for i, c in zip(ids, all_companies):
                id_counts[i] = id_counts.get(i, 0) + 1
            
            duplicates = {k: v for k, v in id_counts.items() if v > 1}
            print("Duplicate IDs count:", len(duplicates))
            for k, v in list(duplicates.items())[:10]:
                matching = [c for c in all_companies if c.get("id") == k]
                print(f"ID {k} occurs {v} times:")
                for m in matching:
                    print(f"  Name: {m.get('data1')}, CodeIdentity: {m.get('codeIdentity')}, Region: {m.get('region1Name')} - {m.get('region2Name')}")
                    
        except Exception as e:
            print("Error:", e)

if __name__ == "__main__":
    check_bps_duplicates()
