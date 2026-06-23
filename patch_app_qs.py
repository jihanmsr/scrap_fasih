with open("app.js", "r", encoding="utf-8") as f:
    code = f.read()

import re

# Fix script.src = 'granular_assignments.js?v=' + Date.now();
# Make it handle file:// protocol
code = code.replace(
    "script.src = 'granular_assignments.js?v=' + Date.now();",
    "script.src = window.location.protocol === 'file:' ? 'granular_assignments.js' : 'granular_assignments.js?v=' + Date.now();"
)

with open("app.js", "w", encoding="utf-8") as f:
    f.write(code)

print("Patched query strings in app.js!")
