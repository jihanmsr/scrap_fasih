import requests
import json
import csv

url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/report-progress-by-responsibility"

headers = {
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9,id-ID;q=0.8,id;q=0.7",
    "content-type": "application/json",
    "cookie": "XSRF-TOKEN=c406ff8c-a60b-4c5f-90fa-998f55393663; SESSION=bcc86f50-4d70-4ee2-9549-56b09659236e;",
    "origin": "https://fasih-sm.bps.go.id",
    "priority": "u=1, i",
    "sec-ch-ua": "\"Google Chrome\";v=\"149\", \"Chromium\";v=\"149\", \"Not)A;Brand\";v=\"24\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"macOS\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
    "x-xsrf-token": "c406ff8c-a60b-4c5f-90fa-998f55393663"
}

payload_template = {
    "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24",
    "surveyRoleId": "93bcf446-c4c1-4462-8ed0-4b0f7ae89e52",
    "size": 100,
    "page": 0,
    "search": "",
    "target": "TARGET_ONLY",
    "region": {
        "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e",
        "region2Id": "4ab6ca2f-7952-4e8e-a94d-b6dd933e5d44",
        "region3Id": None,
        "region4Id": None,
        "region5Id": None,
        "region6Id": None,
        "region7Id": None,
        "region8Id": None,
        "region9Id": None,
        "region10Id": None
    },
    "regionSummaryLevel": 6
}

all_data = []
page = 0
while True:
    print(f"Fetching page {page}...")
    payload = payload_template.copy()
    payload["page"] = page
    
    # We must use verify=False because of BPS SSL issue, just to be safe
    response = requests.post(url, headers=headers, json=payload, verify=False)
    if response.status_code != 200:
        print("Error:", response.status_code, response.text)
        break
        
    data = response.json()
    content = data.get("data", {}).get("content", [])
    if not content:
        break
        
    all_data.extend(content)
    page += 1

# Save to CSV
csv_file = "/Users/jihanmaisaroh/scrap_fasih/fast_petugas_palu.csv"
with open(csv_file, mode='w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    # Tulis header
    writer.writerow(["Email", "Role", "Region Code", "Total Target", "OPEN", "DRAFT", "SUBMITTED BY Pencacah", "APPROVED BY Pengawas", "REJECTED BY Pengawas"])
    
    for row in all_data:
        email = row.get("email", "")
        role = "Pencacah" if row.get("isPencacah") else "Pengawas"
        region_summaries = row.get("regionSummary", [])
        
        for r_sum in region_summaries:
            reg_code = r_sum.get("regionCode", "")
            status_breakdown = r_sum.get("statusBreakdown", [])
            
            counts = {"OPEN": 0, "DRAFT": 0, "SUBMITTED BY Pencacah": 0, "APPROVED BY Pengawas": 0, "REJECTED BY Pengawas": 0}
            total = r_sum.get("total", 0)
            
            for st in status_breakdown:
                s_name = st.get("status", "")
                s_count = st.get("count", 0)
                counts[s_name] = s_count
                
            writer.writerow([email, role, reg_code, total, counts.get("OPEN",0), counts.get("DRAFT",0), counts.get("SUBMITTED BY Pencacah",0), counts.get("APPROVED BY Pengawas",0), counts.get("REJECTED BY Pengawas",0)])

print(f"Selesai! Tersimpan di {csv_file}")
