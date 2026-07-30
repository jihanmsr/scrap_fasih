import requests
import json
import time

HEADERS = {
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.9',
    'content-type': 'application/json',
    'cookie': 'f5avraaaaaaaaaaaaaaaa_session_=JONOBLEHNMJHKLLEFEKFINOIEIFLAEIPJKFIDAFKPAAOKFPHKBNLJHKIAAHFLBLBFGMDLAEPJGMFADDLBPAANGDFBGKDCACELECOMBGHBAJFLNGGMLGPOKLBCINCEBHP; db8ca2b43ed851cc93e71fd5fd72bff7=9ece61c47ecc337c80c51b0520942d99; SESSION=3731f384-f133-41cd-bea1-15e55d5d9127; f5avraaaaaaaaaaaaaaaa_session_=MIKCBGNAIJNPCOIBFLKIPLLOKLDLEBCBALKHBNIMMGLLDEBGGLOAGPDOFLNABJMIAHKDMGAHOEOBGANPOBDAKIGEDFLGPJPBMIIEIJAKHPMEBBDBLPDONCNDHJHPDNKH; XSRF-TOKEN=493c31f7-8e50-440b-80c7-144231cc15fa',
    'origin': 'https://fasih-sm.bps.go.id',
    'referer': 'https://fasih-sm.bps.go.id/app/surveys/a0429e96-51a5-477b-a415-485f9c153004/fd68e454-ba45-4b85-8205-f3bf777ded24',
    'sec-ch-ua': '"Not;A=Brand";v="8", "Chromium";v="150", "Google Chrome";v="150"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36',
    'x-xsrf-token': '493c31f7-8e50-440b-80c7-144231cc15fa'
}

def get_report(kab_code):
    url = 'https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/report-user-assignment'
    payload = {
        "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24",
        "assignmentStatusAlias": None,
        "assignmentErrorStatusType": -1,
        "data1": "72",
        "data2": kab_code,
        "data3": None, "data4": None, "data5": None, "data6": None, "data7": None,
        "data8": None, "data9": None, "data10": None, "regionId": None,
        "currentUserId": None, "userIdResponsibility": None
    }
    try:
        response = requests.post(url, headers=HEADERS, json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error {kab_code}: {e}")
        return None

results = {}
kabupatens = ["7201", "7202", "7203", "7204", "7205", "7206", "7207", "7208", "7209", "7210", "7211", "7212", "7271"]

for kab in kabupatens:
    print(f"Fetching {kab}...")
    data = get_report(kab)
    results[kab] = data
    time.sleep(0.5)

with open('alokasi_petugas_72.json', 'w') as f:
    json.dump(results, f, indent=2)
print("Data saved to alokasi_petugas_72.json")
