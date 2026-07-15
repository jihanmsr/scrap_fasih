with open("scrape_dashboard_via_cdp.py", "r") as f:
    content = f.read()

import re

old_block = """            # Register the bypassed listener if not registered yet
            await page.evaluate(\"\"\"
                () => {
                    if (window.hasBypassBatchListener) return;
                    window.hasBypassBatchListener = true;
                    
                    window.addEventListener('run-sync-batch-bypass', async (e) => {
                        const { url, payloads, token } = e.detail;
                        const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
                        const results = [];
                        
                        for (const payload of payloads) {
                            try {
                                const r = await fetch(url, {
                                    method: "POST",
                                    headers: {
                                        "Content-Type": "application/json",
                                        "x-xsrf-token": token
                                    },
                                    body: JSON.stringify(payload)
                                });
                                if (!r.ok) {
                                    results.push({ error: `HTTP ${r.status}` });
                                } else {
                                    const data = await r.json();
                                    results.push(data);
                                }
                            } catch (err) {
                                results.push({ error: err.toString() });
                            }
                            await delay(300);
                        }
                        
                        window.dispatchEvent(new CustomEvent('run-sync-batch-bypass-result', {
                            detail: results
                        }));
                    });
                }
            \"\"\")
            
            # Start listening for the result promise
            result_promise = page.evaluate(\"\"\"
                () => new Promise((resolve) => {
                    window.addEventListener('run-sync-batch-bypass-result', (e) => {
                        resolve(e.detail);
                    }, { once: true });
                })
            \"\"\")
            
            # Trigger the batch via event dispatch
            await page.evaluate(\"\"\"
                ({url, payloads, token}) => {
                    window.dispatchEvent(new CustomEvent('run-sync-batch-bypass', {
                        detail: { url, payloads, token }
                    }));
                }
            \"\"\", {"url": url, "payloads": payloads, "token": token})
            
            results = await result_promise"""

new_block = """            import httpx
            
            cookie_dict = {c["name"]: c["value"] for c in cookies}
            results = []
            
            async with httpx.AsyncClient(cookies=cookie_dict, timeout=httpx.Timeout(60.0)) as client:
                for payload in payloads:
                    try:
                        r = await client.post(
                            url,
                            json=payload,
                            headers={"x-xsrf-token": token}
                        )
                        if r.status_code != 200:
                            results.append({"error": f"HTTP {r.status_code} - {r.text[:100]}"})
                        else:
                            try:
                                data = r.json()
                                results.append(data)
                            except Exception as e:
                                results.append({"error": f"JSON Decode Error: {e}"})
                    except Exception as err:
                        results.append({"error": str(err)})
                        
                    await asyncio.sleep(0.5)"""

if old_block in content:
    content = content.replace(old_block, new_block)
    with open("scrape_dashboard_via_cdp.py", "w") as f:
        f.write(content)
    print("Replace success!")
else:
    print("Old block not found!")
