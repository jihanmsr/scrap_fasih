import asyncio
import json
import os
from playwright.async_api import async_playwright
from urllib.parse import unquote

async def main():
    async with async_playwright() as p:
        user_data_dir = os.path.abspath("playwright_chrome_profile_w2")
        print(f"Launching Chrome with profile: {user_data_dir}")
        
        # Launch persistent context
        chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        context = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            executable_path=chrome_path,
            ignore_default_args=["--enable-automation"],
            args=["--no-first-run", "--no-default-browser-check", "--disable-blink-features=AutomationControlled"]
        )
        
        page = context.pages[0] if context.pages else await context.new_page()
        print("Navigating to dashboard to load session...")
        await page.goto("https://fasih-sm.bps.go.id/app/dashboard", wait_until="domcontentloaded")
        await asyncio.sleep(2)
        
        cookies = await context.cookies()
        xsrf_token_raw = next((c["value"] for c in cookies if c["name"] == "XSRF-TOKEN"), "")
        xsrf_token = unquote(xsrf_token_raw)
        print(f"XSRF-TOKEN: {xsrf_token}")
        
        endpoints = [
            "/app/api/survey-response/v2/api-docs",
            "/app/api/analytic/v2/api-docs",
            "/app/api/survey-user/v2/api-docs",
            "/app/api/assignment-general/v2/api-docs"
        ]
        
        results = {}
        for ep in endpoints:
            url = "https://fasih-sm.bps.go.id" + ep
            print(f"Fetching Swagger docs from: {url}")
            try:
                res = await page.evaluate("""
                    async ({url, token}) => {
                        const r = await fetch(url, {
                            headers: { "X-XSRF-TOKEN": token }
                        });
                        if (!r.ok) return { error: `HTTP ${r.status}` };
                        return await r.json();
                    }
                """, {"url": url, "token": xsrf_token})
                
                if "paths" in res:
                    results[ep] = res["paths"]
                    print(f" ✅ Success fetching Swagger from {ep}")
                else:
                    print(f" ❌ Failed or no paths in response from {ep}: {res}")
            except Exception as e:
                print(f" ❌ Exception fetching {ep}: {e}")
                
        # Parse and print interesting paths
        interesting_words = ["verify", "approve", "reject", "status", "submit", "remarks", "comment", "review", "log", "history", "response"]
        found_paths = []
        for ep, paths in results.items():
            for path, methods in paths.items():
                if any(w in path.lower() for w in interesting_words):
                    found_paths.append({
                        "ep": ep,
                        "path": path,
                        "methods": list(methods.keys()),
                        "details": methods
                    })
                    
        print(f"\nFound {len(found_paths)} interesting paths:")
        for fp in found_paths:
            print(f"- [{fp['ep']}] {fp['path']} ({', '.join(fp['methods']).upper()})")
            # print description or summary of the method if available
            for method, details in fp["details"].items():
                print(f"  {method.upper()}: {details.get('summary', '') or details.get('description', '')}")
                
        # Save results to scratch
        with open("scratch/swagger_interesting_paths.json", "w") as f:
            json.dump(found_paths, f, indent=2)
        print("\nSaved interesting paths to scratch/swagger_interesting_paths.json")
        
        await context.close()

if __name__ == "__main__":
    asyncio.run(main())
