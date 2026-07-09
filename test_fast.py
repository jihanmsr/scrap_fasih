import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        # Hubungkan SAJA melalui remote CDP, jangan pernah launch context baru.
        browser = None
        for port in [9222, 9223, 9224]:
            try:
                print(f"Mencoba port {port}...")
                browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
                print(f"[INFO] Terhubung ke browser di port {port}")
                break
            except Exception as e:
                pass
                
        if not browser:
            print("[ERROR] Chrome tidak terdeteksi via CDP. Anda harus menjalankan Chrome dengan --remote-debugging-port=9222!")
            return

        context = browser.contexts[0] if browser.contexts else await browser.new_context()

        # Pastikan ada tab fasih
        page = None
        for p_tab in context.pages:
            if "fasih-sm.bps.go.id" in p_tab.url:
                page = p_tab
                break
                
        if not page:
            page = context.pages[0] if context.pages else await context.new_page()
            await page.goto("https://fasih-sm.bps.go.id/app/dashboard", timeout=60000, wait_until="domcontentloaded")
            await asyncio.sleep(3)
        
        cookies = await context.cookies()
        token = ""
        for c in cookies:
            if c["name"] == "XSRF-TOKEN":
                from urllib.parse import unquote
                token = unquote(c["value"])
                break
                
        payload = {
            "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24",
            "surveyRoleId": "93bcf446-c4c1-4462-8ed0-4b0f7ae89e52",
            "size": 10,
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
        
        res = await page.evaluate("""
            async ({payload, token}) => {
                try {
                    const r = await fetch('https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/report-progress-by-responsibility', {
                        method: 'POST',
                        headers: { 
                            'Content-Type': 'application/json', 
                            'X-XSRF-TOKEN': token
                        },
                        body: JSON.stringify(payload)
                    });
                    if (!r.ok) {
                        return { _error: await r.text(), status: r.status };
                    }
                    return await r.json();
                } catch (e) {
                    return { _error: e.toString() };
                }
            }
        """, {"payload": payload, "token": token})
        
        print("Result:", res)

asyncio.run(run())
