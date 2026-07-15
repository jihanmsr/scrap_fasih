with open("scrape_dashboard_via_cdp.py", "r") as f:
    content = f.read()

old_block = """            async with httpx.AsyncClient(cookies=cookie_dict, timeout=httpx.Timeout(60.0)) as client:
                for payload in payloads:
                    retries = 0
                    max_retries = 10
                    kab_data = None
                    while retries < max_retries:
                        try:
                            r = await client.post(
                                url,
                                json=payload,
                                headers={"x-xsrf-token": token}
                            )"""

new_block = """            import json
            headers = {
                "Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.9,id-ID;q=0.8,id;q=0.7",
                "Content-Type": "application/json",
                "Origin": "https://fasih-sm.bps.go.id",
                "Priority": "u=1, i",
                "Referer": "https://fasih-sm.bps.go.id/app/surveys/a0429e96-51a5-477b-a415-485f9c153004/fd68e454-ba45-4b85-8205-f3bf777ded24",
                "Sec-Ch-Ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"macOS"',
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
                "X-Requested-With": "XMLHttpRequest",
                "x-xsrf-token": token
            }
            async with httpx.AsyncClient(cookies=cookie_dict, timeout=httpx.Timeout(60.0)) as client:
                for payload in payloads:
                    retries = 0
                    max_retries = 10
                    kab_data = None
                    while retries < max_retries:
                        try:
                            headers["x-xsrf-token"] = token
                            payload_str = json.dumps(payload, separators=(',', ':'))
                            r = await client.post(
                                url,
                                content=payload_str,
                                headers=headers
                            )"""

if old_block in content:
    content = content.replace(old_block, new_block)
    with open("scrape_dashboard_via_cdp.py", "w") as f:
        f.write(content)
    print("Replace success!")
else:
    print("Old block not found!")
