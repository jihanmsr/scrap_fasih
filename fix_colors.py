import re

with open('index.html', 'r') as f:
    content = f.read()

# Replace all --stat-color with text-secondary (a neutral gray)
content = re.sub(r'--stat-color:\s*[^;]+;', '--stat-color: var(--text-secondary);', content)

# Remove or replace inline colors on stat-value
content = re.sub(r'class="stat-value" id="([^"]+)" style="color:\s*[^"]+"', r'class="stat-value" id="\1"', content)

with open('index.html', 'w') as f:
    f.write(content)
