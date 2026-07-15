with open("scrape_via_api.py", "r") as f:
    content = f.read()

old_session = "    session = requests.Session()"
new_session = "    import httpx\n    session = httpx.Client(http2=True, verify=False)"

if old_session in content:
    content = content.replace(old_session, new_session)
    with open("scrape_via_api.py", "w") as f:
        f.write(content)
    print("Replaced requests.Session with httpx.Client")
else:
    print("requests.Session not found")
