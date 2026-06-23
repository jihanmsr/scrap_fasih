with open("scrape_granular_core.py", "r", encoding="utf-8") as f:
    code = f.read()

import re

# Find the start and end of fetch_desa_granular
start_idx = code.find("async def fetch_desa_granular")
if start_idx == -1:
    print("Function not found!")
    exit(1)
    
end_idx = code.find("def parse_date_to_epoch", start_idx)
if end_idx == -1:
    print("End not found!")
    exit(1)

new_func = """async def fetch_desa_granular(client, survey_period_id, region1_id, kab_id, kec_id, desa_id, kab_name, kec_name, desa_name, label, sem):
    global completed_desas, total_desas
    
    start = 0
    length = 1000
    all_records = []
    
    columns_payload = [
        {"data": "id"},
        {"data": "codeIdentity"},
        {"data": "data1"},
        {"data": "assignmentStatusAlias"},
        {"data": "currentUserUsername"},
        {"data": "currentUserFullname"},
        {"data": "dateCreated"},
        {"data": "dateModified"},
        {"data": "region"}
    ]
    
    while True:
        payload = {
            "start": start,
            "length": length,
            "columns": columns_payload,
            "order": [],
            "search": {"value": "", "regex": False},
            "assignmentExtraParam": {
                "region1Id": region1_id,
                "region2Id": kab_id,
                "region3Id": kec_id,
                "region4Id": desa_id,
                "surveyPeriodId": survey_period_id,
                "assignmentErrorStatusType": -1,
                "filterTargetType": ""
            }
        }
        
        res = None
        for attempt in range(4):
            async with sem:
                try:
                    r = await client.post(DATATABLE_URL, json=payload)
                    if r.status_code == 200:
                        res = r.json()
                        break
                    else:
                        res = {"_error": f"HTTP {r.status_code}"}
                except Exception as e:
                    res = {"_error": str(e)}
            await asyncio.sleep(0.05)
            if res and isinstance(res, dict) and "_error" not in res:
                break
            else:
                await asyncio.sleep(1.0)
                
        if not res or "_error" in res or "searchData" not in res:
            print(f"      [ERROR] Gagal ambil page data {start} untuk Desa {desa_name}.")
            break
            
        records = res["searchData"]
        if not records:
            break
            
        all_records.extend(records)
        
        if len(records) < length or len(all_records) >= res.get("totalHit", 0):
            break
            
        start += length
        
    async with progress_lock:
        completed_desas += 1
        if completed_desas % 50 == 0 or completed_desas == total_desas:
            print(f"      [PROGRESS] SE Umum: Downloaded {completed_desas} / {total_desas} desas...", flush=True)
            
    return all_records

"""

code = code[:start_idx] + new_func + code[end_idx:]

# Also fix the call to fetch_desa_granular
code = code.replace("""                            fetch_desa_granular(
                                client, 
                                cfg_umum["survey_period_id"], 
                                cfg_umum["region1_id"], 
                                kab_cfg["id"], 
                                kec_data["kec_id"], 
                                desa_data["desa_id"], 
                                kab_cfg["name"], 
                                kec_name, 
                                desa_name, 
                                "SE Umum", 
                                sem_umum,
                                raw_se_umum_data,
                                sls_list=desa_data.get("sls", [])
                            )""", """                            fetch_desa_granular(
                                client, 
                                cfg_umum["survey_period_id"], 
                                cfg_umum["region1_id"], 
                                kab_cfg["id"], 
                                kec_data["kec_id"], 
                                desa_data["desa_id"], 
                                kab_cfg["name"], 
                                kec_name, 
                                desa_name, 
                                "SE Umum", 
                                sem_umum
                            )""")

with open("scrape_granular_core.py", "w", encoding="utf-8") as f:
    f.write(code)

print("Patch applied successfully.")
