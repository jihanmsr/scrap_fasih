import re

with open('index.html', 'r') as f:
    html = f.read()

# For se_umum: The first kab-filter is around line 892. The second is around line 927.
# They have exactly the same options inside now, because I inserted into both.
# But one of them has "display: none;" originally in the style. I changed it in JS.
# Let's just remove the one that has <!-- Dropdown Filter Kabkot --> above it.

html = re.sub(r'<!-- Dropdown Filter Kabkot -->\s*<select class="sort-select" id="se_umum-kab-filter".*?</select>', '', html, flags=re.DOTALL)
html = re.sub(r'<!-- Dropdown Filter Kabkot -->\s*<select class="sort-select" id="se_ub-kab-filter".*?</select>', '', html, flags=re.DOTALL)

with open('index.html', 'w') as f:
    f.write(html)
