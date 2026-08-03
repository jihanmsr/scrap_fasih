import re

with open("rekon.js", "r") as f:
    content = f.read()

rekon_func = """
window.downloadRekonData = function () {
    const table = document.querySelector('#rekon-sls-table');
    if (!table) return;
    let csv = [];
    let rows = table.querySelectorAll('tr');
    for (let i = 0; i < rows.length; i++) {
        let row = [], cols = rows[i].querySelectorAll('td, th');
        for (let j = 0; j < cols.length; j++) {
            let data = cols[j].innerText.replace(/(\\r\\n|\\n|\\r)/gm, ' ').replace(/"/g, '""');
            row.push('"' + data + '"');
        }
        csv.push(row.join(','));
    }
    let blob = new Blob([csv.join('\\n')], { type: 'text/csv;charset=utf-8;' });
    let link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "tabel_rekon_sls.csv";
    link.style.display = "none";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
};
"""
if "downloadRekonData" not in content:
    content += rekon_func

with open("rekon.js", "w") as f:
    f.write(content)
