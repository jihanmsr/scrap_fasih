import asyncio
import json
import os
import sys
from playwright.async_api import async_playwright

async def main():
    print("[START] Script check_columns started", flush=True)
    async with async_playwright() as p:
        # Connect to Chrome remote debugging port 9222 or 9223
        browser = None
        for port in [9223, 9222]:
            try:
                print(f"[TRY] Connecting to port {port}...", flush=True)
                browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
                print(f"[SUCCESS] Connected to port {port}", flush=True)
                break
            except Exception as e:
                print(f"[FAIL] Could not connect to port {port}: {e}", flush=True)
        
        if not browser:
            print("[ERROR] Could not connect to Chrome on port 9222 or 9223. Please ensure Chrome is running with remote debugging.", flush=True)
            return

        try:
            context = browser.contexts[0]
            
            # Use Playwright's built-in Request API which has cookies and bypasses CORS
            print("[INFO] Fetching dataset metadata using context.request.get...", flush=True)
            url = 'https://fasih-dashboard.bps.go.id/api/v1/dataset/7047'
            response = await context.request.get(url)
            
            print(f"[INFO] Response status: {response.status}", flush=True)
            if response.status == 200:
                result = await response.json()
                print("Dataset Metadata Keys:", list(result.keys()), flush=True)
                if "result" in result:
                    columns = result["result"].get("columns", [])
                    print(f"[SUCCESS] Found {len(columns)} columns:", flush=True)
                    for col in columns:
                        print(f" - Name: {col.get('column_name')}, Type: {col.get('type')}, Expression: {col.get('expression')}", flush=True)
                else:
                    print("[ERROR] Result field missing in response json", flush=True)
            else:
                text = await response.text()
                print(f"[ERROR] Failed to fetch: {response.status} - {text[:200]}", flush=True)

        except Exception as ex:
            print(f"[EXCEPTION] Error during Request API execution: {ex}", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
