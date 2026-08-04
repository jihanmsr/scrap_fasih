window.downloadRekonData = function () {
    const isSls = document.getElementById('rekon-sub-sls').style.display !== 'none';
    const tableSelector = isSls ? '#rekon-sub-sls table' : '#rekon-sub-petugas table';
    const table = document.querySelector(tableSelector);
    if (!table) {
        alert("Tabel tidak ditemukan!");
        return;
    }
    let csv = [];
    let rows = table.querySelectorAll('tr');
    for (let i = 0; i < rows.length; i++) {
        let row = [], cols = rows[i].querySelectorAll('td, th');
        for (let j = 0; j < cols.length; j++) {
            let data = cols[j].innerText.replace(/(\r\n|\n|\r)/gm, ' ').replace(/"/g, '""');
            row.push('"' + data + '"');
        }
        csv.push(row.join(','));
    }
    let blob = new Blob([csv.join('\n')], { type: 'text/csv;charset=utf-8;' });
    let link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    let typeName = isSls ? 'sls' : 'petugas';
    link.download = `tabel_rekon_${typeName}.csv`;
    link.style.display = "none";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
};
