import requests
import json

headers = {
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.9',
    'content-type': 'application/json',
    'cookie': 'f5avraaaaaaaaaaaaaaaa_session_=JONOBLEHNMJHKLLEFEKFINOIEIFLAEIPJKFIDAFKPAAOKFPHKBNLJHKIAAHFLBLBFGMDLAEPJGMFADDLBPAANGDFBGKDCACELECOMBGHBAJFLNGGMLGPOKLBCINCEBHP; db8ca2b43ed851cc93e71fd5fd72bff7=9ece61c47ecc337c80c51b0520942d99; SESSION=3731f384-f133-41cd-bea1-15e55d5d9127; f5avraaaaaaaaaaaaaaaa_session_=MIKCBGNAIJNPCOIBFLKIPLLOKLDLEBCBALKHBNIMMGLLDEBGGLOAGPDOFLNABJMIAHKDMGAHOEOBGANPOBDAKIGEDFLGPJPBMIIEIJAKHPMEBBDBLPDONCNDHJHPDNKH; XSRF-TOKEN=493c31f7-8e50-440b-80c7-144231cc15fa',
    'origin': 'https://fasih-sm.bps.go.id',
    'referer': 'https://fasih-sm.bps.go.id/app/surveys/a0429e96-51a5-477b-a415-485f9c153004/fd68e454-ba45-4b85-8205-f3bf777ded24',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
    'x-xsrf-token': '493c31f7-8e50-440b-80c7-144231cc15fa'
}

data = {
    "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24",
    "assignmentStatusAlias": None,
    "assignmentErrorStatusType": -1,
    "data1": "72",
    "data2": None,
    "data3": None,
    "data4": None,
    "data5": None,
    "data6": None,
    "data7": None,
    "data8": None,
    "data9": None,
    "data10": None,
    "regionId": None,
    "currentUserId": None,
    "userIdResponsibility": None
}

response = requests.post('https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/report-user-assignment', headers=headers, json=data)
print(response.text[:1000])

