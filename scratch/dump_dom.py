import asyncio
import os
from playwright.async_api import async_playwright
import socket

def check_port_open(port=9222):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('127.0.0.1', port)) == 0
    except:
        return False

async def main():
    async with async_playwright() as p:
        if not check_port_open(9222):
            print("Port 9222 is closed")
            return
            
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0] if browser.contexts else await browser.new_context()
        
        target_page = None
        for page in context.pages:
            if "fasih-sm" in page.url:
                target_page = page
                break
                
        if not target_page:
            target_page = context.pages[0] if context.pages else await context.new_page()
            
        print(f"Connected to page: {target_page.url}")
        
        # Save DOM
        html = await target_page.content()
        with open("scratch/dashboard_dom.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("DOM saved to scratch/dashboard_dom.html")
        
        # Save screenshot
        await target_page.screenshot(path="scratch/active_dashboard_screenshot.png")
        print("Screenshot saved to scratch/active_dashboard_screenshot.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
