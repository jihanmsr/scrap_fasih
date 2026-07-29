import re

with open('rekon.js', 'r') as f:
    js = f.read()

# Replace loadRekonData logic
new_load = """
async function loadRekonData() {
    try {
        if (window.rekonSlsData) rekonSlsData = window.rekonSlsData;
        if (window.rekonPetugasData) rekonPetugasData = window.rekonPetugasData;
        
        initRekonFilters();
        renderRekon();
    } catch (e) {
        console.error("Gagal load data rekon:", e);
    }
}
"""

js = re.sub(r'async function loadRekonData\(\) \{.*?\n\}', new_load, js, flags=re.DOTALL)

with open('rekon.js', 'w') as f:
    f.write(js)

