import pandas as pd
import requests

df = pd.read_excel('hasil_bpom_prov_72_kab01.xlsx')

headers = {
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.9,id-ID;q=0.8,id;q=0.7',
    'content-type': 'application/json',
    'origin': 'https://fasih-sm.bps.go.id',
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

for idx, row in df.head(10).iterrows():
    # Construct 16-digit code:
    code = f"{int(row['kdprov']):02d}{int(row['kdkab']):02d}{int(row['kdkec']):03d}{int(row['kddesa']):03d}{int(row['kdsls']):04d}{int(row['kdsubsls']):02d}"
    print(f"Testing code: {code} for {row['nama_usaha']}")
    
    payload = {
        "start": 0, "length": 10, "columns": [], "order": [],
        "search": {"value": code, "regex": False},
        "assignmentExtraParam": {
            "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e",
            "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24",
            "assignmentErrorStatusType": -1,
            "filterTargetType": "TARGET_ONLY"
        }
    }
    
    r = requests.post(
        'https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode',
        headers=headers, cookies=cookies, json=payload
    )
    
    try:
        data = r.json()
        hits = data.get('searchData', [])
        print(f"Hits: {data.get('totalHit')}")
        for h in hits:
            print(f"  - {h.get('codeIdentity')} | ID match? {h.get('id') == row['assignment_id']}")
    except:
        print("Failed to decode JSON", r.text)

