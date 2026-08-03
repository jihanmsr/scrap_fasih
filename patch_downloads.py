import re

with open("app.js", "r") as f:
    content = f.read()

# 1. Update switchGranularSummaryView to toggle the buttons
content = content.replace("function switchGranularSummaryView(view) {", "window.switchGranularSummaryView = function(view) {")

if "document.getElementById('btn-download-excel-desa');" not in content:
    content = content.replace("""    if (view === 'petugas') {
        document.getElementById('petugas-summary-table-container').style.display = '';
        document.getElementById('petugas-summary-pagination').style.display = 'flex';
        document.getElementById('desa-summary-table-container').style.display = 'none';
        document.getElementById('btn-summary-petugas').classList.add('active');
        document.getElementById('btn-summary-desa').classList.remove('active');
    } else {""", """    if (view === 'petugas') {
        document.getElementById('petugas-summary-table-container').style.display = '';
        document.getElementById('petugas-summary-pagination').style.display = 'flex';
        document.getElementById('desa-summary-table-container').style.display = 'none';
        document.getElementById('btn-summary-petugas').classList.add('active');
        document.getElementById('btn-summary-desa').classList.remove('active');
        if (document.getElementById('btn-download-excel-petugas')) document.getElementById('btn-download-excel-petugas').style.display = 'flex';
        if (document.getElementById('btn-download-excel-desa')) document.getElementById('btn-download-excel-desa').style.display = 'none';
    } else {""")
    content = content.replace("""        document.getElementById('petugas-summary-table-container').style.display = 'none';
        document.getElementById('petugas-summary-pagination').style.display = 'none';
        document.getElementById('desa-summary-table-container').style.display = '';
        document.getElementById('btn-summary-petugas').classList.remove('active');
        document.getElementById('btn-summary-desa').classList.add('active');
        
        // Render desa if empty
        if (!window.desaSummaryData || window.desaSummaryData.length === 0) {
            renderDesaSummaryTable();
        }
    }
}""", """        document.getElementById('petugas-summary-table-container').style.display = 'none';
        document.getElementById('petugas-summary-pagination').style.display = 'none';
        document.getElementById('desa-summary-table-container').style.display = '';
        document.getElementById('btn-summary-petugas').classList.remove('active');
        document.getElementById('btn-summary-desa').classList.add('active');
        if (document.getElementById('btn-download-excel-petugas')) document.getElementById('btn-download-excel-petugas').style.display = 'none';
        if (document.getElementById('btn-download-excel-desa')) document.getElementById('btn-download-excel-desa').style.display = 'flex';
        
        // Render desa if empty
        if (!window.desaSummaryData || window.desaSummaryData.length === 0) {
            renderDesaSummaryTable();
        }
    }
}""")

# 2. Add downloadDesaSummaryExcel
desa_func = """
window.downloadDesaSummaryExcel = function () {
    if (!window.desaSummaryData || window.desaSummaryData.length === 0) {
        alert("Tidak ada data desa untuk didownload.");
        return;
    }
    let csv = "Kecamatan,Desa/Kelurahan,Total Target,Belum Selesai,Selesai,Persentase\\n";
    window.desaSummaryData.forEach(d => {
        let pct = d.total > 0 ? ((d.selesai / d.total) * 100).toFixed(1) : 0;
        csv += `"${d.kec}","${d.desa}",${d.total},${d.belum},${d.selesai},"${pct}%"\\n`;
    });
    let blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    let link = document.createElement("a");
    let url = URL.createObjectURL(blob);
    link.setAttribute("href", url);
    link.setAttribute("download", "rekap_desa_sulteng.csv");
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
};
"""
if "downloadDesaSummaryExcel" not in content:
    content += desa_func

# 3. Add downloadEmailTable
email_func = """
window.downloadEmailTable = function () {
    const table = document.querySelector('.company-table');
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
    link.download = "tabel_status_email.csv";
    link.style.display = "none";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
};
"""
if "downloadEmailTable" not in content:
    content += email_func

with open("app.js", "w") as f:
    f.write(content)
