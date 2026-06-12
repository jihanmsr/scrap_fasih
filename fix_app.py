import re

with open('app.js', 'r') as f:
    content = f.read()

# Fix the renderSyncTable broken line
content = content.replace("        // Populate global sync\n        updateGlobalSyncProgress();\n    };\n\n    window.refreshAllData = function() {\n        const tbody = document.getElementById('sync-table-body');", 
"        // Populate global sync\n        updateGlobalSyncProgress();\n    };\n\n    window.renderSyncTable = function() {\n        const tbody = document.getElementById('sync-table-body');")

with open('app.js', 'w') as f:
    f.write(content)
