let currentPage = 1;
const itemsPerPage = 20;
let filteredData = [];
let sortColumn = null;
let sortAsc = true;
let columnFilters = {};
let currentFilterKey = null;
let filterPopup = null;

document.addEventListener('DOMContentLoaded', () => {
    try {
        if (!window.OPEN_SUBSLS_DATA) {
            console.error("OPEN_SUBSLS_DATA is missing");
            return;
        }

        filterPopup = document.createElement('div');
        filterPopup.className = 'excel-filter-popup';
        filterPopup.style.display = 'none';
        filterPopup.style.position = 'absolute';
        filterPopup.style.background = '#fff';
        filterPopup.style.border = '1px solid #ccc';
        filterPopup.style.boxShadow = '0 4px 6px rgba(0,0,0,0.1)';
        filterPopup.style.padding = '10px';
        filterPopup.style.zIndex = '9999';
        filterPopup.style.borderRadius = '4px';
        filterPopup.style.width = '200px';
        document.body.appendChild(filterPopup);

        document.addEventListener('click', (e) => {
            if (filterPopup && !filterPopup.contains(e.target) && e.target.tagName !== 'TH' && e.target.tagName !== 'SPAN') {
                filterPopup.style.display = 'none';
            }
        });

        initFilters();
        window.filterSubSlsData();
    } catch(err) {
        console.error("Error in DOMContentLoaded:", err);
        alert("JS Error: " + err.message);
    }
});

function initFilters() {
    const kabFilter = document.getElementById('subsls-filter-kab');
    if (!kabFilter) return;
    const kabupatens = [...new Set(window.OPEN_SUBSLS_DATA.map(d => d.kabupaten))].filter(Boolean).sort();
    kabupatens.forEach(kab => {
        const option = document.createElement('option');
        option.value = kab;
        option.textContent = kab;
        kabFilter.appendChild(option);
    });
}

window.toggleExcelFilter = function(e, key) {
    if (!e) return;
    e.stopPropagation();
    if (!filterPopup) return;

    if (filterPopup.style.display === 'block' && currentFilterKey === key) {
        filterPopup.style.display = 'none';
        return;
    }

    currentFilterKey = key;
    
    let uniqueVals = [...new Set(window.OPEN_SUBSLS_DATA.map(d => {
        if (key === 'nama_petugas' && !d[key]) return '(Belum Diassign)';
        if (key === 'nama_sub_sls') return d.nama_sub_sls || d.sls || '-';
        return d[key] || '-';
    }))].sort();

    let html = `
        <div style="margin-bottom: 10px; border-bottom: 1px solid #eee; padding-bottom: 5px;">
            <div style="cursor:pointer; margin-bottom:5px;" onclick="window.applySort('${key}', true)">&#x2191; Sort A to Z</div>
            <div style="cursor:pointer;" onclick="window.applySort('${key}', false)">&#x2193; Sort Z to A</div>
        </div>
        <input type="text" id="excel-search-${key}" placeholder="Search..." style="width: 100%; margin-bottom: 10px; padding: 4px; box-sizing: border-box;" oninput="window.filterExcelList()">
        <div id="excel-list-${key}" style="max-height: 150px; overflow-y: auto; margin-bottom: 10px; font-size: 0.85rem;">
    `;
    
    const activeSet = columnFilters[key];

    html += `<div><label><input type="checkbox" id="excel-all-${key}" ${!activeSet ? 'checked' : ''} onchange="window.toggleAllExcel(this)"> (Select All)</label></div>`;
    
    uniqueVals.forEach(v => {
        const isChecked = !activeSet || activeSet.has(v);
        html += `<div class="excel-item"><label><input type="checkbox" class="excel-chk" value="${v}" ${isChecked ? 'checked' : ''}> ${v}</label></div>`;
    });

    html += `
        </div>
        <div style="display: flex; justify-content: space-between;">
            <button onclick="window.applyExcelFilter()" style="padding: 2px 8px; background: #0ea5e9; color: white; border: none; border-radius: 4px; cursor: pointer;">OK</button>
            <button onclick="window.clearExcelFilter()" style="padding: 2px 8px; background: #e2e8f0; border: none; border-radius: 4px; cursor: pointer;">Clear</button>
        </div>
    `;

    filterPopup.innerHTML = html;
    
    // Position
    const rect = e.target.getBoundingClientRect();
    filterPopup.style.top = (rect.bottom + window.scrollY) + 'px';
    filterPopup.style.left = (rect.left + window.scrollX) + 'px';
    filterPopup.style.display = 'block';
};

