import re

filename = "app.js"
with open(filename, "r") as f:
    content = f.read()

# We need to compute delta_kemarin_persen and delta_lusa_persen inside app.js if they don't exist.
# Let's find where IPAS_DATA is processed or just before we render the table rows.
# In app.js, renderSeTableBody iterates over dataToRender.

injection = """
        // Inject historical deltas from DAILY_SUMMARY if available
        if (window.DAILY_SUMMARY) {
            const today = new Date();
            const getStr = (d) => {
                const nd = new Date(d);
                return nd.getFullYear() + "-" + String(nd.getMonth()+1).padStart(2,'0') + "-" + String(nd.getDate()).padStart(2,'0');
            };
            const h1Date = new Date(); h1Date.setDate(h1Date.getDate() - 1);
            const h2Date = new Date(); h2Date.setDate(h2Date.getDate() - 2);
            const h3Date = new Date(); h3Date.setDate(h3Date.getDate() - 3);
            
            const h1Str = getStr(h1Date);
            const h2Str = getStr(h2Date);
            const h3Str = getStr(h3Date);
            
            dataToRender.forEach(item => {
                let kabNameClean = item.kabupaten.replace(/\\[\\d+\\]/g, '').trim().toUpperCase();
                
                const getSubForDate = (dateStr) => {
                    const row = window.DAILY_SUMMARY.find(r => r.tanggal === dateStr && r.kabupaten === kabNameClean);
                    return row ? row.total_submitted : null;
                };
                
                const subH1 = getSubForDate(h1Str);
                const subH2 = getSubForDate(h2Str);
                const subH3 = getSubForDate(h3Str);
                
                if (item.total_prelist > 0) {
                    if (subH1 !== null && subH2 !== null) {
                        const tc1 = subH1 - subH2;
                        if(item.delta_kemarin_persen === undefined) item.delta_kemarin_persen = (tc1 / item.total_prelist) * 100;
                    }
                    if (subH2 !== null && subH3 !== null) {
                        const tc2 = subH2 - subH3;
                        if(item.delta_lusa_persen === undefined) item.delta_lusa_persen = (tc2 / item.total_prelist) * 100;
                    }
                }
            });
        }
"""

target_hook = "const tbody = document.getElementById('se-umum-table-body');"
if target_hook in content:
    content = content.replace(target_hook, injection + "\n        " + target_hook)
    print("Injected historical delta computation")
else:
    print("Could not find target hook")

with open(filename, "w") as f:
    f.write(content)
