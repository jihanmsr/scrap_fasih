/**
 * Belum Diassign Monitoring Module
 * Manages rendering, filtering, sorting, pagination, and Excel export for unassigned data.
 */

(function () {
    let rawData = [];
    let filteredData = [];
    let currentPage = 1;
    let itemsPerPage = 25;
    let sortColumn = 'idsubsls';
    let sortAsc = true;
    let isInitialized = false;

    window.initBelumDiassign = function () {
        if (!window.BELUM_DIASSIGN_DATA || !Array.isArray(window.BELUM_DIASSIGN_DATA)) {
            console.warn("BELUM_DIASSIGN_DATA not available.");
            return;
        }

        rawData = window.BELUM_DIASSIGN_DATA;
        filteredData = [...rawData];

        if (!isInitialized) {
            populateKabupatenFilter();
            populateStatusFilter();
            setupEventListeners();
            isInitialized = true;
        }

        updateStats();
        applyFilters();
    };

    function populateKabupatenFilter() {
        const select = document.getElementById('belum-filter-kab');
        if (!select) return;

        const kabs = [...new Set(rawData.map(d => d.kab_name).filter(Boolean))].sort();
        select.innerHTML = '<option value="">Semua Kabupaten/Kota</option>';
        kabs.forEach(kab => {
            const opt = document.createElement('option');
            opt.value = kab;
            opt.textContent = kab;
            select.appendChild(opt);
        });
    }

    function populateStatusFilter() {
        const select = document.getElementById('belum-filter-status');
        if (!select) return;

        const statuses = [...new Set(rawData.map(d => d.status).filter(Boolean))].sort();
        select.innerHTML = '<option value="">Semua Status</option>';
        statuses.forEach(st => {
            const opt = document.createElement('option');
            opt.value = st;
            opt.textContent = st;
            select.appendChild(opt);
        });
    }

    function setupEventListeners() {
        const searchInput = document.getElementById('belum-search-input');
        if (searchInput) {
            searchInput.addEventListener('input', () => {
                currentPage = 1;
                applyFilters();
            });
        }

        const kabFilter = document.getElementById('belum-filter-kab');
        if (kabFilter) {
            kabFilter.addEventListener('change', () => {
                currentPage = 1;
                applyFilters();
            });
        }

        const statusFilter = document.getElementById('belum-filter-status');
        if (statusFilter) {
            statusFilter.addEventListener('change', () => {
                currentPage = 1;
                applyFilters();
            });
        }

        const modeFilter = document.getElementById('belum-filter-mode');
        if (modeFilter) {
            modeFilter.addEventListener('change', () => {
                currentPage = 1;
                applyFilters();
            });
        }

        const pageSizeSelect = document.getElementById('belum-page-size');
        if (pageSizeSelect) {
            pageSizeSelect.addEventListener('change', (e) => {
                itemsPerPage = parseInt(e.target.value, 10) || 25;
                currentPage = 1;
                renderTable();
            });
        }
    }

    function updateStats() {
        const totalCount = rawData.length;
        const submittedCount = rawData.filter(d => (d.status || '').toUpperCase().includes('SUBMITTED')).length;
        const draftCount = rawData.filter(d => (d.status || '').toUpperCase().includes('DRAFT')).length;
        const approvedCount = rawData.filter(d => (d.status || '').toUpperCase().includes('APPROVED')).length;
        const uniqueKab = new Set(rawData.map(d => d.kab_name).filter(Boolean)).size;

        const statTotal = document.getElementById('stat-belum-total');
        const statSubmitted = document.getElementById('stat-belum-submitted');
        const statDraft = document.getElementById('stat-belum-draft');
        const statApproved = document.getElementById('stat-belum-approved');
        const statKab = document.getElementById('stat-belum-kab');

        if (statTotal) statTotal.textContent = totalCount.toLocaleString('id-ID');
        if (statSubmitted) statSubmitted.textContent = submittedCount.toLocaleString('id-ID');
        if (statDraft) statDraft.textContent = draftCount.toLocaleString('id-ID');
        if (statApproved) statApproved.textContent = approvedCount.toLocaleString('id-ID');
        if (statKab) statKab.textContent = uniqueKab.toLocaleString('id-ID');
    }

    window.applyFilters = function () {
        const searchInput = document.getElementById('belum-search-input');
        const kabFilter = document.getElementById('belum-filter-kab');
        const statusFilter = document.getElementById('belum-filter-status');
        const modeFilter = document.getElementById('belum-filter-mode');

        const query = searchInput ? searchInput.value.toLowerCase().trim() : '';
        const selectedKab = kabFilter ? kabFilter.value : '';
        const selectedStatus = statusFilter ? statusFilter.value : '';
        const selectedMode = modeFilter ? modeFilter.value : '';

        filteredData = rawData.filter(item => {
            if (selectedKab && item.kab_name !== selectedKab) return false;
            if (selectedStatus && item.status !== selectedStatus) return false;
            if (selectedMode && item.mode !== selectedMode) return false;

            if (query) {
                const combined = `${item.idsubsls} ${item.data1} ${item.code_identity} ${item.alamat} ${item.catatan} ${item.assignment_id} ${item.kab_name}`.toLowerCase();
                if (!combined.includes(query)) return false;
            }

            return true;
        });

        // Apply sorting
        if (sortColumn) {
            filteredData.sort((a, b) => {
                let valA = a[sortColumn] || '';
                let valB = b[sortColumn] || '';
                if (typeof valA === 'string') valA = valA.toLowerCase();
                if (typeof valB === 'string') valB = valB.toLowerCase();

                if (valA < valB) return sortAsc ? -1 : 1;
                if (valA > valB) return sortAsc ? 1 : -1;
                return 0;
            });
        }

        renderTable();
    };

    window.sortBelumTable = function (column) {
        if (sortColumn === column) {
            sortAsc = !sortAsc;
        } else {
            sortColumn = column;
            sortAsc = true;
        }
        applyFilters();
    };

    function renderTable() {
        const tbody = document.getElementById('tbody-belum-diassign');
        if (!tbody) return;

        const totalItems = filteredData.length;
        const totalPages = Math.ceil(totalItems / itemsPerPage) || 1;
        if (currentPage > totalPages) currentPage = totalPages;
        if (currentPage < 1) currentPage = 1;

        const startIndex = (currentPage - 1) * itemsPerPage;
        const pageData = filteredData.slice(startIndex, startIndex + itemsPerPage);

        if (pageData.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="9" style="text-align: center; padding: 2.5rem; color: var(--text-secondary);">
                        <div style="font-size: 1.1rem; font-weight: 600; margin-bottom: 0.25rem;">Tidak ada data ditemukan</div>
                        <div style="font-size: 0.85rem;">Coba sesuaikan kata kunci pencarian atau filter yang dipilih.</div>
                    </td>
                </tr>
            `;
            updatePaginationInfo(0, 0, 0, 1);
            return;
        }

        tbody.innerHTML = pageData.map((row, idx) => {
            const rowNum = startIndex + idx + 1;
            
            // Status badge styling
            let statusBadge = `<span class="badge" style="background:#e2e8f0; color:#475569; font-weight:600;">${row.status || '-'}</span>`;
            const st = (row.status || '').toUpperCase();
            if (st.includes('SUBMITTED')) {
                statusBadge = `<span class="badge" style="background:#dbeafe; color:#1e40af; font-weight:700; border: 1px solid #bfdbfe;">📤 SUBMITTED</span>`;
            } else if (st.includes('DRAFT')) {
                statusBadge = `<span class="badge" style="background:#fef3c7; color:#92400e; font-weight:700; border: 1px solid #fde68a;">📝 DRAFT</span>`;
            } else if (st.includes('APPROVED')) {
                statusBadge = `<span class="badge" style="background:#dcfce7; color:#166534; font-weight:700; border: 1px solid #bbf7d0;">✅ APPROVED</span>`;
            }

            // Mode badge
            let modeBadge = `<span style="font-size:0.75rem; font-weight:600; color:#64748b;">${row.mode || '-'}</span>`;
            if (row.mode === '[CAPI]') {
                modeBadge = `<span style="background:#f1f5f9; color:#0f172a; padding:2px 8px; border-radius:4px; font-weight:700; font-size:0.75rem; border:1px solid #cbd5e1;">CAPI</span>`;
            } else if (row.mode === '[CAWI]') {
                modeBadge = `<span style="background:#fdf2f8; color:#9d174d; padding:2px 8px; border-radius:4px; font-weight:700; font-size:0.75rem; border:1px solid #fbcfe8;">CAWI</span>`;
            }

            // Map link
            let coordDisplay = `<span style="color:#94a3b8; font-size:0.8rem;">-</span>`;
            if (row.lat && row.lng) {
                const mapsUrl = `https://www.google.com/maps?q=${row.lat},${row.lng}`;
                coordDisplay = `
                    <a href="${mapsUrl}" target="_blank" rel="noopener noreferrer" style="display:inline-flex; align-items:center; gap:4px; color:#2563eb; font-size:0.8rem; text-decoration:none; font-weight:600;" title="Buka di Google Maps">
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
                        ${Number(row.lat).toFixed(5)}, ${Number(row.lng).toFixed(5)}
                    </a>
                `;
            }

            // Fasih link button
            let actionBtn = `<span style="color:#94a3b8; font-size:0.8rem;">-</span>`;
            if (row.link_assignment) {
                actionBtn = `
                    <a href="${row.link_assignment}" target="_blank" rel="noopener noreferrer" class="btn-action-sm" style="display:inline-flex; align-items:center; gap:5px; padding:4px 10px; background:#4f46e5; color:#ffffff; border-radius:6px; font-size:0.75rem; font-weight:600; text-decoration:none; box-shadow:0 1px 2px rgba(79,70,229,0.2); transition:background 0.15s;" onmouseover="this.style.background='#4338ca'" onmouseout="this.style.background='#4f46e5'">
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
                        Buka Fasih
                    </a>
                `;
            }

            return `
                <tr>
                    <td style="text-align: center; color: var(--text-secondary); font-size: 0.8rem;">${rowNum}</td>
                    <td>
                        <div style="font-family: monospace; font-weight: 700; color: var(--primary); font-size: 0.85rem;">${row.idsubsls || '-'}</div>
                    </td>
                    <td>
                        <div style="font-size: 0.82rem; font-weight: 600;">${row.kab_name || '-'}</div>
                    </td>
                    <td>
                        <div style="font-weight: 700; color: var(--text-primary); font-size: 0.88rem; margin-bottom: 2px;">${row.data1 || '-'}</div>
                        <div style="font-size: 0.75rem; color: var(--text-secondary); line-height: 1.3;" title="${row.code_identity}">${row.code_identity.length > 60 ? row.code_identity.substring(0, 60) + '...' : row.code_identity}</div>
                    </td>
                    <td>${statusBadge}</td>
                    <td style="text-align: center;">${modeBadge}</td>
                    <td>
                        <div style="font-size: 0.8rem; color: var(--text-secondary); max-width: 220px; word-break: break-word;">${row.alamat || row.catatan || '-'}</div>
                    </td>
                    <td>${coordDisplay}</td>
                    <td style="text-align: center;">${actionBtn}</td>
                </tr>
            `;
        }).join('');

        updatePaginationInfo(startIndex + 1, Math.min(startIndex + itemsPerPage, totalItems), totalItems, totalPages);
    }

    function updatePaginationInfo(start, end, total, totalPages) {
        const info = document.getElementById('belum-page-info');
        if (info) {
            info.textContent = total === 0 ? 'Menampilkan 0 data' : `Menampilkan ${start} - ${end} dari ${total.toLocaleString('id-ID')} data`;
        }

        const prevBtn = document.getElementById('belum-btn-prev');
        const nextBtn = document.getElementById('belum-btn-next');
        if (prevBtn) prevBtn.disabled = currentPage <= 1;
        if (nextBtn) nextBtn.disabled = currentPage >= totalPages;

        const pageNumsContainer = document.getElementById('belum-page-nums');
        if (pageNumsContainer) {
            pageNumsContainer.innerHTML = '';
            
            // Build pagination buttons
            const maxVisible = 5;
            let startPage = Math.max(1, currentPage - Math.floor(maxVisible / 2));
            let endPage = Math.min(totalPages, startPage + maxVisible - 1);
            if (endPage - startPage + 1 < maxVisible) {
                startPage = Math.max(1, endPage - maxVisible + 1);
            }

            for (let i = startPage; i <= endPage; i++) {
                const btn = document.createElement('button');
                btn.textContent = i;
                btn.className = `btn-page ${i === currentPage ? 'active' : ''}`;
                btn.style.cssText = `
                    padding: 0.3rem 0.65rem;
                    border: 1px solid var(--card-border);
                    border-radius: 0.4rem;
                    background: ${i === currentPage ? 'var(--primary)' : 'var(--input-bg)'};
                    color: ${i === currentPage ? '#ffffff' : 'var(--text-secondary)'};
                    font-weight: ${i === currentPage ? '700' : '500'};
                    font-size: 0.8rem;
                    cursor: pointer;
                `;
                btn.onclick = () => {
                    currentPage = i;
                    renderTable();
                };
                pageNumsContainer.appendChild(btn);
            }
        }
    }

    window.changeBelumPage = function (delta) {
        currentPage += delta;
        renderTable();
    };

    window.downloadBelumExcel = function () {
        if (!window.XLSX) {
            alert('Library SheetJS (XLSX) belum dimuat.');
            return;
        }

        const dataToExport = filteredData.map((d, idx) => ({
            'No': idx + 1,
            'ID Sub SLS': d.idsubsls,
            'Kabupaten/Kota': d.kab_name,
            'Nama Usaha / Prelist': d.data1,
            'Code Identity': d.code_identity,
            'Status Assignment': d.status,
            'Mode': d.mode,
            'Alamat': d.alamat,
            'Latitude': d.lat || '',
            'Longitude': d.lng || '',
            'Catatan': d.catatan,
            'Link Assignment': d.link_assignment
        }));

        const ws = XLSX.utils.json_to_sheet(dataToExport);
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, "Belum Diassign");

        const now = new Date();
        const dateStr = now.toISOString().slice(0, 10);
        XLSX.writeFile(wb, `Data_Belum_Diassign_${dateStr}.xlsx`);
    };

    // Auto-init if DOM is already ready
    if (typeof document !== 'undefined') {
        if (document.readyState === 'complete' || document.readyState === 'interactive') {
            setTimeout(window.initBelumDiassign, 100);
        } else {
            document.addEventListener('DOMContentLoaded', () => {
                setTimeout(window.initBelumDiassign, 100);
            });
        }
    }
})();