window.applySort = function(key, asc) {
    sortColumn = key;
    sortAsc = asc;
    if(filterPopup) filterPopup.style.display = 'none';
    window.filterSubSlsData();
};

window.toggleAllExcel = function(cb) {
    document.querySelectorAll('.excel-chk').forEach(c => c.checked = cb.checked);
};

window.filterExcelList = function() {
    const q = document.getElementById(`excel-search-${currentFilterKey}`).value.toLowerCase();
    document.querySelectorAll('.excel-item').forEach(el => {
        const txt = el.textContent.toLowerCase();
        el.style.display = txt.includes(q) ? 'block' : 'none';
    });
};

window.applyExcelFilter = function() {
    const allChecked = document.getElementById(`excel-all-${currentFilterKey}`).checked;
    if (allChecked) {
        delete columnFilters[currentFilterKey];
    } else {
        const selected = new Set();
        document.querySelectorAll('.excel-chk:checked').forEach(c => selected.add(c.value));
        columnFilters[currentFilterKey] = selected;
    }
    if(filterPopup) filterPopup.style.display = 'none';
    window.filterSubSlsData();
};

window.clearExcelFilter = function() {
    delete columnFilters[currentFilterKey];
    if(filterPopup) filterPopup.style.display = 'none';
    window.filterSubSlsData();
};

window.filterSubSlsData = function() {
    if (!window.OPEN_SUBSLS_DATA) return;
    
    const searchInput = document.getElementById('subsls-search-input');
    const kabFilter = document.getElementById('subsls-filter-kab');
    const searchTerm = (searchInput ? searchInput.value : '').toLowerCase();
    const kabTerm = kabFilter ? kabFilter.value : '';

    filteredData = window.OPEN_SUBSLS_DATA.filter(item => {
        if (kabTerm && item.kabupaten !== kabTerm) return false;

        for (const key in columnFilters) {
            const allowed = columnFilters[key];
            if (!allowed) continue;
            
            let val = item[key] || '-';
            if (key === 'nama_petugas' && !item[key]) val = '(Belum Diassign)';
            if (key === 'nama_sub_sls') val = item.nama_sub_sls || item.sls || '-';
            
            if (!allowed.has(val.toString())) return false;
        }

        if (!searchTerm) return true;

        const searchableFields = [
            item.kode_sub_sls,
            item.kabupaten,
            item.kecamatan,
            item.desa,
            item.nama_sub_sls,
            item.nama_petugas,
            (!item.nama_petugas ? 'belum diassign kosong' : '')
        ].map(f => (f || '').toString().toLowerCase());

        return searchableFields.some(field => field.includes(searchTerm));
    });

    if (sortColumn) {
        filteredData.sort((a, b) => {
            let valA = a[sortColumn] || '';
            let valB = b[sortColumn] || '';
            
            if (sortColumn === 'nama_sub_sls') {
                valA = a.nama_sub_sls || a.sls || '';
                valB = b.nama_sub_sls || b.sls || '';
            }
            if (sortColumn === 'nama_petugas') {
                valA = a.nama_petugas || '';
                valB = b.nama_petugas || '';
            }
            
            if (sortColumn === 'jumlah_prelist') {
                valA = parseInt(valA) || 0;
                valB = parseInt(valB) || 0;
                return sortAsc ? (valA - valB) : (valB - valA);
            }

            if (typeof valA === 'string') valA = valA.toLowerCase();
            if (typeof valB === 'string') valB = valB.toLowerCase();

            if (valA < valB) return sortAsc ? -1 : 1;
            if (valA > valB) return sortAsc ? 1 : -1;
            return 0;
        });
    }

    currentPage = 1;
    
    // Update stats
    const uniqueSubSls = new Set(filteredData.map(d => d.kode_sub_sls)).size;
    const totalPrelists = filteredData.reduce((sum, item) => sum + (item.jumlah_prelist || 0), 0);
    const elSubTotal = document.getElementById('stat-subsls-total');
    const elSubPrelist = document.getElementById('stat-subsls-prelist');
    if(elSubTotal) elSubTotal.textContent = uniqueSubSls.toLocaleString('id-ID');
    if(elSubPrelist) elSubPrelist.textContent = totalPrelists.toLocaleString('id-ID');

    renderTable();
};

