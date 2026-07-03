import asyncio
import os
from playwright.async_api import async_playwright

async def check_profile(p, profile_name):
    user_data_dir = os.path.abspath(profile_name)
    if not os.path.isdir(user_data_dir):
        return None
    
    print(f"Checking profile: {profile_name}...")
    chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    try:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=True,
            executable_path=chrome_path,
            ignore_default_args=["--enable-automation"],
            args=["--no-first-run", "--no-default-browser-check", "--disable-blink-features=AutomationControlled"]
        )
        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto("https://fasih-sm.bps.go.id/app/dashboard", wait_until="domcontentloaded", timeout=15000)
        await asyncio.sleep(2)
        
        url = page.url
        cookies = await context.cookies()
        xsrf = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), None)
        
        await context.close()
        
        if "login" in url:
            return "Not logged in (redirected to login)"
        elif xsrf:
            return f"Logged in! (XSRF: {xsrf[:10]}... URL: {url})"
        else:
            return f"Unknown state (URL: {url})"
    except Exception as e:
        return f"Error: {e}"

async def main():
    profiles = [
        "playwright_chrome_profile",
        "playwright_chrome_profile_email",
        "playwright_chrome_profile_fast",
        "playwright_chrome_profile_w0",
        "playwright_chrome_profile_w1",
        "playwright_chrome_profile_w2",
        "playwright_chrome_profile_w3",
        "chrome_user_data"
    ]
    
    async with async_playwright() as p:
        for prof in profiles:
            res = await check_profile(p, prof)
            if res:
                print(f" => {prof}: {res}\n")

if __name__ == "__main__":
    asyncio.run(main())
