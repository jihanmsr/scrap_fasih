import re

with open('index.html', 'r') as f:
    html = f.read()

# Remove the title case options that are duplicates
duplicate_pattern = re.compile(r'<option value="\[\d{2}\].*?">\[\d{2}\] [A-Z][a-z].*?</option>\s*')
html = re.sub(duplicate_pattern, '', html)

# The pattern captures options like <option value="[01] BANGGAI KEPULAUAN">[01] Banggai Kepulauan</option>
# Wait, let's just make it simpler: remove lines containing '[01] Banggai Kepulauan' etc.
html = re.sub(r'<option value="\[\d{2}\] .*?">\[\d{2}\] (?![A-Z- ]+<)[A-Za-z- ]+</option>\s*', '', html)

with open('index.html', 'w') as f:
    f.write(html)
