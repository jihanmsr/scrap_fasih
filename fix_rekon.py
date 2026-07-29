import re
import json

# 1. Convert JSON to JS
try:
    with open('rekon_sls.json', 'r') as f:
        sls_data = f.read()
    with open('rekon_petugas.json', 'r') as f:
        petugas_data = f.read()
        
    js_content = f"window.rekonSlsData = {sls_data};\nwindow.rekonPetugasData = {petugas_data};\n"
    with open('rekon_data.js', 'w') as f:
        f.write(js_content)
except Exception as e:
    print(f"Error converting JSON to JS: {e}")

# 2. Patch index.html to load rekon_data.js
with open('index.html', 'r') as f:
    html = f.read()
if '<script src="rekon_data.js"></script>' not in html:
    html = html.replace('<script src="rekon.js"></script>', '<script src="rekon_data.js"></script>\n    <script src="rekon.js"></script>')
with open('index.html', 'w') as f:
    f.write(html)

# 3. Patch app.js header for 'rekon'
with open('app.js', 'r') as f:
    app_js = f.read()

rekon_header_logic = """
        } else if (tabId === 'rekon') {
            if (mainHeader) mainHeader.textContent = 'Rekap Lintas Sistem';
            if (mainSubheader) mainSubheader.textContent = 'Perbandingan muatan SLS vs alokasi Fasih vs SQL Lab';
            if (btnDownloadXlsx) btnDownloadXlsx.style.display = 'none';
            if (btnDownloadBackupCsv) btnDownloadBackupCsv.style.display = 'none';
"""
if "tabId === 'rekon'" not in app_js:
    app_js = app_js.replace("} else if (tabId === 'anomali') {", rekon_header_logic + "        } else if (tabId === 'anomali') {")
    with open('app.js', 'w') as f:
        f.write(app_js)

