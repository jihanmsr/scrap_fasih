import re

with open('generate_ipas_report.py', 'r') as f:
    content = f.read()

# Replace the kab_data definition to include both UUIDs
new_kab_data = """
        # UMUM Group ID: a45adac1-e711-4c15-b3f9-1f30fc151565
        # UB Group ID: 6b0b053f-aa43-4855-ac8f-26857b735c93
        kab_data = [
            {"name": "[01] BANGGAI KEPULAUAN", "uuid_umum": "bc32354f-1245-426f-b2cf-a5733e1295ad", "uuid_ub": "9c9b2d79-9fb1-4ce7-b0f1-6b7bb5511beb"},
            {"name": "[02] BANGGAI", "uuid_umum": "530e9ca5-86ba-434e-9b04-405102e6d900", "uuid_ub": "34165dd5-372e-42fa-99c6-0cc19a9b4d0b"},
            {"name": "[03] MOROWALI", "uuid_umum": "9783f0c1-f047-477f-8840-11eae7cf70e2", "uuid_ub": "9d90ecaa-f350-4288-bcbb-f9630c144e5f"},
            {"name": "[04] POSO", "uuid_umum": "fb9cd9f0-c4c0-4a37-9041-57190693f625", "uuid_ub": "583348f9-4d62-4217-a1f7-e772f4e3c965"},
            {"name": "[05] DONGGALA", "uuid_umum": "289f1ff3-a6ad-4c9b-a49f-7b454d03a33f", "uuid_ub": "a24446c7-3b26-4cf3-bf7b-bd761356e267"},
            {"name": "[06] TOLI-TOLI", "uuid_umum": "d833fdce-ebfb-429b-a1bb-8966239fd8e4", "uuid_ub": "b34e4020-e2b2-4d20-b4d4-28b3e85e4933"},
            {"name": "[07] BUOL", "uuid_umum": "c523694a-2e72-4570-9489-da2d7b119fe7", "uuid_ub": "63f7331d-b8d4-469b-983d-e490455a29ed"},
            {"name": "[08] PARIGI MOUTONG", "uuid_umum": "25c59fd9-afd5-4c1a-9dfb-42bb697a7434", "uuid_ub": "ecf543dc-803d-4c31-97b7-6bcf59600a94"},
            {"name": "[09] TOJO UNA-UNA", "uuid_umum": "736c4c22-51d1-44be-8b2c-aa197d9459a4", "uuid_ub": "b78b876d-1bf9-45e0-a7d5-d0c2e92c0b2b"},
            {"name": "[10] SIGI", "uuid_umum": "0061da62-2a47-4dee-b8d0-239b33e2c59d", "uuid_ub": "fc6ec155-70ad-48b0-8c2d-dbf4a0c88599"},
            {"name": "[11] BANGGAI LAUT", "uuid_umum": "eed1a3e7-b81d-4fc7-b0d6-61257c1449b2", "uuid_ub": "5b9e07f9-67d1-4db5-b8dd-1a5200234a41"},
            {"name": "[12] MOROWALI UTARA", "uuid_umum": "d05ef8fd-b5e4-414f-9a83-8cdea03e0767", "uuid_ub": "cc5fc252-054d-4ba6-992a-dd041df67140"},
            {"name": "[71] PALU", "uuid_umum": "557a66b1-0bc7-4340-a359-99fc545aeb78", "uuid_ub": "cc5b736b-67df-420a-8bf8-09ee8650e854"},
        ]
"""

content = re.sub(r'kab_data = \[\s*\{"name".*?\]', new_kab_data.strip(), content, flags=re.DOTALL)

