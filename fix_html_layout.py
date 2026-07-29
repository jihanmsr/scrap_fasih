import re

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Extract the rekon block
match = re.search(r'(<!-- TAB REKONSILIASI -->.*?)</body>', html, flags=re.DOTALL)
if match:
    rekon_block = match.group(1)
    
    # 2. Remove it from the end
    html = html.replace(rekon_block, '')
    
    # 3. Insert it right before the closing </main>
    # Let's find </main>
    html = html.replace('</main>', rekon_block + '\n        </main>')
    
    # 4. Save
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("Fixed layout!")
else:
    print("Could not find rekon block.")
