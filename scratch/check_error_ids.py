import asyncio
import json
from auth_handler import get_authenticated_context
from utils import fetch_api_safely

async def main():
    ctx = await get_authenticated_context()
    xsrf_token = ctx["xsrf_token"]
    
    with open("config.json", "r") as f:
        config = json.load(f)
        
    prov_id = "07fbcbf0-3eeb-4bc2-af82-595304bc2b6f" # Sulteng
    period_id = "fd68e454-ba45-4b85-8205-f3bf777ded24" # SE UMUM
    
    datatable_url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode"
    
    # Let's query assignmentErrorStatusType = 1 or 2 (or just everything minus 0, wait, API might only accept exact match or -1)
    # Let's try to get them by passing assignmentErrorStatusType: 1 (Error) and 2 (Dropped)
    
    error_ids = []
    
    for status_type in [1, 2]:
        payload = {
            "start": 0, "length": 1000, 
            "columns": [{"data": "id"}, {"data": "codeIdentity"}, {"data": "data1"}], 
            "order": [], "search": {"value": "", "regex": False},
            "assignmentExtraParam": {
                "region1Id": prov_id,
                "surveyPeriodId": period_id,
                "assignmentErrorStatusType": status_type,
                "filterTargetType": "target"
            }
        }
        res = await fetch_api_safely(datatable_url, payload, xsrf_token)
        if res and "searchData" in res:
            records = res["searchData"]
            for r in records:
                error_ids.append({
                    "id": r.get("id"),
                    "codeIdentity": r.get("codeIdentity"),
                    "name": r.get("data1"),
                    "errorType": status_type
                })
            print(f"Found {len(records)} records with errorStatusType={status_type}")
            
    print(f"Total error/dropped: {len(error_ids)}")
    with open("error_targets.json", "w") as f:
        json.dump(error_ids, f, indent=2)

asyncio.run(main())
