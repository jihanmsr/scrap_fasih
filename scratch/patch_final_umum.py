import re

with open('generate_ipas_report.py', 'r') as f:
    code = f.read()

# Replace the kabs array in se_umum with the correct Group 1 UUIDs
correct_umum_kabs = """                "kabs": [
                    {"code": "01", "name": "[01] BANGGAI KEPULAUAN", "id": "bc32354f-1245-426f-b2cf-a5733e1295ad"},
                    {"code": "02", "name": "[02] BANGGAI", "id": "530e9ca5-86ba-434e-9b04-405102e6d900"},
                    {"code": "03", "name": "[03] MOROWALI", "id": "9783f0c1-f047-477f-8840-11eae7cf70e2"},
                    {"code": "04", "name": "[04] POSO", "id": "fb9cd9f0-c4c0-4a37-9041-57190693f625"},
                    {"code": "05", "name": "[05] DONGGALA", "id": "289f1ff3-a6ad-4c9b-a49f-7b454d03a33f"},
                    {"code": "06", "name": "[06] TOLI-TOLI", "id": "d833fdce-ebfb-429b-a1bb-8966239fd8e4"},
                    {"code": "07", "name": "[07] BUOL", "id": "c523694a-2e72-4570-9489-da2d7b119fe7"},
                    {"code": "08", "name": "[08] PARIGI MOUTONG", "id": "25c59fd9-afd5-4c1a-9dfb-42bb697a7434"},
                    {"code": "09", "name": "[09] TOJO UNA-UNA", "id": "736c4c22-51d1-44be-8b2c-aa197d9459a4"},
                    {"code": "10", "name": "[10] SIGI", "id": "0061da62-2a47-4dee-b8d0-239b33e2c59d"},
                    {"code": "11", "name": "[11] BANGGAI LAUT", "id": "eed1a3e7-b81d-4fc7-b0d6-61257c1449b2"},
                    {"code": "12", "name": "[12] MOROWALI UTARA", "id": "d05ef8fd-b5e4-414f-9a83-8cdea03e0767"},
                    {"code": "71", "name": "[71] PALU", "id": "557a66b1-0bc7-4340-a359-99fc545aeb78"}
                ]"""

old_umum_kabs = re.search(r'"se_umum": \{.*?("kabs": \[.*?\]).*?"se_ub": \{', code, re.DOTALL).group(1)
code = code.replace(old_umum_kabs, correct_umum_kabs)

# Now fix the loop
# Find the loop body starting from 'for kab in survey_cfg["kabs"]:'
loop_start = code.find('            for kab in survey_cfg["kabs"]:')
loop_end = code.find('            # 2. Fetch new_usaha_today')
if loop_start != -1 and loop_end != -1:
    old_loop = code[loop_start:loop_end]
    new_loop = """            for kab in survey_cfg["kabs"]:
                if survey_key == "se_umum":
                    payload = {
                        "start": 0, "length": 1, "columns": [{"data": "id"}], "order": [], "search": {"value": "", "regex": False},
                        "assignmentExtraParam": {
                            "region1Id": survey_cfg["prov_id"],
                            "region2Id": kab["id"],
                            "surveyPeriodId": period_id,
                            "assignmentErrorStatusType": -1,
                            "filterTargetType": ""
                        }
                    }
                    res_aggr = await page.evaluate(f\"\"\"
                        async () => {{
                            try {{
                                const r = await fetch('{datatable_url}', {{ 
                                    method: "POST", headers: {{ "Content-Type": "application/json", "X-XSRF-TOKEN": '{token}' }},
                                    body: JSON.stringify({json.dumps(payload)})
                                }});
                                return await r.json();
                            }} catch(e) {{ return null; }}
                        }}
                    \"\"\")
                    
                    if res_aggr and "searchAggregation" in res_aggr:
                        aggr = res_aggr["searchAggregation"]
                        report_data[kab["name"]]["total_prelist"] = sum(i["docCount"] for i in aggr)
                        report_data[kab["name"]]["total_draft"] = sum(i["docCount"] for i in aggr if i["keyAggregation"] == "DRAFT")
                        report_data[kab["name"]]["total_open"] = sum(i["docCount"] for i in aggr if i["keyAggregation"] == "OPEN")
                        report_data[kab["name"]]["total_submitted"] = sum(i["docCount"] for i in aggr if "SUBMITTED" in i["keyAggregation"])
                        report_data[kab["name"]]["total_rejected"] = sum(i["docCount"] for i in aggr if "REJECTED" in i["keyAggregation"])
                else:
                    url = f"https://fasih-sm.bps.go.id/app/api/analytic/api/v2/se-2026/report-progress-listing-usaha?aggregationType=kabupaten&regionId={kab['id']}&isUb=true"
                    res = await page.evaluate(f\"\"\"
                        async () => {{
                            try {{
                                const r = await fetch('{url}', {{ headers: {{ "X-XSRF-TOKEN": '{token}' }} }});
                                return await r.json();
                            }} catch(e) {{ return null; }}
                        }}
                    \"\"\")
                    
                    if res and "data" in res and isinstance(res["data"], list) and len(res["data"]) > 0:
                        item = res["data"][0]
                        report_data[kab["name"]]["total_prelist"] = item.get("total_prelist", 0)
                        report_data[kab["name"]]["total_draft"] = item.get("total_draft", 0)
                        report_data[kab["name"]]["total_open"] = item.get("total_open", 0)
                        report_data[kab["name"]]["total_submitted"] = item.get("total_submitted", 0)
                        report_data[kab["name"]]["total_rejected"] = item.get("total_rejected", 0)
                        report_data[kab["name"]]["total_approved"] = item.get("total_approved", 0)
            """
    code = code.replace(old_loop, new_loop)

# Fix province_id for se_umum. In datatable-all-user-survey-periode, prov_id is b640a1f2-a891-4a1f-8716-c6c73b3a49f1
code = code.replace('"5214ecb2-bef1-4a86-9446-451cf430928e"', '"b640a1f2-a891-4a1f-8716-c6c73b3a49f1"')

with open('generate_ipas_report.py', 'w') as f:
    f.write(code)
print("generate_ipas_report.py heavily patched for accurate datatable SE_UMUM aggregation!")
