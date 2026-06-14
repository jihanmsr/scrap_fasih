import asyncio
from urllib.parse import unquote
from playwright.async_api import async_playwright

async def check_via_browser():
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9223")
            context = browser.contexts[0]
            page = context.pages[0]
            print("Connected to page:", page.url)

            cookies = await context.cookies()
            xsrf_token = None
            for cookie in cookies:
                if cookie['name'] == 'XSRF-TOKEN':
                    xsrf_token = unquote(cookie['value'])
                    break
            
            if not xsrf_token:
                print("Error: XSRF-TOKEN cookie not found")
                return

            print("XSRF-TOKEN found:", xsrf_token[:15])

            # Let's get the regions
            regions_data = await page.evaluate("""
                async (token) => {
                    const codes = ["7201", "7202", "7203", "7204", "7205", "7206", "7207", "7208", "7209", "7210", "7211", "7212", "7271"];
                    const kab_map = {};
                    for (const code of codes) {
                        const url = `https://fasih-sm.bps.go.id/app/api/region/api/v1/region/custom-by-smallest-code-and-level?groupId=6b0b053f-aa43-4855-ac8f-26857b735c93&smallestLevelFullCode=${code}&level=2`;
                        const res = await fetch(url, {
                            headers: {
                                "X-XSRF-TOKEN": token
                            }
                        });
                        const json = await res.json();
                        if (json && json.success && json.data) {
                            const level2 = json.data.level1.level2;
                            if (level2) {
                                kab_map[level2.name] = level2.id;
                            }
                        }
                    }
                    return kab_map;
                }
            """, xsrf_token)
            print("Resolved regions:", list(regions_data.keys()))

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
                                headers: {
                                    "Content-Type": "application/json",
                                    "X-XSRF-TOKEN": token
                                },
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
                            if (start >= total_hit) {
                                break;
                            }
                        }
                    }
                    return results;
                }
            """, {"regions": regions_data, "token": xsrf_token})

            print("Total assignments fetched from BPS API:", len(all_assignments))
            ids = [c['id'] for c in all_assignments]
            code_idents = [c['codeIdentity'] for c in all_assignments]
            
            print("Unique Assignment IDs:", len(set(ids)))
            print("Unique Code Identities:", len(set(code_idents)))
            
            # Print duplicates if any
            from collections import Counter
            id_counts = Counter(ids)
            dup_ids = [k for k, v in id_counts.items() if v > 1]
            print("Number of duplicate Assignment IDs:", len(dup_ids))
            for d in dup_ids[:5]:
                print(f"ID {d} occurs {id_counts[d]} times:")
                for c in all_assignments:
                    if c['id'] == d:
                        print(f"  Name: {c['name']}, CodeIdentity: {c['codeIdentity']}, Region: {c['region']}")

        except Exception as e:
            print("Error:", e)

asyncio.run(check_via_browser())
