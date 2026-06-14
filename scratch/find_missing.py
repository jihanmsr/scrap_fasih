import asyncio
from urllib.parse import unquote
import pandas as pd
from playwright.async_api import async_playwright

async def find_missing():
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9223")
            context = browser.contexts[0]
            page = context.pages[0]

            cookies = await context.cookies()
            xsrf_token = None
            for cookie in cookies:
                if cookie['name'] == 'XSRF-TOKEN':
                    xsrf_token = unquote(cookie['value'])
                    break
            
            # Get regions
            regions_data = await page.evaluate("""
                async (token) => {
                    const codes = ["7201", "7202", "7203", "7204", "7205", "7206", "7207", "7208", "7209", "7210", "7211", "7212", "7271"];
                    const kab_map = {};
                    for (const code of codes) {
                        const url = `https://fasih-sm.bps.go.id/app/api/region/api/v1/region/custom-by-smallest-code-and-level?groupId=6b0b053f-aa43-4855-ac8f-26857b735c93&smallestLevelFullCode=${code}&level=2`;
                        const res = await fetch(url, { headers: { "X-XSRF-TOKEN": token } });
                        const json = await res.json();
                        if (json && json.success && json.data) {
                            const level2 = json.data.level1.level2;
                            if (level2) kab_map[level2.name] = level2.id;
                        }
                    }
                    return kab_map;
                }
            """, xsrf_token)

            # Fetch all assignments
            all_assignments = await page.evaluate("""
                async ({regions, token}) => {
                    const datatable_url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode";
                    const survey_period_id = "37526b20-81c8-42f5-a895-6190137d7394";
                    const results = [];
                    for (const [name, id] of Object.entries(regions)) {
                        let start = 0;
                        while (true) {
                            const payload = {
                                "start": start,
                                "length": 100,
                                "columns": [{"data": "id"}, {"data": "codeIdentity"}, {"data": "data1"}],
                                "order": [],
                                "search": {"value": "", "regex": false},
                                "assignmentExtraParam": {
                                    "region1Id": "a00c8aef-afc4-4d4f-b80d-789a15450ef9",
                                    "region2Id": id,
                                    "surveyPeriodId": survey_period_id,
                                    "assignmentErrorStatusType": -1,
                                    "filterTargetType": ""
                                }
                            };
                            const res = await fetch(datatable_url, {
                                method: "POST",
                                headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                                body: JSON.stringify(payload)
                            });
                            const json = await res.json();
                            const data_part = json.searchData || [];
                            const total_hit = json.totalHit || 0;
                            results.push(...data_part.map(c => ({
                                id: c.id,
                                codeIdentity: c.codeIdentity,
                                name: c.data1,
                                region: name
                            })));
                            start += 100;
                            if (start >= total_hit) break;
                        }
                    }
                    return results;
                }
            """, {"regions": regions_data, "token": xsrf_token})

            bps_ids = set(c['id'] for c in all_assignments)
            
            # Read CSV
            df = pd.read_csv('all_email_history.csv')
            csv_ids = set(df['Kode Identitas'].tolist())
            
            missing_in_csv = bps_ids - csv_ids
            print("Number of BPS IDs missing in CSV:", len(missing_in_csv))
            for m in list(missing_in_csv)[:10]:
                for c in all_assignments:
                    if c['id'] == m:
                        print(f"  Missing: ID={m}, CodeIdentity={c['codeIdentity']}, Name={c['name']}, Region={c['region']}")

        except Exception as e:
            print("Error:", e)

asyncio.run(find_missing())
