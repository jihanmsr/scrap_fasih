with open("scrape_dashboard_via_cdp.py", "r") as f:
    content = f.read()

old_block = """            import httpx
            
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

new_block = """            import httpx
            
            cookie_dict = {c["name"]: c["value"] for c in cookies}
            results = []
            
            async with httpx.AsyncClient(cookies=cookie_dict, timeout=httpx.Timeout(60.0)) as client:
                for payload in payloads:
                    retries = 0
                    max_retries = 10
                    kab_data = None
                    while retries < max_retries:
                        try:
                            r = await client.post(
                                url,
                                json=payload,
                                headers={"x-xsrf-token": token}
                            )
                            if r.status_code != 200:
                                raise Exception(f"HTTP {r.status_code} - {r.text[:50]}")
                            
                            kab_data = r.json()
                            break # Success!
                        except Exception as e:
                            retries += 1
                            print(f"  [ERROR] Gagal ambil data kabupaten (Percobaan {retries}/{max_retries}): {e}")
                            print("  [INFO] Terdeteksi blokir F5 WAF. Memuat ulang cookie...")
                            try:
                                await page.reload(wait_until="networkidle")
                                new_cookies = await page.context.cookies()
                                cookie_dict = {c["name"]: c["value"] for c in new_cookies}
                                client.cookies.update(cookie_dict)
                                for c in new_cookies:
                                    if c["name"] == "XSRF-TOKEN":
                                        from urllib.parse import unquote
                                        token = unquote(c["value"])
                                        break
                                print("  [INFO] Token baru berhasil didapatkan!")
                            except Exception as refr_e:
                                print(f"  [ERROR] Gagal refresh: {refr_e}")
                            await asyncio.sleep(5)
                            
                    if kab_data:
                        results.append(kab_data)
                    else:
                        results.append({"error": "Gagal total setelah retries."})"""

if old_block in content:
    content = content.replace(old_block, new_block)
    with open("scrape_dashboard_via_cdp.py", "w") as f:
        f.write(content)
    print("Replace success!")
else:
    print("Old block not found!")
