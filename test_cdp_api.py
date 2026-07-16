import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9223")
        context = browser.contexts[0]
        page = context.pages[0]
        
        req = await page.evaluate("""async () => {
            const xsrf = document.cookie.split('; ').find(row => row.startsWith('XSRF-TOKEN=')).split('=')[1];
            const resp = await fetch('https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/report-user-assignment', {
                method: 'POST',
                headers: {
                    'Accept': '*/*',
                    'Content-Type': 'application/json',
                    'x-xsrf-token': decodeURIComponent(xsrf)
                },
                body: JSON.stringify({"surveyPeriodId":"ecddb52e-f392-403c-a963-47391f217010","assignmentStatusAlias":null,"assignmentErrorStatusType":-1,"data1":null,"data2":null,"data3":null,"data4":null,"data5":null,"data6":null,"data7":null,"data8":null,"data9":null,"data10":null,"regionId":null,"region1Id":"a00c8aef-afc4-4d4f-b80d-789a15450ef9","region2Id":"9c9b2d79-9fb1-4ce7-b0f1-6b7bb5511beb","currentUserId":null,"userIdResponsibility":null})
            });
            return await resp.text();
        }""")
        print("Response:", req[:1000])

asyncio.run(run())
