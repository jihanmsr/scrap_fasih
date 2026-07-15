with open("scrape_via_api.py", "r") as f:
    content = f.read()

import re

old_headers_block = """    headers = {
        "Content-Type": "application/json",
        "X-XSRF-TOKEN": xsrf_token,
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*"
    }"""

new_headers_block = """    headers = {
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9,id-ID;q=0.8,id;q=0.7",
        "Content-Type": "application/json",
        "Origin": "https://fasih-sm.bps.go.id",
        "Priority": "u=1, i",
        "Referer": "https://fasih-sm.bps.go.id/app/surveys/ecddb52e-f392-403c-a963-47391f217010/37526b20-81c8-42f5-a895-6190137d7394/data",
        "Sec-Ch-Ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"macOS"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "x-xsrf-token": xsrf_token
    }"""

old_post_block = """                            res = http_session.post(datatable_url, json=payload, timeout=60)"""

new_post_block = """                            import json
                            payload_str = json.dumps(payload, separators=(',', ':'))
                            res = http_session.post(datatable_url, data=payload_str, timeout=60)"""

if old_headers_block in content:
    content = content.replace(old_headers_block, new_headers_block)
    content = content.replace(old_post_block, new_post_block)
    with open("scrape_via_api.py", "w") as f:
        f.write(content)
    print("Replace success!")
else:
    print("Headers block not found!")
