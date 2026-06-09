import re

with open('generate_ipas_report.py', 'r') as f:
    code = f.read()

new_prov_total = """            
            # Fetch PROVINCE TOTAL
            if survey_key == "se_umum":
                payload_prov = {
                    "start": 0, "length": 1, "columns": [{"data": "id"}], "order": [], "search": {"value": "", "regex": False},
                    "assignmentExtraParam": {
                        "surveyPeriodId": period_id,
                        "assignmentErrorStatusType": -1
                    }
                }
                res_prov = await page.evaluate(f\"\"\"
                    async () => {{
                        try {{
                            const r = await fetch('{datatable_url}', {{ 
                                method: "POST", headers: {{ "Content-Type": "application/json", "X-XSRF-TOKEN": '{token}' }},
                                body: JSON.stringify({json.dumps(payload_prov)})
                            }});
                            return await r.json();
                        }} catch(e) {{ return null; }}
                    }}
                \"\"\")
                prov_total = 0
                if res_prov and "searchAggregation" in res_prov:
                    prov_total = sum(i["docCount"] for i in res_prov["searchAggregation"])
                report_data["PROVINSI_TOTAL"] = prov_total

            for kab in survey_cfg["kabs"]:
"""

code = code.replace('            for kab in survey_cfg["kabs"]:', new_prov_total, 1)

# Modify output_data extraction
code = code.replace('        output_data[survey_key] = list(report_data.values())', 
                    '        output_data[survey_key] = [v for k, v in report_data.items() if k != "PROVINSI_TOTAL"]\n        if "PROVINSI_TOTAL" in report_data:\n            output_data[survey_key + "_prov_total"] = report_data["PROVINSI_TOTAL"]')

with open('generate_ipas_report.py', 'w') as f:
    f.write(code)
print("Patched prov total!")
