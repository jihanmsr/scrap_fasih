import asyncio
import httpx
from playwright.async_api import async_playwright

async def get_token_cookies(p):
    browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9223")
    context = browser.contexts[0]
    cookies = await context.cookies()
    token = ""
    for c in cookies:
        if c['name'] == 'XSRF-TOKEN':
            from urllib.parse import unquote
            token = unquote(c['value'])
            break
    return token, cookies

async def main():
    async with async_playwright() as p:
        try:
            token, cookies = await get_token_cookies(p)
        except Exception as e:
            print(f"Could not connect to browser: {e}")
            return
        
        assignment_id = "fb8a92db-3ef2-4f3d-a519-53e34b9cfc01" # dummy id, we can try to find a rejected one
        # Let's search for a rejected id in granular_assignments.json
        import json, gzip, base64
        try:
            with open("granular_assignments.json") as f:
                d = json.load(f)
                b = base64.b64decode(d["compressed_data"])
                decomp = json.loads(gzip.decompress(b).decode('utf-8'))
                statuses = decomp["statuses"]
                rejected_idx = [i for i, s in enumerate(statuses) if "REJECTED" in s.upper()]
                if not rejected_idx:
                    print("No rejected status found")
                    return
                for target in decomp["targets"]:
                    if target[3] in rejected_idx:
                        assignment_id = target[0]
                        print(f"Found rejected target: {assignment_id}")
                        break
        except Exception as e:
            print(f"Error reading local data: {e}")
            
        url = f"https://fasih-sm.bps.go.id/app/api/survey-response/api/v1/remarks?assignmentId={assignment_id}"
        
        async with httpx.AsyncClient() as client:
            client.headers.update({"X-XSRF-TOKEN": token})
            for c in cookies:
                client.cookies.set(c['name'], c['value'])
            res = await client.get(url)
            print(res.status_code)
            print(res.text)

asyncio.run(main())
