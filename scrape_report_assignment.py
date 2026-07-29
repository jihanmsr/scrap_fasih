import requests
import json
import os
import time

# Cookie dan Headers dari curl request
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

def get_report_assignment(prov=None, kab=None, kec=None, desa=None, sls=None):
    url = 'https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/report-user-assignment'
    
    payload = {
        "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24",
        "assignmentStatusAlias": None,
        "assignmentErrorStatusType": -1,
        "data1": prov,
        "data2": kab,
        "data3": kec,
        "data4": desa,
        "data5": sls,
        "data6": None,
        "data7": None,
        "data8": None,
        "data9": None,
        "data10": None,
        "regionId": None,
        "currentUserId": None,
        "userIdResponsibility": None
    }

    try:
        response = requests.post(url, headers=HEADERS, json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

if __name__ == "__main__":
    # Contoh ambil data untuk Provinsi 72
    print("Mengambil data untuk Provinsi 72...")
    data_prov = get_report_assignment(prov="72")
    print(json.dumps(data_prov, indent=2))
    
    # Contoh ambil data untuk Kabupaten 7205
    print("\nMengambil data untuk Kabupaten 7205...")
    data_kab = get_report_assignment(prov="72", kab="7205")
    print(json.dumps(data_kab, indent=2))

    # TODO: Bisa ditambahkan looping untuk semua kabupaten/kecamatan/desa sesuai kebutuhan
    # menggunakan master wilayah yang sudah ada.
