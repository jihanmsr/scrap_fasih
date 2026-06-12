from playwright.sync_api import sync_playwright
import time
import subprocess
import os

# Start HTTP server
server = subprocess.Popen(["python3", "-m", "http.server", "8008"])
time.sleep(2)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1400, "height": 900})
    page.goto("http://localhost:8008/index.html")
    time.sleep(3)
    
    # Wait for the data to load
    page.wait_for_selector(".compact-stats", timeout=10000)
    
    # Screenshot Light
    page.screenshot(path="screenshot_ui_light.png", full_page=True)
    
    # Toggle details
    page.click("#se_umum-toggle-detail")
    time.sleep(1)
    page.screenshot(path="screenshot_ui_expanded.png")

    # Go to Assign Tab
    page.click("#tab-btn-assign")
    time.sleep(1)
    page.screenshot(path="screenshot_assign_sync.png")
    
    browser.close()

# Kill server
server.terminate()
