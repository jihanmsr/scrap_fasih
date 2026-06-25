"""
Debug: test responsibility API untuk satu kabupaten dengan payload benar.
Jalankan saat Chrome FASIH sudah terbuka.
"""
import asyncio
import json
import sys
from urllib.parse import unquote
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        except Exception as e:
            print(f"[ERROR] Gagal connect ke Chrome: {e}")
            print("Pastikan Chrome dibuka dengan: --remote-debugging-port=9222")
            return

        context = browser.contexts[0]
        page = None
        for pg in context.pages:
            if "fasih-sm.bps.go.id" in pg.url:
                page = pg
                break
        if not page:
            page = await context.new_page()
            await page.goto("https://fasih-sm.bps.go.id/app/dashboard")
            await asyncio.sleep(2)

        cookies = await page.context.cookies()
        token_raw = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), "")
        token = unquote(token_raw) if token_raw else ""
        print(f"[OK] Token: {'ada' if token else 'KOSONG'}")
        print(f"[OK] Page URL: {page.url}")

        url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/report-progress-by-responsibility"

        # Test 1: Bangkep, SE Umum, Pencacah
        payload = {
            "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24",
            "surveyRoleId": "6d7d919a-45e5-4779-bb87-2905b49fd31a",
            "size": 5,
            "page": 0,
            "search": "",
            "target": "TARGET_ONLY",
            "region": {
                "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e",
                "region2Id": "bc32354f-1245-426f-b2cf-a5733e1295ad",  # Bangkep
                "region3Id": None, "region4Id": None, "region5Id": None,
                "region6Id": None, "region7Id": None, "region8Id": None,
                "region9Id": None, "region10Id": None
            },
            "regionSummaryLevel": 6
        }

        print("\n[TEST] POST ke responsibility API (Bangkep, SE Umum, level 6)...")
        resp = await page.evaluate("""
            async ({url, payload, token}) => {
                try {
                    const r = await fetch(url, {
                        method: "POST",
                        headers: { "Content-Type": "application/json", "X-XSRF-TOKEN": token },
                        body: JSON.stringify(payload)
                    });
                    const status = r.status;
                    if (!r.ok) {
                        const text = await r.text();
                        return { _httpError: status, _body: text.substring(0, 300) };
                    }
                    return await r.json();
                } catch(e) {
                    return { _error: e.toString() };
                }
            }
        """, {"url": url, "payload": payload, "token": token})

        print(f"[RESULT] success: {resp.get('success')}, message: {resp.get('message', '-')}")
        print(f"[RESULT] Full top-level keys: {list(resp.keys()) if isinstance(resp, dict) else 'N/A'}")
        if resp.get("_httpError"):
            print(f"[HTTP ERROR] Status: {resp['_httpError']}, Body: {resp.get('_body', '')}")
        elif resp.get("_error"):
            print(f"[FETCH ERROR] {resp['_error']}")
        elif resp.get("success"):
            data = resp.get("data", {})
            print(f"[DATA] keys: {list(data.keys()) if isinstance(data, dict) else type(data)}")
            if isinstance(data, dict):
                print(f"  totalPages: {data.get('totalPages')}")
                print(f"  totalElements: {data.get('totalElements')}")
                content = data.get("content", [])
                print(f"  content len: {len(content)}")
                if content:
                    print(f"  First item keys: {list(content[0].keys())}")
                    print(f"  First item (no regionSummary): ", {k: v for k, v in content[0].items() if k != 'regionSummary'})
                    rs = content[0].get("regionSummary", [])
                    print(f"  regionSummary count: {len(rs)}")
                    if rs:
                        print(f"  regionSummary[0]: {json.dumps(rs[0], indent=2)}")
                else:
                    print("  Content KOSONG tapi success=true!")
        else:
            print(f"[FAIL] {json.dumps(resp, indent=2)[:500]}")

if __name__ == "__main__":
    asyncio.run(main())
