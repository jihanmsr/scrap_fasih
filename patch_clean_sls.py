import re

with open('rekon.js', 'r') as f:
    content = f.read()

# Add a cleanup step right after loading data
cleanup_logic = """
async function loadRekonData() {
    try {
        if (window.rekonSlsData) {
            // Clean up garbage rows (e.g., nmkab is 0 or '-')
            rekonSlsData = window.rekonSlsData.filter(d => d.nmkab && d.nmkab !== 0 && d.nmkab !== '-');
            
            // Remove .0 from sls_id if present
            rekonSlsData.forEach(d => {
                if (typeof d.sls_id === 'number') {
                    d.sls_id = d.sls_id.toString().replace(/\.0$/, '');
                } else if (typeof d.sls_id === 'string') {
                    d.sls_id = d.sls_id.replace(/\.0$/, '');
                }
            });
        }
        if (window.rekonPetugasData) rekonPetugasData = window.rekonPetugasData;

        initRekonFilters();
"""

content = re.sub(r'async function loadRekonData\(\) \{\n    try \{\n        if \(window.rekonSlsData\) rekonSlsData = window.rekonSlsData;\n        if \(window.rekonPetugasData\) rekonPetugasData = window.rekonPetugasData;\n\n        initRekonFilters\(\);', cleanup_logic, content, flags=re.DOTALL)

with open('rekon.js', 'w') as f:
    f.write(content)
