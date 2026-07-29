import re

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Extract tab-content-rekon
match = re.search(r'<!-- TAB REKONSILIASI -->\s*<div class="tab-content" id="tab-content-rekon".*?</div>\s*</div>\s*</div>', html, flags=re.DOTALL)
if match:
    rekon_content = match.group(0)
    # Remove it from current location
    html = html.replace(rekon_content, '')
    
    # Insert it right before </main>
    html = html.replace('</main>', rekon_content + '\n        </main>')
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html)
        print("Tab rekon moved successfully.")
else:
    print("Could not find tab-content-rekon with regex. Let's try string split.")
    
