from playwright.sync_api import sync_playwright
import os

html_path = f"file://{os.path.abspath('index.html')}"

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(html_path)
    page.wait_for_timeout(2000)
    
    # Evaluate window.IPAS_DATA
    res = page.evaluate("() => { return window.IPAS_DATA ? window.IPAS_DATA.se_umum.length : -1; }")
    print("se_umum length:", res)
    
    # Check text content of the target card
    text = page.locator('#se_umum-stat-total-prelist').text_content()
    print("Total target:", text)
    
    browser.close()
