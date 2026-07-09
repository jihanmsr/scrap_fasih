#!/bin/bash
echo "[" > /Users/jihanmaisaroh/scrap_fasih/fast_results.json
for i in {0..10}; do
  echo "Fetching page $i..."
  curl -s 'https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/report-progress-by-responsibility' \
  -H 'accept: */*' \
  -H 'accept-language: en-US,en;q=0.9,id-ID;q=0.8,id;q=0.7' \
  -H 'content-type: application/json' \
  -b 'f5avraaaaaaaaaaaaaaaa_session_=IPGJPFBCGGABFEADKHECOGLCEBKOGIHFKEMPNFMNLAHIOJNKJPDGKDEFMAOACBJKHBGDKEIFODJEKNPIKMDAJCCHGPOOLPGHFPPMDJHOBKFEJMKINJOPPADIECPJMANH; f5_cspm=1234; db8ca2b43ed851cc93e71fd5fd72bff7=13b6ee7a488307959e12f96ea563eca4; XSRF-TOKEN=c406ff8c-a60b-4c5f-90fa-998f55393663; SESSION=bcc86f50-4d70-4ee2-9549-56b09659236e; TS00000000076=0868f8be6fab2800aa4374f4afeb553a5c7e23146e8123b18d7e031c4da0f69b52baafc86d77b8529465855088f89ec408ad03dac409d00040b7e1a60ffebc6061b69315d0492ba7bebaaa5c62e3deb6410d97de37f0d6dd00d42d3c122060db5d8c661a5ddac91adb34fcfc17bb155cba0eaa13e80df5a1cf70d1e416704261471fec53ff4b73d93d48149fa76a89e803935e151adc266b61d3bb19ca151d95cdaae79d6e0a4390e7667e162cf69ce40d58b3053c0dbcd7fb25af855458a175408b689b24a85cac4564ca6a15dec1366354e8452a3354fb944cae6d3d5629ab93872c76d1eb572fc4c05364bdd7cab8a37f79e0aa6df14aa614238a54c3899864ce057d1892b498; TSPD_101_DID=0868f8be6fab2800aa4374f4afeb553a5c7e23146e8123b18d7e031c4da0f69b52baafc86d77b8529465855088f89ec408ad03dac406380088957f264238030518f078c59d443eb5574e7ee45043b30e21c7acba33a51d433713405f42cb0f8ea1d27eaf217348754c902f2a00bd65e2; TSPD_101=0868f8be6fab2800afce8ed0a17be263a0c508358d9c994e323bababb96acce31cf6d40f93362b4009d12b55f2cfbf5a081b4efa230518008f77aeab177c80df5ca1732140a3428bba23ce13beb1c95e; TS5220f739077=0868f8be6fab28005b028cdc1a457fbdb11c079a30bfde71ec92057c4dbda3fdb6178e511eecc11e4c468b6a1b44a59608d9887266172000e55336d4be77b84fd9c4a74430b9b10ca87912d8e9ea5c3c0852dcc0262c7102; TS011f2d1a=01266d26d0f8c8ee62120202aec1ae51d51a83ae8fb6880a9b53b6f133f71f18b397ad716c12858b46bb57c9cdf04ff6952b7b6f06; TS5220f739029=0868f8be6fab28005884ce5707e241588b14237c35525043d0d4392068fc74489697bbf4b8b12b15af44a9063e21bdbd; TSf1edb2d2027=0868f8be6fab20002eff442b7a135f07b9c542c4f1efbd6cb24dea7f030b774921357a777829e7e30805f1418e113000d9a4553e7a754336b32d924cbdfde699e2b4bbe2d37a862b0cd2667c16f2d8727d26a2ebd43cf8df946ecf2d291d9880' \
  -H 'origin: https://fasih-sm.bps.go.id' \
  -H 'priority: u=1, i' \
  -H 'sec-ch-ua: "Google Chrome";v="149", "Chromium";v="149", "Not)A;Brand";v="24"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "macOS"' \
  -H 'sec-fetch-dest: empty' \
  -H 'sec-fetch-mode: cors' \
  -H 'sec-fetch-site: same-origin' \
  -H 'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36' \
  -H 'x-xsrf-token: c406ff8c-a60b-4c5f-90fa-998f55393663' \
  --data-raw '{"surveyPeriodId":"fd68e454-ba45-4b85-8205-f3bf777ded24","surveyRoleId":"93bcf446-c4c1-4462-8ed0-4b0f7ae89e52","size":100,"page":'"$i"',"search":"","target":"TARGET_ONLY","region":{"region1Id":"5214ecb2-bef1-4a86-9446-451cf430928e","region2Id":"4ab6ca2f-7952-4e8e-a94d-b6dd933e5d44","region3Id":null,"region4Id":null,"region5Id":null,"region6Id":null,"region7Id":null,"region8Id":null,"region9Id":null,"region10Id":null},"regionSummaryLevel":6}' >> /Users/jihanmaisaroh/scrap_fasih/fast_results.json
  echo "," >> /Users/jihanmaisaroh/scrap_fasih/fast_results.json
done
echo "]" >> /Users/jihanmaisaroh/scrap_fasih/fast_results.json

# Parse with python
python3 -c "
import json
import csv

with open('/Users/jihanmaisaroh/scrap_fasih/fast_results.json') as f:
    raw = f.read()
    raw = raw.replace('},\n]', '}]') # Fix trailing comma
    
try:
    data_list = json.loads(raw)
except Exception as e:
    print('Failed to parse JSON:', e)
    import sys
    sys.exit(1)
    
all_results = []
for d in data_list:
    if isinstance(d, dict) and 'data' in d and 'content' in d['data']:
        all_results.extend(d['data']['content'])

csv_file = '/Users/jihanmaisaroh/scrap_fasih/fast_petugas_palu.csv'
with open(csv_file, mode='w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Email', 'Role', 'Region Code', 'Total Target', 'OPEN', 'DRAFT', 'SUBMITTED BY Pencacah', 'APPROVED BY Pengawas', 'REJECTED BY Pengawas'])
    for row in all_results:
        email = row.get('email', '')
        role = 'Pencacah' if row.get('isPencacah') else 'Pengawas'
        for r_sum in row.get('regionSummary', []):
            counts = {'OPEN': 0, 'DRAFT': 0, 'SUBMITTED BY Pencacah': 0, 'APPROVED BY Pengawas': 0, 'REJECTED BY Pengawas': 0}
            for st in r_sum.get('statusBreakdown', []):
                counts[st.get('status', '')] = st.get('count', 0)
            writer.writerow([email, role, r_sum.get('regionCode', ''), r_sum.get('total', 0), counts.get('OPEN',0), counts.get('DRAFT',0), counts.get('SUBMITTED BY Pencacah',0), counts.get('APPROVED BY Pengawas',0), counts.get('REJECTED BY Pengawas',0)])
print('SUCCESS! Check', csv_file)
"
