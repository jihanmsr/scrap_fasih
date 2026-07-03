import asyncio
import os
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        user_data_dir = os.path.abspath("playwright_chrome_profile_w2")
        chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        
        try:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=True,
                executable_path=chrome_path,
                ignore_default_args=["--enable-automation"],
                args=["--no-first-run", "--no-default-browser-check", "--disable-blink-features=AutomationControlled"]
            )
        except Exception as e:
            print(f"[ERROR] Gagal meluncurkan Chrome: {e}")
            return
            
        page = context.pages[0] if context.pages else await context.new_page()
        
        # Target ID
        tid = "3208777a-d127-4787-b9ca-edbdaf5dddc1"
        url = f"https://fasih-sm.bps.go.id/app/assignment/fd68e454-ba45-4b85-8205-f3bf777ded24/{tid}"
        print(f"Navigating to {url}...")
        
        await page.goto(url, wait_until="domcontentloaded")
        await asyncio.sleep(6) # Tunggu rendering selesai
        
        print("\n=== Listing all buttons on the page ===")
        buttons = await page.locator("button").all()
        for idx, btn in enumerate(buttons):
            try:
                text = await btn.inner_text()
                html = await btn.evaluate("el => el.outerHTML")
                print(f"Button {idx}: Text='{text.strip()}' | HTML={html[:200]}")
            except Exception as e:
                pass
                
        print("\n=== Listing all links (a tags) on the page ===")
        links = await page.locator("a").all()
        for idx, link in enumerate(links):
            try:
                text = await link.inner_text()
                href = await link.get_attribute("href")
                print(f"Link {idx}: Text='{text.strip()}' | Href='{href}'")
            except Exception as e:
                pass
                
        print("\n=== Listing all elements containing 'Review' ===")
        review_elements = await page.locator("*:has-text('Review')").all()
        for idx, el in enumerate(review_elements[:15]):
            try:
                tag = await el.evaluate("el => el.tagName")
                text = await el.inner_text()
                print(f"Element {idx}: Tag={tag} | Text={text.strip()[:100]}")
            except Exception as e:
                pass
                
        await context.close()

if __name__ == "__main__":
    asyncio.run(main())
