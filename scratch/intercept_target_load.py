import asyncio
import os
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        user_data_dir = os.path.abspath("playwright_chrome_profile_w2")
        chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        
        context = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=True,
            executable_path=chrome_path,
            ignore_default_args=["--enable-automation"],
            args=["--no-first-run", "--no-default-browser-check", "--disable-blink-features=AutomationControlled"]
        )
        
        page = context.pages[0] if context.pages else await context.new_page()
        
        # Target 12 (Berhasil - BALTHASAR BOUK)
        # ID: e1682c11-9c77-4f92-8550-38d0dccad36f
        # Target 13 (Gagal - ... )
        # ID: 007a6993-1fbe-47b6-8df8-9ac53e184017
        
        async def intercept_response(response):
            # Cek jika URL merupakan request API ke fasih
            if "api" in response.url or "assignment" in response.url:
                try:
                    text = await response.text()
                    print(f"\n[API RESPONSE] URL: {response.url}")
                    print(f"Status: {response.status}")
                    print(f"Content (first 1000 chars): {text[:1000]}")
                except Exception as e:
                    pass

        page.on("response", intercept_response)

        # 1. Load Target 12 (Berhasil)
        target_success = "e1682c11-9c77-4f92-8550-38d0dccad36f"
        print(f"\n================ Loading TARGET SUCCESS (ID: {target_success}) ================")
        url_success = f"https://fasih-sm.bps.go.id/app/assignment/fd68e454-ba45-4b85-8205-f3bf777ded24/{target_success}"
        await page.goto(url_success, wait_until="domcontentloaded")
        await asyncio.sleep(5)

        # 2. Load Target 13 (Gagal)
        target_fail = "007a6993-1fbe-47b6-8df8-9ac53e184017"
        print(f"\n================ Loading TARGET FAIL (ID: {target_fail}) ================")
        url_fail = f"https://fasih-sm.bps.go.id/app/assignment/fd68e454-ba45-4b85-8205-f3bf777ded24/{target_fail}"
        await page.goto(url_fail, wait_until="domcontentloaded")
        await asyncio.sleep(5)

        await context.close()

if __name__ == "__main__":
    asyncio.run(main())
