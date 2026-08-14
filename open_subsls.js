document.addEventListener('DOMContentLoaded', () => {
    // Only init if data exists
    if (!window.OPEN_SUBSLS_DATA) return;

    let currentPage = 1;
    const itemsPerPage = 20;
    let filteredData = [];
    let sortColumn = null;
    let sortAsc = true;

    const searchInput = document.getElementById('subsls-search-input');
    const kabFilter = document.getElementById('subsls-filter-kab');
    const tbody = document.getElementById('tbody-subsls-open');
    const pagination = document.getElementById('pagination-subsls-open');

    // Initialize Filter Options
    function initFilters() {
        const kabupatens = [...new Set(window.OPEN_SUBSLS_DATA.map(d => d.kabupaten))].filter(Boolean).sort();
        kabupatens.forEach(kab => {
            const option = document.createElement('option');
            option.value = kab;
            option.textContent = kab;
            kabFilter.appendChild(option);
        });
    }

    function renderStats(data) {
        // Unique Sub SLS count
        const uniqueSubSls = new Set(data.map(d => d.kode_sub_sls)).size;
        // Total Prelists
        const totalPrelists = data.reduce((sum, item) => sum + (item.jumlah_prelist || 0), 0);

        document.getElementById('stat-subsls-total').textContent = uniqueSubSls.toLocaleString('id-ID');
        document.getElementById('stat-subsls-prelist').textContent = totalPrelists.toLocaleString('id-ID');
    }

    function renderTable() {
        tbody.innerHTML = '';
        
        const start = (currentPage - 1) * itemsPerPage;
        const end = start + itemsPerPage;
        const paginatedData = filteredData.slice(start, end);

        if (paginatedData.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding: 2rem;">Tidak ada data ditemukan</td></tr>';
            renderPagination();
            return;
        }

        paginatedData.forEach(item => {
            const tr = document.createElement('tr');
            
            // Highlight unassigned
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

        renderPagination();
    }

    function renderPagination() {
        pagination.innerHTML = '';
        const totalPages = Math.ceil(filteredData.length / itemsPerPage);
        
        if (totalPages <= 1) return;

        const maxButtons = 5;
        let startPage = Math.max(1, currentPage - Math.floor(maxButtons / 2));
        let endPage = Math.min(totalPages, startPage + maxButtons - 1);

        if (endPage - startPage + 1 < maxButtons) {
            startPage = Math.max(1, endPage - maxButtons + 1);
        }

        // Prev Button
        const prevBtn = document.createElement('button');
        prevBtn.textContent = '«';
        prevBtn.className = 'page-btn' + (currentPage === 1 ? ' disabled' : '');
        prevBtn.onclick = () => { if (currentPage > 1) { currentPage--; renderTable(); } };
        pagination.appendChild(prevBtn);

        // Page Buttons
        for (let i = startPage; i <= endPage; i++) {
            const btn = document.createElement('button');
            btn.textContent = i;
            btn.className = 'page-btn' + (i === currentPage ? ' active' : '');
            btn.onclick = () => { currentPage = i; renderTable(); };
            pagination.appendChild(btn);
        }

        // Next Button
        const nextBtn = document.createElement('button');
        nextBtn.textContent = '»';
        nextBtn.className = 'page-btn' + (currentPage === totalPages ? ' disabled' : '');
        nextBtn.onclick = () => { if (currentPage < totalPages) { currentPage++; renderTable(); } };
        pagination.appendChild(nextBtn);
    }

    window.sortSubSls = function(key) {
        if (sortColumn === key) {
            sortAsc = !sortAsc;
        } else {
            sortColumn = key;
            sortAsc = true;
        }

        // Reset sort icons
        const keys = ['kode_sub_sls', 'kabupaten', 'kecamatan', 'desa', 'nama_sub_sls', 'nama_petugas', 'jumlah_prelist'];
        keys.forEach(k => {
            const el = document.getElementById('sort-' + k);
            if (el) el.textContent = '↕';
        });

        // Set active sort icon
        const activeEl = document.getElementById('sort-' + key);
        if (activeEl) {
            activeEl.textContent = sortAsc ? '↑' : '↓';
        }

        window.filterSubSlsData();
    };

    window.filterSubSlsData = function() {
        const searchTerm = (searchInput.value || '').toLowerCase();
        const kabTerm = kabFilter.value;
        
        // Column filters
        const cKode = (document.getElementById('col-filter-kode_sub_sls')?.value || '').toLowerCase();
        const cKab = (document.getElementById('col-filter-kabupaten')?.value || '').toLowerCase();
        const cKec = (document.getElementById('col-filter-kecamatan')?.value || '').toLowerCase();
        const cDesa = (document.getElementById('col-filter-desa')?.value || '').toLowerCase();
        const cSls = (document.getElementById('col-filter-nama_sub_sls')?.value || '').toLowerCase();
        const cPetugas = (document.getElementById('col-filter-nama_petugas')?.value || '').toLowerCase();

        filteredData = window.OPEN_SUBSLS_DATA.filter(item => {
            const matchKab = !kabTerm || item.kabupaten === kabTerm;
            if (!matchKab) return false;

            // Individual column filters
            if (cKode && !(item.kode_sub_sls || '').toString().toLowerCase().includes(cKode)) return false;
            if (cKab && !(item.kabupaten || '').toString().toLowerCase().includes(cKab)) return false;
            if (cKec && !(item.kecamatan || '').toString().toLowerCase().includes(cKec)) return false;
            if (cDesa && !(item.desa || '').toString().toLowerCase().includes(cDesa)) return false;
            if (cSls && !(item.nama_sub_sls || item.sls || '').toString().toLowerCase().includes(cSls)) return false;
            
            if (cPetugas) {
                const petugasName = (!item.nama_petugas ? 'belum diassign kosong' : item.nama_petugas.toString().toLowerCase());
                if (!petugasName.includes(cPetugas)) return false;
            }

            // Global search
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

        // Apply Sort
        if (sortColumn) {
            filteredData.sort((a, b) => {
                let valA = a[sortColumn] || '';
                let valB = b[sortColumn] || '';
                
                // Fallback for SLS name since data could have 'sls' or 'nama_sub_sls'
                if (sortColumn === 'nama_sub_sls') {
                    valA = a.nama_sub_sls || a.sls || '';
                    valB = b.nama_sub_sls || b.sls || '';
                }

                // Treat unassigned as empty string for sorting
                if (sortColumn === 'nama_petugas') {
                    valA = a.nama_petugas || '';
                    valB = b.nama_petugas || '';
                }

                if (typeof valA === 'string') valA = valA.toLowerCase();
                if (typeof valB === 'string') valB = valB.toLowerCase();

                if (valA < valB) return sortAsc ? -1 : 1;
                if (valA > valB) return sortAsc ? 1 : -1;
                return 0;
            });
        }

        currentPage = 1;
        renderStats(filteredData);
        renderTable();
    };

    if (searchInput) {
        searchInput.addEventListener('input', window.filterSubSlsData);
    }

    // Initial Load
    initFilters();
    window.filterSubSlsData();
});
