import pandas as pd
import requests
import json
import time
import sys
import os

def match_data():
    df = pd.read_excel('hasil_bpom_prov_72_kab01.xlsx')
    
    headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9,id-ID;q=0.8,id;q=0.7',
        'content-type': 'application/json',
        'origin': 'https://fasih-sm.bps.go.id',
        'referer': 'https://fasih-sm.bps.go.id/app/surveys/a0429e96-51a5-477b-a415-485f9c153004/fd68e454-ba45-4b85-8205-f3bf777ded24/data?page=1&perPage=10',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36',
        'x-xsrf-token': '25a960b8-0e8b-4269-85de-eda44d3f24a0',
        'cookie': 'f5avraaaaaaaaaaaaaaaa_session_=AHILIAJOGGAOCBJKCNHJBJBJHPCGPDPAPOJEEDDKPHADMNDIPEPINAMDPJODLHENBPADPANCPAGDBHBKJBKANMCAADIDILIIEEOCNPFCIFBFKHENFCFKHNGEJOBCALMB; _ga_FMZTHHQN2K=GS2.1.s1784444662$o1$g0$t1784444662$j60$l0$h0; _ga_XXTTVXWHDB=GS2.3.s1784513566$o2$g0$t1784513568$j58$l0$h0; _ga=GA1.1.411082986.1784444638; _ga_QPPE1C18C5=GS2.1.s1784513560$o3$g1$t1784513632$j60$l0$h0; db8ca2b43ed851cc93e71fd5fd72bff7=1e9c1d1d24bcbe65a32da54dd7e4755e; XSRF-TOKEN=25a960b8-0e8b-4269-85de-eda44d3f24a0; JSESSIONID=B7CC2F5A31C0AB729C01089D4CCEE4AB; SESSION=e410a908-5a2c-416b-8949-bddd5ecee958; f5avraaaaaaaaaaaaaaaa_session_=EDPDMNNGLIFBJHKJJBCCGKHKCOPGMGJJNNBPKPJOLNFKAKCOBOGOIJABDMPCJAIICHGDEEPOLHJCBGGONFIAKHKJPCNIKPFMHDIJHEHAGFIOJNDDGKODHOMBMBFGICPL; TS011f2d1a=01266d26d02a918312a461534cf67fd625f860e84384e7796147451402098933979bbfeb752b713171318503dd40033c1ba126770b; TS00000000076=0868f8be6fab2800dfceb14c51b306ff9b4547817a4473835aa01f87137784760397acf79022e361f28ed7f065e3a72e080ac378c809d000accbcd03086892abeb2da193bca169248b989c7fe3b19b73266be8da8a64df33e035cfbd36d861c0c7efb407838e129e454e037d8c0b44808716d8d5d796df1bc392bf0856da1a6ccadbbe769e1c399cd8a1bd83dc79eedf86db4946e6b9cd0f74e35493a0d232fd293c4f88cc70ce3dafc0eadddfe1042b543c634c4ef0cab2c280264a8f3c6ecb81f909b589e3c77b8f5fca517856cd55d3ed1dfce4da69f2fabf520cdf8b4a754ab153b75d22c2320c487a3f12deb85e56d22d9200097fa28b71141f75d40d2c27a56a5def34e8dd; TSPD_101_DID=0868f8be6fab2800dfceb14c51b306ff9b4547817a4473835aa01f87137784760397acf79022e361f28ed7f065e3a72e080ac378c806380020e552d03192afe66f60a2a0c27931f5c335bd04609bd06898e462f3e0e4ed81973634607242485a01e09ce9321bf3172d22b89ebe21d9fd; TSPD_101=0868f8be6fab2800b32b9ad7415b6e89f1f7c0a0dbdc600731ab70c28b3ac0326f4c59278b9c634d86750b506a4065550863f83faf051800856d72ed34a8b8165ca1732140a3428bba23ce13beb1c95e; TS5220f739077=0868f8be6fab280044b1e342463deb7056970653b938b13050dd2a3ce672c8a368a7f6dad5e10d95fbfc4340d85cba4c08ce00a30717200062bd84da830640e0ffb920bee3576360703f1cea183a550e442bfcdad729002b; TS5220f739029=0868f8be6fab28003c61e0567273c6952035e05ba6d25849a44c506913ba74758763101778b266b47136367616668817; TSf1edb2d2027=0868f8be6fab20002e2d01915cc46e87825fd9ed8b822e70bd63b21bc1ba511c5b1d92be386f175e085c65d6d41130005d6befb47f15fce423d3018a5c08f8e2e57f8086d3123ae701053ea8e6efaaab743af2fd3c66a4c4d45bb222f8aa3818'
    }

    statuses = []
    
    cols = [{"data":"id","orderable":True},{"data":"codeIdentity","orderable":True},{"data":"data1","orderable":True},{"data":"data2","orderable":True},{"data":"data3","orderable":True},{"data":"data4","orderable":True},{"data":"data5","orderable":True},{"data":"data6","orderable":True},{"data":"data7","orderable":True},{"data":"data8","orderable":True},{"data":"data9","orderable":True},{"data":"data10","orderable":True}]
    
    def search_api(val):
        start = 0
        length = 150
        all_hits = []
        while True:
            payload = {
                "start": start, "length": length, "columns": cols, "order": [],
                "search": {"value": val, "regex": False},
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
                    headers=headers, json=payload, timeout=10
                )
                data = r.json()
            except Exception as e:
                print(f"Net Error: {e}")
                time.sleep(5) # Wait before retry
                break
                
            if 'error' in data:
                if data['status'] == 429: # Rate limit
                    time.sleep(10) # Wait 10 seconds for rate limit to reset!
                    continue # Retry the same request!
                else:
                    print(f"API Error: {data}")
                    break
                
            hits = data.get('searchData', [])
            all_hits.extend(hits)
            
            total_hits = data.get('totalHit', 0)
            if start + length >= total_hits:
                break
            start += length
            time.sleep(1) # Be nice to the server between pagination
        return all_hits

    for idx, row in df.iterrows():
        code = f"{int(row['kdprov']):02d}{int(row['kdkab']):02d}{int(row['kdkec']):03d}{int(row['kddesa']):03d}{int(row['kdsls']):04d}{int(row['kdsubsls']):02d}"
        assignment_id = str(row['assignment_id'])
        
        nama = str(row['nama_pengusaha'])
        if pd.isna(row['nama_pengusaha']) or nama == 'nan':
            nama = str(row['nama_usaha'])
        if '(' in nama:
            nama = nama.split('(')[0].strip()
            
        match_status = 'NOT_FOUND'
        try:
            hits = search_api(code)
            for hit in hits:
                if hit.get('id') == assignment_id:
                    match_status = hit.get('assignmentStatusAlias', 'UNKNOWN_STATUS')
                    break
            
            if match_status == 'NOT_FOUND':
                hits2 = search_api(nama)
                for hit in hits2:
                    if hit.get('id') == assignment_id:
                        match_status = hit.get('assignmentStatusAlias', 'UNKNOWN_STATUS')
                        break

            statuses.append(match_status)
        except Exception as e:
            print(f"Exception on {code}: {e}")
            statuses.append('ERROR')
            
        time.sleep(2) # 2 second sleep between completely new rows to prevent rate limit
        sys.stdout.write(f"\rProcessed {idx+1}/{len(df)}: {match_status} (Name: {nama}, Code: {code})                    ")
        sys.stdout.flush()

    df['status_by_id'] = statuses
    df.to_excel('hasil_bpom_prov_72_kab01_final.xlsx', index=False)
    print(f"\nDone processing KAB 01. Matches by ID: {len([s for s in statuses if s not in ('NOT_FOUND', 'ERROR', 'ERROR_DECODE', 'ERROR_NET')])} / {len(statuses)}")

if __name__ == "__main__":
    match_data()
