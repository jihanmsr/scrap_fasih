import requests
import json

headers = {
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.9',
    'content-type': 'application/json',
    'cookie': 'f5avraaaaaaaaaaaaaaaa_session_=JONOBLEHNMJHKLLEFEKFINOIEIFLAEIPJKFIDAFKPAAOKFPHKBNLJHKIAAHFLBLBFGMDLAEPJGMFADDLBPAANGDFBGKDCACELECOMBGHBAJFLNGGMLGPOKLBCINCEBHP; db8ca2b43ed851cc93e71fd5fd72bff7=9ece61c47ecc337c80c51b0520942d99; SESSION=3731f384-f133-41cd-bea1-15e55d5d9127; f5avraaaaaaaaaaaaaaaa_session_=MIKCBGNAIJNPCOIBFLKIPLLOKLDLEBCBALKHBNIMMGLLDEBGGLOAGPDOFLNABJMIAHKDMGAHOEOBGANPOBDAKIGEDFLGPJPBMIIEIJAKHPMEBBDBLPDONCNDHJHPDNKH; XSRF-TOKEN=493c31f7-8e50-440b-80c7-144231cc15fa; TS00000000076=0868f8be6fab2800980769e3bd3a8287e36675b79fc3041812d95f085e3c12e933d82901790903d95db343b2a1ffc0610875306e8a09d000e6dee1525afa90742b294e071e5fe95a07ab0e7c5f9857425ae665f486ced2547fe4a9776e87909d9e1fc753058dd37fcf1e5139d4ed1a6b2a923b1d03b6c992eae98205d47ebf51b45b193bbbf904abf259c00a92fb8b6e1d8ad436df2c7c5a98ca2ccf31bdfc51dd60c1c73b28549ccdd25faf7225e772afcfff50846e258ddf5bc945e837929a5902235d3721669241c3bad60e443b7a33dd53cb14d78e68994a5d83f9fa73e0a431c74a478f22fdd6afbfc1019dba4f3e7a2904912a38623cc28494bd78f03c03c1f7379af3203c; TSPD_101_DID=0868f8be6fab2800980769e3bd3a8287e36675b79fc3041812d95f085e3c12e933d82901790903d95db343b2a1ffc0610875306e8a063800ff45495490715517e553d7fc8f3b1fc90e027cef20d6d5269e2e1866d6dcf7553b630aecda43c2e68f570768251c28a1adce6f63b6ced4e7; TS011f2d1a=01266d26d0c43dc9cc4c93f32294d678cb026cb5fd23ce413dd338a352a1f5e4a1931cc282b4fb5581ea95431ecbc8c8b2d2f011e5; TSPD_101=0868f8be6fab28002d09aa48c771c0656b81788b6f43e680a69b162783863acc603ee09f9a3919f8c3850365de44341108bf665853051800beeb1a4c93b3d1a25ca1732140a3428bba23ce13beb1c95e; TS5220f739077=0868f8be6fab280088a57a99c0692dcf6a6fd6faa5882d5cb78b3f98255815c849d8fac4b23d9e3a5f3aa2f144a748e208ecf64995172000a32b85574b9c874de1a0caaf21e34b071ddb56100fe824b6f4bc20ab6307eeaf; TS5220f739029=0868f8be6fab28002561edc109dd2d81c0a9b899059aa506fb8e6072c406c81de6894f87480319c512eff8b17aaff632; TSf1edb2d2027=0868f8be6fab2000b6141b678bff9d6cd632fb5d93c2a30d2fcbd41b36e62f6430a40894d0ef6b52086acd6ca9113000959caaca0fd5735f0b2432a7ad5af89006d1f1b5f6bc65c05fbc88f43323ddd1c677d7ae6d221aa6cf1a67cd1b2aa5cc',
    'origin': 'https://fasih-sm.bps.go.id',
    'priority': 'u=1, i',
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

data = {
    "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24",
    "assignmentStatusAlias": None,
    "assignmentErrorStatusType": -1,
    "data1": "72",
    "data2": "7205",
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

print(response.status_code)
print(response.text[:1000])

