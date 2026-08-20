import re

with open('/Users/jihanmaisaroh/scrap_fasih/app_v2.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Replace the text of switchDataHilangSubTab to also update the header text.
new_switch = """
    window.switchDataHilangSubTab = function(tab) {
        currentDataHilangTab = tab;
        const btnUsaha = document.getElementById('btn-data-hilang-usaha');
        const btnKeluarga = document.getElementById('btn-data-hilang-keluarga');
        const mainHeader = document.getElementById('main-header');
        const mainSubheader = document.getElementById('main-subheader');
        
        if(tab === 'usaha') {
            btnUsaha.style.background = 'var(--primary)';
            btnUsaha.style.color = 'white';
            
            btnKeluarga.style.background = 'transparent';
            btnKeluarga.style.color = 'var(--text-secondary)';
            
            if (mainHeader) mainHeader.textContent = 'Usaha Hilang';
            if (mainSubheader) mainSubheader.textContent = 'Usahanya tidak ditemukan tapi bisa dilacak keluarganya';
        } else {
            btnKeluarga.style.background = 'var(--primary)';
            btnKeluarga.style.color = 'white';
            
            btnUsaha.style.background = 'transparent';
            btnUsaha.style.color = 'var(--text-secondary)';
            
            if (mainHeader) mainHeader.textContent = 'Keluarga Hilang';
            if (mainSubheader) mainSubheader.textContent = 'Keluarganya hilang atau tidak dapat ditemukan pada dokumen Sensus';
        }
        
        window.loadDataHilangData();
    };
"""

# Regex to find the current switchDataHilangSubTab
pattern = re.compile(r'window\.switchDataHilangSubTab = function\(tab\).*?window\.loadDataHilangData\(\);\s*\};', re.DOTALL)
if pattern.search(js):
    js = pattern.sub(new_switch.strip(), js)
    with open('/Users/jihanmaisaroh/scrap_fasih/app_v2.js', 'w', encoding='utf-8') as f:
        f.write(js)
    print("app_v2.js patched switchDataHilangSubTab")
else:
    print("Could not find switchDataHilangSubTab in app_v2.js")
