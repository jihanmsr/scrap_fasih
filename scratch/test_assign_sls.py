import asyncio
from playwright.async_api import async_playwright
import json

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()

        payload = {
            "level": "sls",
            "provinsi": "72"
        }

        # Inject fetch call into the page
        js_code = """
        async (payload) => {
            const url = 'https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/report-progress-assignment';
            try {
                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'Accept': '*/*',
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });
                return await response.json();
            } catch (e) {
                return {error: e.toString()};
            }
        }
        """

        result = await page.evaluate(js_code, payload)
        print(json.dumps(result, indent=2)[:1000])

if __name__ == "__main__":
    asyncio.run(main())