# Replace url_umum and url_ub loops
old_loop = """
        for item in kab_data:
            kab_name = item["name"]
            kab_uuid = item["uuid"]
            
            # 1. IPAS Umum
            url_umum = f"https://fasih-sm.bps.go.id/app/api/analytic/api/v2/se-2026/report-progress-listing-usaha?aggregationType=kabupaten&regionId={kab_uuid}&isUb=false"
            res_umum = await page.evaluate(f\"\"\"
                async () => {{
                    try {{
                        const r = await fetch('{url_umum}', {{ headers: {{ "X-XSRF-TOKEN": '{token}' }} }});
                        return await r.json();
                    }} catch(e) {{ return null; }}
                }}
            \"\"\")
            
            # 2. IPAS UB
            url_ub = f"https://fasih-sm.bps.go.id/app/api/analytic/api/v2/se-2026/report-progress-listing-usaha?aggregationType=kabupaten&regionId={kab_uuid}&isUb=true"
            res_ub = await page.evaluate(f\"\"\"
                async () => {{
                    try {{
                        const r = await fetch('{url_ub}', {{ headers: {{ "X-XSRF-TOKEN": '{token}' }} }});
                        return await r.json();
                    }} catch(e) {{ return null; }}
                }}
            \"\"\")
"""

new_loop = """
        # We will use datatable-all-user-survey-periode for UMUM to get the EXACT ~1.1M data matching BPS dashboard!
        datatable_url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode"
        
        for item in kab_data:
            kab_name = item["name"]
            uuid_umum = item["uuid_umum"]
            uuid_ub = item["uuid_ub"]
            
            # 1. IPAS Umum (Using datatable searchAggregation)
            payload_umum = {
                "start": 0, "length": 1, "columns": [{"data": "id"}], "order": [], "search": {"value": "", "regex": False},
                "assignmentExtraParam": {
                    "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24", # PENDATAAN
                    "assignmentErrorStatusType": -1,
                    "region2Id": uuid_umum
                }
            }
            res_umum_aggr = await page.evaluate(f\"\"\"
                async () => {{
                    try {{
                        const r = await fetch('{datatable_url}', {{ 
                            method: "POST", headers: {{ "Content-Type": "application/json", "X-XSRF-TOKEN": '{token}' }},
                            body: JSON.stringify({json.dumps(payload_umum)})
                        }});
                        return await r.json();
                    }} catch(e) {{ return null; }}
                }}
            \"\"\")
            
            res_umum = {"data": []}
            if res_umum_aggr and "searchAggregation" in res_umum_aggr:
                aggr = res_umum_aggr["searchAggregation"]
                total = sum(i["docCount"] for i in aggr)
                draft = sum(i["docCount"] for i in aggr if i["keyAggregation"] == "DRAFT")
                open_v = sum(i["docCount"] for i in aggr if i["keyAggregation"] == "OPEN")
                submitted = sum(i["docCount"] for i in aggr if "SUBMITTED" in i["keyAggregation"])
                rejected = sum(i["docCount"] for i in aggr if "REJECTED" in i["keyAggregation"])
                res_umum["data"] = [{
                    "total_prelist": total,
                    "total_draft": draft,
                    "total_open": open_v,
                    "total_submitted": submitted,
                    "total_rejected": rejected,
                    "total_approved": 0 # Not provided but usually included in submitted
                }]
            else:
                # Fallback to the old API if datatable fails
                url_umum_fb = f"https://fasih-sm.bps.go.id/app/api/analytic/api/v2/se-2026/report-progress-listing-usaha?aggregationType=kabupaten&regionId={uuid_umum}&isUb=false"
                res_umum = await page.evaluate(f\"\"\"
                    async () => {{
                        try {{
                            const r = await fetch('{url_umum_fb}', {{ headers: {{ "X-XSRF-TOKEN": '{token}' }} }});
                            return await r.json();
                        }} catch(e) {{ return null; }}
                    }}
                \"\"\")

            # 2. IPAS UB (Using the normal api since UB data is small and accurate)
            url_ub = f"https://fasih-sm.bps.go.id/app/api/analytic/api/v2/se-2026/report-progress-listing-usaha?aggregationType=kabupaten&regionId={uuid_ub}&isUb=true"
            res_ub = await page.evaluate(f\"\"\"
                async () => {{
                    try {{
                        const r = await fetch('{url_ub}', {{ headers: {{ "X-XSRF-TOKEN": '{token}' }} }});
                        return await r.json();
                    }} catch(e) {{ return null; }}
                }}
            \"\"\")
"""

content = content.replace(old_loop.strip(), new_loop.strip())

with open('generate_ipas_report.py', 'w') as f:
    f.write(content)
print("generate_ipas_report.py patched to use correct UUIDs and datatable API for Umum!")
