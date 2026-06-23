#!/bin/bash
echo "=== Menutup sisa-sisa Chrome Scraper ==="
pkill -f "remote-debugging-port=9222"
pkill -f "remote-debugging-port=9223"
pkill -f "playwright_chrome_profile"
pkill -f "main_scraper.py"
pkill -f "scrape_granular_core.py"
rm -f "/Users/jihanmaisaroh/scrap_fasih/playwright_chrome_profile/SingletonLock"
sleep 2

echo "=== Mulai Penarikan Data Penuh (Unified Scraper) ==="
python3 main_scraper.py
