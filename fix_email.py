with open("scrape_via_api.py", "r") as f:
    content = f.read()

old_post_block = """                        res = http_session.post(email_datatable_url, json=email_payload, timeout=30)"""
new_post_block = """                        import json
                        payload_str = json.dumps(email_payload, separators=(',', ':'))
                        res = http_session.post(email_datatable_url, data=payload_str, timeout=30)"""

if old_post_block in content:
    content = content.replace(old_post_block, new_post_block)
    with open("scrape_via_api.py", "w") as f:
        f.write(content)
    print("Replace email success!")
else:
    print("Email block not found!")
