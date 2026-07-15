with open("scrape_via_api.py", "r") as f:
    content = f.read()

content = content.replace("data=payload_str", "content=payload_str")

with open("scrape_via_api.py", "w") as f:
    f.write(content)
print("Replaced data with content")
