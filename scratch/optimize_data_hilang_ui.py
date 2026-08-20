import re

with open('/Users/jihanmaisaroh/scrap_fasih/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Update title and description in the UI
# The user wants dynamic title depending on the tab, but for now we can update the static header in HTML.
# But wait, the header is defined in index.html in the <main> section somewhere?
# No, the screenshot shows "Pemantauan Data Hilang". That's probably in the <h2> of the section.
