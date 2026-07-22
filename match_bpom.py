import pandas as pd
import requests
import json
import time

def match_data():
    df = pd.read_excel('hasil_bpom_prov_72_20260720_140549.xlsx')
    
    # Process only KAB 01 (Banggai Kepulauan)
    df_palu = df[df['kdkab'] == 1].copy()
    
    headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9,id-ID;q=0.8,id;q=0.7',
        'content-type': 'application/json',
        'origin': 'https://fasih-sm.bps.go.id',
        'referer': 'https://fasih-sm.bps.go.id/app/surveys/a0429e96-51a5-477b-a415-485f9c153004/fd68e454-ba45-4b85-8205-f3bf777ded24/data?page=1&perPage=10',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36',
        'x-xsrf-token': '25a960b8-0e8b-4269-85de-eda44d3f24a0'
    }

    cookies = {
        'f5avraaaaaaaaaaaaaaaa_session_': 'HDIJEICKOFCANFAIOEELMDPGFNINNILDDLGKEDDKKLBEBJJPEBFBEDKAIKIMNMDFLFGDBJBABIKCBLGLCDNANBPGNCPHGCMFDECDCEFGIENBEBPEJKPPNFOGHMEHHGLI',
        '_ga': 'GA1.1.411082986.1784444638',
        'db8ca2b43ed851cc93e71fd5fd72bff7': '1e9c1d1d24bcbe65a32da54dd7e4755e',
        'XSRF-TOKEN': '25a960b8-0e8b-4269-85de-eda44d3f24a0',
        'JSESSIONID': 'B7CC2F5A31C0AB729C01089D4CCEE4AB',
        'SESSION': 'e410a908-5a2c-416b-8949-bddd5ecee958'
    }
    
    statuses = []
    
    for idx, row in df_palu.iterrows():
        nama = str(row['nama_usaha'])
        
        payload = {
            "start": 0,
            "length": 50,
            "columns": [],
            "order": [],
            "search": {"value": nama, "regex": False},
            "assignmentExtraParam": {
                "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e",
                "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24",
                "assignmentErrorStatusType": -1,
                "filterTargetType": "TARGET_ONLY"
            }
        }
        
        try:
            r = requests.post(
                'https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode',
                headers=headers,
                cookies=cookies,
                json=payload,
                timeout=10
            )
            data = r.json()
            
            hits = data.get('searchData', [])
            
            # Filter by kdkab
            filtered_hits = []
            for hit in hits:
                try:
                    if hit['region']['level1']['level2']['code'] == '01':
                        filtered_hits.append(hit)
                except Exception:
                    pass
            
            if len(filtered_hits) > 0:
                statuses.append(filtered_hits[0].get('assignmentStatusAlias', 'NOT_FOUND'))
            else:
                statuses.append('NOT_FOUND')
                
        except Exception as e:
            print(f"Error on {nama}: {e}")
            statuses.append('ERROR')
            
        time.sleep(0.1) # Be nice to the server

    df_palu['status'] = statuses
    df_palu.to_excel('hasil_bpom_prov_72_kab01.xlsx', index=False)
    
    print(f"Done processing KAB 01. Matches: {len([s for s in statuses if s not in ('NOT_FOUND', 'ERROR')])} / {len(statuses)}")

if __name__ == "__main__":
    match_data()