function renderTable() {
    const tbody = document.getElementById('tbody-subsls-open');
    const pagination = document.getElementById('pagination-subsls-open');
    if(!tbody) return;
    
    tbody.innerHTML = '';
    const start = (currentPage - 1) * itemsPerPage;
    const end = start + itemsPerPage;
    const paginatedData = filteredData.slice(start, end);

    if (paginatedData.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding: 2rem;">Tidak ada data ditemukan</td></tr>';
        if(pagination) pagination.innerHTML = '';
        return;
    }

    paginatedData.forEach(item => {
        const tr = document.createElement('tr');
        const isUnassigned = !item.nama_petugas;
        const petugasHtml = isUnassigned 
            ? '<span style="color: #ef4444; font-weight: 600; font-size: 0.8rem; background: rgba(239, 68, 68, 0.1); padding: 2px 6px; border-radius: 4px;">BELUM DIASSIGN</span>'
            : `<span style="color: var(--text-primary); font-weight: 500;">${item.nama_petugas}</span>`;

        tr.innerHTML = `
            <td style="font-family: monospace; font-weight: 600;">${item.kode_sub_sls || '-'}</td>
            <td>${item.kabupaten || '-'}</td>
            <td>${item.kecamatan || '-'}</td>
            <td>${item.desa || '-'}</td>
            <td>${item.nama_sub_sls || item.sls || '-'}</td>
            <td>${petugasHtml}</td>
            <td style="text-align: right; font-weight: 600;">${item.jumlah_prelist || 0}</td>
        `;
        tbody.appendChild(tr);
    });

    if(pagination) {
        pagination.innerHTML = '';
        const totalPages = Math.ceil(filteredData.length / itemsPerPage);
        if (totalPages <= 1) return;

        const maxButtons = 5;
        let startPage = Math.max(1, currentPage - Math.floor(maxButtons / 2));
        let endPage = Math.min(totalPages, startPage + maxButtons - 1);
        if (endPage - startPage + 1 < maxButtons) {
            startPage = Math.max(1, endPage - maxButtons + 1);
        }

        const prevBtn = document.createElement('button');
        prevBtn.textContent = '«';
        prevBtn.className = 'page-btn' + (currentPage === 1 ? ' disabled' : '');
        prevBtn.onclick = () => { if (currentPage > 1) { currentPage--; renderTable(); } };
        pagination.appendChild(prevBtn);

        for (let i = startPage; i <= endPage; i++) {
            const btn = document.createElement('button');
            btn.textContent = i;
            btn.className = 'page-btn' + (i === currentPage ? ' active' : '');
            btn.onclick = () => { currentPage = i; renderTable(); };
            pagination.appendChild(btn);
        }

        const nextBtn = document.createElement('button');
        nextBtn.textContent = '»';
        nextBtn.className = 'page-btn' + (currentPage === totalPages ? ' disabled' : '');
        nextBtn.onclick = () => { if (currentPage < totalPages) { currentPage++; renderTable(); } };
        pagination.appendChild(nextBtn);
    }
}
