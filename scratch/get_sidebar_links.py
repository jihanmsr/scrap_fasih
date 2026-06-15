import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        for port in [9222, 9223]:
            try:
                browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
                print(f"\n--- Connected on port {port} ---")
                context = browser.contexts[0]
                for idx, p_page in enumerate(context.pages):
                    print(f"  Page {idx}: URL={p_page.url} Title={await p_page.title()}")
                    
                    if "survey-collection" in p_page.url:
                        print("    Found survey-collection page!")
                        sidebar_links = await p_page.evaluate("""() => {
                            const links = Array.from(document.querySelectorAll('a'));
                            return links.map(a => ({ text: a.innerText.trim(), href: a.href }));
                        }""")
                        print("    Links:")
                        for link in sidebar_links:
                            if link['text'] or link['href']:
                                print(f"      Text: {link['text']} | Href: {link['href']}")
                await browser.close()
            except Exception as e:
                print(f"Failed to connect on port {port}: {e}")

asyncio.run(run())
