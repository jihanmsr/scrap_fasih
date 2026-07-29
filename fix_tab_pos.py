import re

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Remove the tab-content-rekon from the end of the file
pattern = r'<!-- TAB REKONSILIASI -->\s*<div class="tab-content" id="tab-content-rekon".*?</div>\n    </div>\n'
html_cleaned = re.sub(pattern, '', html, flags=re.DOTALL)
# Try removing it more generally if the above didn't work perfectly
pattern2 = r'<!-- TAB REKONSILIASI -->.*?</div>\s*</div>\s*</div>'
if '<!-- TAB REKONSILIASI -->' in html_cleaned:
    html_cleaned = re.sub(pattern2, '', html_cleaned, flags=re.DOTALL)

# Let's just extract the tab content block if it's there
tab_match = re.search(r'<!-- TAB REKONSILIASI -->.*?(?=</body>)', html, flags=re.DOTALL)
if tab_match:
    tab_html = tab_match.group(0)
    # Remove it from the end
    html = html.replace(tab_html, '')
    
    # Find where tab-content-anomali ends
    # We will just insert it right BEFORE the closing </main> tag (line 2489 usually)
    # But wait, there are multiple </main>? Let's find the first one.
    html = html.replace('</main>', tab_html + '\n        </main>', 1)
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html)
        print("Fixed tab placement!")
else:
    print("Could not find tab block at the end.")

