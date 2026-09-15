/**
 * keberadaan_petugas.js
 * Modul Rekapitulasi & Monitoring Keberadaan Bangunan Usaha dan Keluarga
 * Sensus Ekonomi 2026 - BPS Provinsi Sulawesi Tengah
 */

(function () {
    'use strict';

    // State Variables
    window.keberadaanRole = 'Pencacah'; // 'Pencacah' | 'Pengawas'
    window.keberadaanView = 'compact';  // 'compact' | 'full'
    window.keberadaanMode = 'all';      // 'all' | 'bu_bar' | 'kl_bar' | 'tdk_dit' | 'selisih'
    window.keberadaanSearchQuery = '';
    window.keberadaanSortField = 'sls_count';
    window.keberadaanSortOrder = -1;
    window.keberadaanCurrentPage = 1;
    window.keberadaanPerPage = 25;
    window.lastKeberadaanFiltered = [];

    const KAB_NAMES = {
        '7201': '[01] Banggai Kepulauan',
        '7202': '[02] Banggai',
        '7203': '[03] Morowali',
        '7204': '[04] Poso',
        '7205': '[05] Donggala',
        '7206': '[06] Toli-Toli',
        '7207': '[07] Buol',
        '7208': '[08] Parigi Moutong',
        '7209': '[09] Tojo Una-Una',
        '7210': '[10] Sigi',
        '7211': '[11] Banggai Laut',
        '7212': '[12] Morowali Utara',
        '7271': '[71] Kota Palu'
    };

    function getPetugasName(email) {
        if (!email) return '-';
        const clean = email.trim().toLowerCase();
        if (window.MITRA_DATA && Array.isArray(window.MITRA_DATA)) {
            const found = window.MITRA_DATA.find(m => m.email && m.email.trim().toLowerCase() === clean);
            if (found && found.nama) return found.nama.trim();
        }
        if (window.userMap) {
            let mapped = window.userMap[clean] || window.userMap[clean.split('@')[0]];
            if (mapped) return mapped;
        }
        let userPart = clean.split('@')[0];
        return userPart.replace(/[._-]/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
    }

    function formatNumber(num) {
        return (Number(num) || 0).toLocaleString('id-ID');
    }

    // Role switcher
    window.setKeberadaanRole = function (role) {
        window.keberadaanRole = role;
        window.keberadaanCurrentPage = 1;

        const tabPencacah = document.getElementById('tab-keb-pencacah');
        const tabPengawas = document.getElementById('tab-keb-pengawas');
        if (tabPencacah && tabPengawas) {
            if (role === 'Pencacah') {
                tabPencacah.classList.add('active');
                tabPengawas.classList.remove('active');
            } else {
                tabPengawas.classList.add('active');
                tabPencacah.classList.remove('active');
            }
        }

        window.renderKeberadaanTable();
    };

    // View Mode switcher (compact vs full 13 statuses)
    window.setKeberadaanView = function (view) {
        window.keberadaanView = view;
        const btnCompact = document.getElementById('btn-keb-view-compact');
        const btnFull = document.getElementById('btn-keb-view-full');
        if (btnCompact && btnFull) {
            if (view === 'compact') {
                btnCompact.classList.add('active');
                btnFull.classList.remove('active');
            } else {
                btnFull.classList.add('active');
                btnCompact.classList.remove('active');
            }
        }
        window.renderKeberadaanTable();
    };

    // Mode filter pills
    window.setKeberadaanMode = function (mode) {
        window.keberadaanMode = mode;
        window.keberadaanCurrentPage = 1;

        const pills = [
            { id: 'pill-keb-all', key: 'all' },
            { id: 'pill-keb-bu', key: 'bu_bar' },
            { id: 'pill-keb-kl', key: 'kl_bar' },
            { id: 'pill-keb-tdk', key: 'tdk_dit' },
            { id: 'pill-keb-selisih', key: 'selisih' }
        ];

        pills.forEach(p => {
            const el = document.getElementById(p.id);
            if (el) {
                if (p.key === mode) {
                    el.classList.add('active');
                    if (p.key === 'selisih') {
                        el.style.background = '#ef4444';
                    } else if (p.key === 'tdk_dit') {
                        el.style.background = '#d97706';
                    } else {
                        el.style.background = 'var(--primary)';
                    }
                    el.style.color = '#ffffff';
                } else {
                    el.classList.remove('active');
                    if (p.key === 'selisih') {
                        el.style.background = 'rgba(239,68,68,0.06)';
                        el.style.color = '#dc2626';
                    } else if (p.key === 'tdk_dit') {
                        el.style.background = 'rgba(245,158,11,0.08)';
                        el.style.color = '#d97706';
                    } else {
                        el.style.background = 'var(--card-bg)';
                        el.style.color = 'var(--text-secondary)';
                    }
                }
            }
        });

        // Auto-set sort field if specific mode chosen
        if (mode === 'bu_bar') {
            window.keberadaanSortField = 'bu_bar';
            window.keberadaanSortOrder = -1;
        } else if (mode === 'kl_bar') {
            window.keberadaanSortField = 'kl_bar';
            window.keberadaanSortOrder = -1;
        } else if (mode === 'tdk_dit') {
            window.keberadaanSortField = 'tot_tdk';
            window.keberadaanSortOrder = -1;
        } else if (mode === 'selisih') {
            window.keberadaanSortField = 'anomali_count';
            window.keberadaanSortOrder = -1;
        }

        window.renderKeberadaanTable();
    };

    window.toggleKeberadaanSelisihOnly = function () {
        if (window.keberadaanMode === 'selisih') {
            window.setKeberadaanMode('all');
        } else {
            window.setKeberadaanMode('selisih');
        }
    };

    // Search input
    let searchTimer = null;
    window.handleKeberadaanSearch = function (val) {
        clearTimeout(searchTimer);
        searchTimer = setTimeout(() => {
            window.keberadaanSearchQuery = (val || '').trim().toLowerCase();
            window.keberadaanCurrentPage = 1;
            window.renderKeberadaanTable();
        }, 200);
    };

    // Sorting
    window.sortKeberadaan = function (field) {
        if (window.keberadaanSortField === field) {
            window.keberadaanSortOrder *= -1;
        } else {
            window.keberadaanSortField = field;
            window.keberadaanSortOrder = (field === 'name') ? 1 : -1;
        }
        window.renderKeberadaanTable();
    };

    // Pagination controls
    window.changeKeberadaanPerPage = function (val) {
        window.keberadaanPerPage = parseInt(val, 10) || 25;
        window.keberadaanCurrentPage = 1;
        window.renderKeberadaanTable();
    };

    window.changeKeberadaanPage = function (page) {
        window.keberadaanCurrentPage = page;
        window.renderKeberadaanTable();
    };

    // Dynamic Thead Renderer
    function renderTableHeader() {
        const thead = document.getElementById('keberadaan-table-head');
        if (!thead) return;

        const isFull = (window.keberadaanView === 'full');
        const sf = window.keberadaanSortField;
        const so = window.keberadaanSortOrder;

        function sortIcon(f) {
            if (sf !== f) return '';
            return `<span style="font-size:0.75rem; color:var(--primary); font-weight:800;">${so === 1 ? ' ▲' : ' ▼'}</span>`;
        }

        if (!isFull) {
            // COMPACT VIEW: Clean 15 columns with explicit Tidak Ditemukan
            thead.innerHTML = `
                <tr style="background: var(--bg-secondary, #f8fafc); border-bottom: 2px solid var(--card-border);">
                    <th style="width: 45px; text-align: center;">No</th>
                    <th style="text-align: left; min-width: 190px; cursor: pointer;" onclick="window.sortKeberadaan('name')">Nama Petugas ${sortIcon('name')}</th>
                    <th style="text-align: center; width: 70px; cursor: pointer;" onclick="window.sortKeberadaan('sls_count')">SLS ${sortIcon('sls_count')}</th>
                    <!-- Usaha -->
                    <th style="text-align: center; width: 85px; background: rgba(16,185,129,0.06); cursor: pointer;" onclick="window.sortKeberadaan('bu_dit')">U-Dit ${sortIcon('bu_dit')}</th>
                    <th style="text-align: center; width: 85px; background: rgba(16,185,129,0.06); cursor: pointer;" onclick="window.sortKeberadaan('bu_bar')">U-Baru ${sortIcon('bu_bar')}</th>
                    <th style="text-align: center; width: 95px; background: rgba(245,158,11,0.08); color: #d97706; cursor: pointer;" onclick="window.sortKeberadaan('bu_tdk')" title="Bangunan Usaha Tidak Ditemukan">U-Tdk Dit ${sortIcon('bu_tdk')}</th>
                    <th style="text-align: center; width: 95px; background: rgba(239,68,68,0.05); color: #dc2626; cursor: pointer;" onclick="window.sortKeberadaan('bu_nonaktif')" title="Tutup, Ganda, dan Kantor Pusat">U-Tutup/Lain ${sortIcon('bu_nonaktif')}</th>
                    <!-- Keluarga -->
                    <th style="text-align: center; width: 85px; background: rgba(59,130,246,0.06); cursor: pointer;" onclick="window.sortKeberadaan('kl_dit')">K-Dit ${sortIcon('kl_dit')}</th>
                    <th style="text-align: center; width: 85px; background: rgba(59,130,246,0.06); cursor: pointer;" onclick="window.sortKeberadaan('kl_bar')">K-Baru ${sortIcon('kl_bar')}</th>
                    <th style="text-align: center; width: 95px; background: rgba(245,158,11,0.08); color: #d97706; cursor: pointer;" onclick="window.sortKeberadaan('kl_tdk')" title="Keluarga Tidak Ditemukan">K-Tdk Dit ${sortIcon('kl_tdk')}</th>
                    <th style="text-align: center; width: 95px; background: rgba(59,130,246,0.06); cursor: pointer;" onclick="window.sortKeberadaan('kl_nonaktif')" title="Meninggal, Tidak Eligible, Tidak Dapat Ditemui, Khusus">K-Lain ${sortIcon('kl_nonaktif')}</th>
                    <!-- Audit & Totals -->
                    <th style="text-align: center; width: 90px; cursor: pointer;" onclick="window.sortKeberadaan('tot_status')">Tot Status ${sortIcon('tot_status')}</th>
                    <th style="text-align: center; width: 90px; cursor: pointer;" onclick="window.sortKeberadaan('tot_keb')">Tot Keb ${sortIcon('tot_keb')}</th>
                    <th style="text-align: center; width: 105px; cursor: pointer;" onclick="window.sortKeberadaan('selisih')">Selisih ${sortIcon('selisih')}</th>
                    <th style="text-align: center; width: 75px;">Aksi</th>
                </tr>
            `;
        } else {
            // FULL 13-STATUS VIEW: 2-level grouped header
            thead.innerHTML = `
                <tr style="background: var(--bg-secondary, #f8fafc); border-bottom: 1px solid var(--card-border);">
                    <th rowspan="2" style="width: 45px; text-align: center; vertical-align: middle;">No</th>
                    <th rowspan="2" style="text-align: left; min-width: 190px; vertical-align: middle; cursor: pointer;" onclick="window.sortKeberadaan('name')">Nama Petugas ${sortIcon('name')}</th>
                    <th rowspan="2" style="text-align: center; width: 65px; vertical-align: middle; cursor: pointer;" onclick="window.sortKeberadaan('sls_count')">SLS ${sortIcon('sls_count')}</th>
                    <!-- Usaha Group -->
                    <th colspan="6" style="text-align: center; background: rgba(16,185,129,0.12); color: #047857; font-weight: 800; border-left: 1px solid var(--border-light); border-right: 1px solid var(--border-light); font-size: 0.8rem; padding: 0.4rem;">BANGUNAN USAHA (6 KATEGORI)</th>
                    <!-- Keluarga Group -->
                    <th colspan="7" style="text-align: center; background: rgba(59,130,246,0.12); color: #1d4ed8; font-weight: 800; border-right: 1px solid var(--border-light); font-size: 0.8rem; padding: 0.4rem;">KELUARGA (7 KATEGORI)</th>
                    <!-- Audit Group -->
                    <th colspan="3" style="text-align: center; background: rgba(139,92,246,0.12); color: #6d28d9; font-weight: 800; border-right: 1px solid var(--border-light); font-size: 0.8rem; padding: 0.4rem;">REKONSILIASI</th>
                    <th rowspan="2" style="text-align: center; width: 75px; vertical-align: middle;">Aksi</th>
                </tr>
                <tr style="background: var(--bg-secondary, #f8fafc); border-bottom: 2px solid var(--card-border); font-size: 0.76rem;">
                    <!-- Usaha Sub-cols -->
                    <th style="text-align: center; width: 70px; background: rgba(16,185,129,0.06); cursor: pointer;" onclick="window.sortKeberadaan('bu_dit')">Ditemukan ${sortIcon('bu_dit')}</th>
                    <th style="text-align: center; width: 70px; background: rgba(16,185,129,0.06); cursor: pointer;" onclick="window.sortKeberadaan('bu_bar')">Baru ${sortIcon('bu_bar')}</th>
                    <th style="text-align: center; width: 75px; background: rgba(245,158,11,0.08); color: #d97706; cursor: pointer;" onclick="window.sortKeberadaan('bu_tdk')">Tdk Dit ${sortIcon('bu_tdk')}</th>
                    <th style="text-align: center; width: 65px; background: rgba(239,68,68,0.06); color: #dc2626; cursor: pointer;" onclick="window.sortKeberadaan('bu_tut')">Tutup ${sortIcon('bu_tut')}</th>
                    <th style="text-align: center; width: 65px; background: rgba(239,68,68,0.04); cursor: pointer;" onclick="window.sortKeberadaan('bu_gan')">Ganda ${sortIcon('bu_gan')}</th>
                    <th style="text-align: center; width: 65px; background: rgba(239,68,68,0.04); cursor: pointer;" onclick="window.sortKeberadaan('bu_pus')">Pusat ${sortIcon('bu_pus')}</th>
                    <!-- Keluarga Sub-cols -->
                    <th style="text-align: center; width: 70px; background: rgba(59,130,246,0.06); cursor: pointer;" onclick="window.sortKeberadaan('kl_dit')">Ditemukan ${sortIcon('kl_dit')}</th>
                    <th style="text-align: center; width: 70px; background: rgba(59,130,246,0.06); cursor: pointer;" onclick="window.sortKeberadaan('kl_bar')">Baru ${sortIcon('kl_bar')}</th>
                    <th style="text-align: center; width: 75px; background: rgba(245,158,11,0.08); color: #d97706; cursor: pointer;" onclick="window.sortKeberadaan('kl_tdk')">Tdk Dit ${sortIcon('kl_tdk')}</th>
                    <th style="text-align: center; width: 70px; background: rgba(59,130,246,0.04); cursor: pointer;" onclick="window.sortKeberadaan('kl_men')">Meninggal ${sortIcon('kl_men')}</th>
                    <th style="text-align: center; width: 70px; background: rgba(59,130,246,0.04); cursor: pointer;" onclick="window.sortKeberadaan('kl_tem')">Tdk Ditemui ${sortIcon('kl_tem')}</th>
                    <th style="text-align: center; width: 70px; background: rgba(59,130,246,0.04); cursor: pointer;" onclick="window.sortKeberadaan('kl_eli')">Tdk Eligible ${sortIcon('kl_eli')}</th>
                    <th style="text-align: center; width: 65px; background: rgba(59,130,246,0.04); cursor: pointer;" onclick="window.sortKeberadaan('kl_khu')">Khusus ${sortIcon('kl_khu')}</th>
                    <!-- Audit Sub-cols -->
                    <th style="text-align: center; width: 80px; cursor: pointer;" onclick="window.sortKeberadaan('tot_status')">Status ${sortIcon('tot_status')}</th>
                    <th style="text-align: center; width: 80px; cursor: pointer;" onclick="window.sortKeberadaan('tot_keb')">Keberadaan ${sortIcon('tot_keb')}</th>
                    <th style="text-align: center; width: 95px; cursor: pointer;" onclick="window.sortKeberadaan('selisih')">Selisih ${sortIcon('selisih')}</th>
                </tr>
            `;
        }
    }

    // Main Render Function
    window.renderKeberadaanTable = function () {
        const tbody = document.getElementById('keberadaan-table-body');
        if (!tbody) return;

        // Render appropriate header
        renderTableHeader();

        if (!window.DATA_KEBERADAAN_PETUGAS) {
            tbody.innerHTML = `<tr><td colspan="20" style="text-align: center; padding: 2rem; color: var(--text-secondary);">
                Data keberadaan belum dimuat. Pastikan file <code>data_keberadaan_petugas.js</code> telah tersedia.
            </td></tr>`;
            return;
        }

        // 1. Resolve active Wilayah filter from dashboard controls
        const kabFilter = document.getElementById('assign-sls-kab-filter')?.value || 'all';
        const kecFilter = document.getElementById('assign-sls-kec-filter')?.value || 'all';

        let resolvedKabPrefix = null;
        const kabPrefixMatch = kabFilter.match(/\[(\d+)\]/);
        if (kabPrefixMatch) resolvedKabPrefix = '72' + kabPrefixMatch[1];

        let resolvedKecPrefix = null;
        const kecPrefixMatch = kecFilter.match(/\[(\d+)\]/);
        if (kecPrefixMatch) {
            resolvedKecPrefix = kecPrefixMatch[1];
        }

        // Update Wilayah Badge
        const wilayahBadge = document.getElementById('keberadaan-wilayah-badge');
        if (wilayahBadge) {
            if (resolvedKabPrefix && KAB_NAMES[resolvedKabPrefix]) {
                let badgeText = KAB_NAMES[resolvedKabPrefix];
                if (kecFilter !== 'all' && kecFilter) badgeText += ' › ' + kecFilter;
                wilayahBadge.textContent = badgeText;
            } else {
                wilayahBadge.textContent = 'Provinsi Sulawesi Tengah (Semua Kab/Kota)';
            }
        }

        // 2. Compute Executive KPI Summary
        updateKeberadaanKPIs(resolvedKabPrefix, resolvedKecPrefix);

        // 3. Filter Petugas List
        const rawList = (window.keberadaanRole === 'Pengawas')
            ? (window.DATA_KEBERADAAN_PETUGAS.pengawas || [])
            : (window.DATA_KEBERADAAN_PETUGAS.pencacah || []);

        let filtered = rawList.map(p => {
            const name = getPetugasName(p.email);
            const bu_nonaktif = (p.bu_tut || 0) + (p.bu_gan || 0) + (p.bu_pus || 0);
            const kl_nonaktif = (p.kl_men || 0) + (p.kl_eli || 0) + (p.kl_tem || 0) + (p.kl_khu || 0);
            const tot_tdk = (p.bu_tdk || 0) + (p.kl_tdk || 0);

            return {
                ...p,
                name: name,
                bu_nonaktif: bu_nonaktif,
                kl_nonaktif: kl_nonaktif,
                tot_tdk: tot_tdk
            };
        });

        // Filter by Wilayah
        if (resolvedKabPrefix) {
            filtered = filtered.filter(p => {
                if (!p.kabs || !p.kabs.includes(resolvedKabPrefix)) return false;
                if (resolvedKecPrefix) {
                    const expectedKecPrefix = resolvedKabPrefix + resolvedKecPrefix;
                    return p.kecs && p.kecs.some(k => k.startsWith(expectedKecPrefix));
                }
                return true;
            });
        }

        // Filter by Search Query
        if (window.keberadaanSearchQuery) {
            const q = window.keberadaanSearchQuery;
            filtered = filtered.filter(p => {
                return (p.name && p.name.toLowerCase().includes(q)) ||
                       (p.email && p.email.toLowerCase().includes(q));
            });
        }

        // Filter by Mode
        if (window.keberadaanMode === 'bu_bar') {
            filtered = filtered.filter(p => (p.bu_bar || 0) > 0);
        } else if (window.keberadaanMode === 'kl_bar') {
            filtered = filtered.filter(p => (p.kl_bar || 0) > 0);
        } else if (window.keberadaanMode === 'tdk_dit') {
            filtered = filtered.filter(p => (p.tot_tdk || 0) > 0);
        } else if (window.keberadaanMode === 'selisih') {
            filtered = filtered.filter(p => (p.anomali_count || 0) > 0 || (p.selisih || 0) !== 0);
        }

        // 4. Sort
        const sf = window.keberadaanSortField;
        const so = window.keberadaanSortOrder;
        filtered.sort((a, b) => {
            let va = a[sf];
            let vb = b[sf];
            if (typeof va === 'string') {
                return so * (va.localeCompare(vb));
            }
            va = Number(va) || 0;
            vb = Number(vb) || 0;
            if (va !== vb) return so * (va - vb);
            return (b.sls_count || 0) - (a.sls_count || 0);
        });

        window.lastKeberadaanFiltered = filtered;

        // 5. Pagination
        const totalItems = filtered.length;
        const perPage = window.keberadaanPerPage;
        const totalPages = Math.max(1, Math.ceil(totalItems / perPage));
        if (window.keberadaanCurrentPage > totalPages) window.keberadaanCurrentPage = totalPages;
        const currentPage = window.keberadaanCurrentPage;

        const startIndex = (currentPage - 1) * perPage;
        const pageItems = filtered.slice(startIndex, startIndex + perPage);

        // Update Pagination Info
        const paginationInfo = document.getElementById('keberadaan-pagination-info');
        if (paginationInfo) {
            const startDisplay = totalItems === 0 ? 0 : startIndex + 1;
            const endDisplay = Math.min(startIndex + perPage, totalItems);
            paginationInfo.innerHTML = `Menampilkan <b>${startDisplay} - ${endDisplay}</b> dari <b>${formatNumber(totalItems)}</b> ${window.keberadaanRole}`;
        }

        // Update Pagination Buttons
        renderPaginationButtons(totalPages, currentPage);

        // 6. Render Table Rows
        const isFull = (window.keberadaanView === 'full');
        const colspanTotal = isFull ? 20 : 15;

        if (pageItems.length === 0) {
            tbody.innerHTML = `<tr><td colspan="${colspanTotal}" style="text-align: center; padding: 2.5rem; color: var(--text-secondary);">
                Tidak ada data ${window.keberadaanRole} yang cocok dengan filter.
            </td></tr>`;
            return;
        }

        let html = '';
        pageItems.forEach((p, idx) => {
            const rowNo = startIndex + idx + 1;
            const hasSelisih = (p.anomali_count > 0 || p.selisih !== 0);

            // Audit Badge
            let selisihBadge = '';
            if (p.selisih === 0 && p.anomali_count === 0) {
                selisihBadge = `<span class="badge" style="background: rgba(16,185,129,0.12); color: #059669; font-weight: 700; border: 1px solid rgba(16,185,129,0.25);">0 (Cocok)</span>`;
            } else {
                const diffStr = (p.selisih > 0) ? `+${p.selisih}` : `${p.selisih}`;
                selisihBadge = `<span class="badge" style="background: rgba(239,68,68,0.15); color: #dc2626; font-weight: 800; border: 1px solid rgba(239,68,68,0.3); font-family: monospace;" title="${p.anomali_count} SLS memiliki selisih">${diffStr} (${p.anomali_count} SLS)</span>`;
            }

            // Role Badge
            const roleBadge = (p.role === 'Pengawas')
                ? `<span class="badge" style="background: rgba(139,92,246,0.12); color: #7c3aed; font-size: 0.7rem; font-weight: 700; padding: 2px 6px;">PML</span>`
                : `<span class="badge" style="background: rgba(59,130,246,0.12); color: #2563eb; font-size: 0.7rem; font-weight: 700; padding: 2px 6px;">PPL</span>`;

            // Action Button
            const actionBtn = `
                <button class="btn btn-sm" onclick="window.openKeberadaanDetail('${p.email}', '${p.role}')" style="padding: 0.25rem 0.6rem; border-radius: 6px; font-size: 0.78rem; font-weight: 600; background: var(--bg-secondary); border: 1px solid var(--border-light); color: var(--text-primary); cursor: pointer; display: inline-flex; align-items: center; gap: 0.3rem;" title="Lihat rincian Sub-SLS">
                    <svg width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                    Detail
                </button>
            `;

            if (!isFull) {
                // COMPACT ROW
                const buTutupLainTitle = `Tutup: ${p.bu_tut || 0} | Ganda: ${p.bu_gan || 0} | Kantor Pusat: ${p.bu_pus || 0}`;
                const klLainTitle = `Meninggal: ${p.kl_men || 0} | Tdk Ditemui: ${p.kl_tem || 0} | Tdk Eligible: ${p.kl_eli || 0} | Khusus: ${p.kl_khu || 0}`;

                html += `
                <tr style="border-bottom: 1px solid var(--border-light, #e2e8f0); ${hasSelisih ? 'background: rgba(239,68,68,0.015);' : ''}">
                    <td style="text-align: center; color: var(--text-secondary); font-size: 0.8rem;">${rowNo}</td>
                    <td style="text-align: left;">
                        <div style="font-weight: 700; color: var(--text-primary); font-size: 0.88rem; display: flex; align-items: center; gap: 0.4rem;">
                            <span>${p.name}</span>
                            ${roleBadge}
                        </div>
                        <div style="font-size: 0.76rem; color: var(--text-secondary); margin-top: 1px; font-family: monospace;">${p.email}</div>
                    </td>
                    <td style="text-align: center;">
                        <span class="badge" style="background: var(--bg-secondary); color: var(--text-primary); font-weight: 700; padding: 3px 8px; border-radius: 6px; border: 1px solid var(--border-light);">${p.sls_count}</span>
                    </td>
                    <!-- Usaha -->
                    <td style="text-align: center; font-weight: 600; color: #047857; background: rgba(16,185,129,0.02);">${formatNumber(p.bu_dit)}</td>
                    <td style="text-align: center; background: rgba(16,185,129,0.02);">
                        <span class="badge" style="background: rgba(16,185,129,0.15); color: #059669; font-weight: 800;">+${formatNumber(p.bu_bar)}</span>
                    </td>
                    <td style="text-align: center; background: rgba(245,158,11,0.03);">
                        <span style="color: #d97706; font-weight: 700;">${formatNumber(p.bu_tdk)}</span>
                    </td>
                    <td style="text-align: center; color: #dc2626; cursor: help;" title="${buTutupLainTitle}">${formatNumber(p.bu_nonaktif)}</td>
                    <!-- Keluarga -->
                    <td style="text-align: center; font-weight: 600; color: #1d4ed8; background: rgba(59,130,246,0.02);">${formatNumber(p.kl_dit)}</td>
                    <td style="text-align: center; background: rgba(59,130,246,0.02);">
                        <span class="badge" style="background: rgba(59,130,246,0.15); color: #2563eb; font-weight: 800;">+${formatNumber(p.kl_bar)}</span>
                    </td>
                    <td style="text-align: center; background: rgba(245,158,11,0.03);">
                        <span style="color: #d97706; font-weight: 700;">${formatNumber(p.kl_tdk)}</span>
                    </td>
                    <td style="text-align: center; color: var(--text-secondary); cursor: help;" title="${klLainTitle}">${formatNumber(p.kl_nonaktif)}</td>
                    <!-- Totals & Audit -->
                    <td style="text-align: center; font-weight: 700; color: var(--text-primary);">${formatNumber(p.tot_status)}</td>
                    <td style="text-align: center; font-weight: 700; color: var(--text-primary);">${formatNumber(p.tot_keb)}</td>
                    <td style="text-align: center;">${selisihBadge}</td>
                    <td style="text-align: center;">${actionBtn}</td>
                </tr>`;
            } else {
                // FULL 13-STATUS ROW
                html += `
                <tr style="border-bottom: 1px solid var(--border-light, #e2e8f0); ${hasSelisih ? 'background: rgba(239,68,68,0.015);' : ''}">
                    <td style="text-align: center; color: var(--text-secondary); font-size: 0.8rem;">${rowNo}</td>
                    <td style="text-align: left;">
                        <div style="font-weight: 700; color: var(--text-primary); font-size: 0.86rem; display: flex; align-items: center; gap: 0.4rem;">
                            <span>${p.name}</span>
                            ${roleBadge}
                        </div>
                        <div style="font-size: 0.74rem; color: var(--text-secondary); margin-top: 1px; font-family: monospace;">${p.email}</div>
                    </td>
                    <td style="text-align: center;">
                        <span class="badge" style="background: var(--bg-secondary); color: var(--text-primary); font-weight: 700; padding: 2px 6px; border-radius: 6px; border: 1px solid var(--border-light); font-size: 0.78rem;">${p.sls_count}</span>
                    </td>
                    <!-- Usaha 6 cols -->
                    <td style="text-align: center; font-weight: 600; color: #047857; background: rgba(16,185,129,0.02);">${formatNumber(p.bu_dit)}</td>
                    <td style="text-align: center; background: rgba(16,185,129,0.02); font-weight: 700; color: #059669;">+${formatNumber(p.bu_bar)}</td>
                    <td style="text-align: center; background: rgba(245,158,11,0.04); font-weight: 700; color: #d97706;">${formatNumber(p.bu_tdk)}</td>
                    <td style="text-align: center; color: #dc2626;">${formatNumber(p.bu_tut)}</td>
                    <td style="text-align: center; color: var(--text-secondary);">${formatNumber(p.bu_gan)}</td>
                    <td style="text-align: center; color: var(--text-secondary);">${formatNumber(p.bu_pus)}</td>
                    <!-- Keluarga 7 cols -->
                    <td style="text-align: center; font-weight: 600; color: #1d4ed8; background: rgba(59,130,246,0.02);">${formatNumber(p.kl_dit)}</td>
                    <td style="text-align: center; background: rgba(59,130,246,0.02); font-weight: 700; color: #2563eb;">+${formatNumber(p.kl_bar)}</td>
                    <td style="text-align: center; background: rgba(245,158,11,0.04); font-weight: 700; color: #d97706;">${formatNumber(p.kl_tdk)}</td>
                    <td style="text-align: center; color: var(--text-secondary);">${formatNumber(p.kl_men)}</td>
                    <td style="text-align: center; color: var(--text-secondary);">${formatNumber(p.kl_tem)}</td>
                    <td style="text-align: center; color: var(--text-secondary);">${formatNumber(p.kl_eli)}</td>
                    <td style="text-align: center; color: var(--text-secondary);">${formatNumber(p.kl_khu)}</td>
                    <!-- Rekonsiliasi 3 cols -->
                    <td style="text-align: center; font-weight: 700; color: var(--text-primary);">${formatNumber(p.tot_status)}</td>
                    <td style="text-align: center; font-weight: 700; color: var(--text-primary);">${formatNumber(p.tot_keb)}</td>
                    <td style="text-align: center;">${selisihBadge}</td>
                    <td style="text-align: center;">${actionBtn}</td>
                </tr>`;
            }
        });

        tbody.innerHTML = html;
    };

    // Update KPI Summary Cards
    function updateKeberadaanKPIs(resolvedKabPrefix, resolvedKecPrefix) {
        if (!window.DATA_KEBERADAAN_PETUGAS) return;

        let summary = null;
        if (!resolvedKabPrefix || resolvedKabPrefix === 'all') {
            summary = window.DATA_KEBERADAAN_PETUGAS.summary_prov;
        } else if (!resolvedKecPrefix && window.DATA_KEBERADAAN_PETUGAS.summary_kab && window.DATA_KEBERADAAN_PETUGAS.summary_kab[resolvedKabPrefix]) {
            summary = window.DATA_KEBERADAAN_PETUGAS.summary_kab[resolvedKabPrefix];
        } else {
            // Aggregate from active pencacah in that kec
            const list = window.DATA_KEBERADAAN_PETUGAS.pencacah || [];
            const tempSum = {
                bu_dit: 0, bu_bar: 0, bu_tdk: 0, bu_tut: 0, bu_gan: 0, bu_pus: 0,
                kl_dit: 0, kl_bar: 0, kl_tdk: 0, kl_men: 0, kl_eli: 0, kl_tem: 0, kl_khu: 0,
                tot_status: 0, tot_keb: 0, selisih: 0, anomali_sls: 0, sls_count: 0
            };
            list.forEach(p => {
                if (resolvedKabPrefix && (!p.kabs || !p.kabs.includes(resolvedKabPrefix))) return;
                if (resolvedKecPrefix) {
                    const expected = resolvedKabPrefix + resolvedKecPrefix;
                    if (!p.kecs || !p.kecs.some(k => k.startsWith(expected))) return;
                }
                tempSum.bu_dit += p.bu_dit;
                tempSum.bu_bar += p.bu_bar;
                tempSum.bu_tdk += p.bu_tdk;
                tempSum.bu_tut += p.bu_tut;
                tempSum.bu_gan += p.bu_gan;
                tempSum.bu_pus += p.bu_pus;
                tempSum.kl_dit += p.kl_dit;
                tempSum.kl_bar += p.kl_bar;
                tempSum.kl_tdk += p.kl_tdk;
                tempSum.kl_men += p.kl_men;
                tempSum.kl_eli += p.kl_eli;
                tempSum.kl_tem += p.kl_tem;
                tempSum.kl_khu += p.kl_khu;
                tempSum.tot_status += p.tot_status;
                tempSum.tot_keb += p.tot_keb;
                tempSum.selisih += p.selisih;
                tempSum.anomali_sls += p.anomali_count;
                tempSum.sls_count += p.sls_count;
            });
            summary = tempSum;
        }

        if (!summary) return;

        const usahaAktif = (summary.bu_dit || 0) + (summary.bu_bar || 0);
        const usahaNonAktif = (summary.bu_tdk || 0) + (summary.bu_tut || 0) + (summary.bu_gan || 0) + (summary.bu_pus || 0);
        const kelAktif = (summary.kl_dit || 0) + (summary.kl_bar || 0);
        const kelNonAktif = (summary.kl_tdk || 0) + (summary.kl_men || 0) + (summary.kl_eli || 0) + (summary.kl_tem || 0) + (summary.kl_khu || 0);

        const totalSls = summary.sls_count || 1;
        const anomaliSls = summary.anomali_sls || 0;
        const matchPct = (((totalSls - anomaliSls) / totalSls) * 100).toFixed(1);

        const elUaktif = document.getElementById('keb-kpi-usaha-aktif');
        if (elUaktif) elUaktif.textContent = formatNumber(usahaAktif);
        const elUdit = document.getElementById('keb-kpi-bu-dit');
        if (elUdit) elUdit.textContent = formatNumber(summary.bu_dit);
        const elUbar = document.getElementById('keb-kpi-bu-bar');
        if (elUbar) elUbar.textContent = '+' + formatNumber(summary.bu_bar);

        const elUnon = document.getElementById('keb-kpi-usaha-nonaktif');
        if (elUnon) elUnon.textContent = formatNumber(usahaNonAktif);
        const elUtdk = document.getElementById('keb-kpi-bu-tdk');
        if (elUtdk) elUtdk.textContent = formatNumber(summary.bu_tdk);
        const elUtut = document.getElementById('keb-kpi-bu-tut');
        if (elUtut) elUtut.textContent = formatNumber(summary.bu_tut);

        const elKaktif = document.getElementById('keb-kpi-keluarga-aktif');
        if (elKaktif) elKaktif.textContent = formatNumber(kelAktif);
        const elKdit = document.getElementById('keb-kpi-kl-dit');
        if (elKdit) elKdit.textContent = formatNumber(summary.kl_dit);
        const elKbar = document.getElementById('keb-kpi-kl-bar');
        if (elKbar) elKbar.textContent = '+' + formatNumber(summary.kl_bar);

        const elKnon = document.getElementById('keb-kpi-keluarga-anomali');
        if (elKnon) elKnon.textContent = formatNumber(kelNonAktif);
        const elKtdk = document.getElementById('keb-kpi-kl-tdk');
        if (elKtdk) elKtdk.textContent = formatNumber(summary.kl_tdk);
        const elKmen = document.getElementById('keb-kpi-kl-men');
        if (elKmen) elKmen.textContent = formatNumber(summary.kl_men);

        const elAuditRate = document.getElementById('keb-kpi-audit-rate');
        if (elAuditRate) elAuditRate.textContent = matchPct + '%';
        const elAnomaliCount = document.getElementById('keb-kpi-anomali-count');
        if (elAnomaliCount) elAnomaliCount.textContent = `${formatNumber(anomaliSls)} SLS Selisih`;
    }

    // Render Pagination Buttons
    function renderPaginationButtons(totalPages, currentPage) {
        const container = document.getElementById('keberadaan-pagination-buttons');
        if (!container) return;

        if (totalPages <= 1) {
            container.innerHTML = '';
            return;
        }

        let btns = '';

        // Prev
        btns += `<button class="btn btn-sm" onclick="window.changeKeberadaanPage(${currentPage - 1})" ${currentPage === 1 ? 'disabled style="opacity:0.4; cursor:not-allowed;"' : 'style="cursor:pointer;"'} style="padding: 0.25rem 0.5rem; border-radius: 4px; border: 1px solid var(--border-light); background: var(--card-bg); color: var(--text-primary); font-size: 0.8rem;">‹</button>`;

        // Pages with ellipsis
        const range = [];
        for (let i = 1; i <= totalPages; i++) {
            if (i === 1 || i === totalPages || (i >= currentPage - 2 && i <= currentPage + 2)) {
                range.push(i);
            }
        }

        let l = null;
        for (let i of range) {
            if (l) {
                if (i - l === 2) {
                    const mid = l + 1;
                    btns += `<button class="btn btn-sm" onclick="window.changeKeberadaanPage(${mid})" style="padding: 0.25rem 0.55rem; border-radius: 4px; border: 1px solid var(--border-light); background: var(--card-bg); color: var(--text-primary); font-size: 0.8rem;">${mid}</button>`;
                } else if (i - l !== 1) {
                    btns += `<span style="padding: 0.25rem; color: var(--text-secondary); font-size: 0.8rem;">...</span>`;
                }
            }
            const isActive = (i === currentPage);
            btns += `<button class="btn btn-sm" onclick="window.changeKeberadaanPage(${i})" style="padding: 0.25rem 0.55rem; border-radius: 4px; border: 1px solid ${isActive ? 'var(--primary)' : 'var(--border-light)'}; background: ${isActive ? 'var(--primary)' : 'var(--card-bg)'}; color: ${isActive ? '#ffffff' : 'var(--text-primary)'}; font-weight: ${isActive ? '700' : '500'}; font-size: 0.8rem;">${i}</button>`;
            l = i;
        }

        // Next
        btns += `<button class="btn btn-sm" onclick="window.changeKeberadaanPage(${currentPage + 1})" ${currentPage === totalPages ? 'disabled style="opacity:0.4; cursor:not-allowed;"' : 'style="cursor:pointer;"'} style="padding: 0.25rem 0.5rem; border-radius: 4px; border: 1px solid var(--border-light); background: var(--card-bg); color: var(--text-primary); font-size: 0.8rem;">›</button>`;

        container.innerHTML = btns;
    }

    // Modal SLS Drill-down
    window.openKeberadaanDetail = function (email, role) {
        if (!window.DATA_KEBERADAAN_PETUGAS) return;

        const roleKey = (role === 'Pengawas') ? 'pengawas' : 'pencacah';
        const list = window.DATA_KEBERADAAN_PETUGAS[roleKey] || [];
        const petugas = list.find(p => p.email.toLowerCase() === email.toLowerCase());

        if (!petugas) {
            alert('Data detail petugas tidak ditemukan.');
            return;
        }

        const modal = document.getElementById('keberadaan-sls-modal');
        const title = document.getElementById('keberadaan-modal-title');
        const subtitle = document.getElementById('keberadaan-modal-subtitle');
        const summaryBar = document.getElementById('keberadaan-modal-summary-bar');
        const tbody = document.getElementById('keberadaan-modal-tbody');
        const footerNote = document.getElementById('keberadaan-modal-footer-note');

        if (!modal || !tbody) return;

        const name = getPetugasName(petugas.email);
        title.innerHTML = `<span>Detail Sub-SLS: <b>${name}</b></span> <span class="badge" style="background: rgba(99,102,241,0.15); color: #6366f1; font-size: 0.75rem; font-weight: 700;">${petugas.role}</span>`;

        const kabListStr = (petugas.kabs || []).map(k => KAB_NAMES[k] || k).join(', ') || '-';
        subtitle.textContent = `Email: ${petugas.email} | Wilayah: ${kabListStr} | Total ${petugas.sls_count} Sub-SLS Ditugaskan`;

        // Summary Bar in modal with explicit Tidak Ditemukan & all categories
        if (summaryBar) {
            const selisihColor = (petugas.selisih === 0) ? '#059669' : '#dc2626';

            summaryBar.innerHTML = `
                <div style="flex: 1 1 100%; display: flex; gap: 1rem; flex-wrap: wrap; justify-content: space-between; align-items: center;">
                    <div style="display: flex; gap: 0.75rem; flex-wrap: wrap;">
                        <span>🏬 <b>Usaha:</b> Dit: <b>${formatNumber(petugas.bu_dit)}</b> | Baru: <b style="color:#059669;">+${formatNumber(petugas.bu_bar)}</b> | <b style="color:#d97706;">Tdk Dit: ${formatNumber(petugas.bu_tdk)}</b> | Tutup: ${formatNumber(petugas.bu_tut)} | Ganda: ${formatNumber(petugas.bu_gan)} | Pusat: ${formatNumber(petugas.bu_pus)}</span>
                    </div>
                </div>
                <div style="flex: 1 1 100%; display: flex; gap: 1rem; flex-wrap: wrap; justify-content: space-between; align-items: center; margin-top: 0.25rem;">
                    <div style="display: flex; gap: 0.75rem; flex-wrap: wrap;">
                        <span>👨‍👩‍👧‍👦 <b>Keluarga:</b> Dit: <b>${formatNumber(petugas.kl_dit)}</b> | Baru: <b style="color:#2563eb;">+${formatNumber(petugas.kl_bar)}</b> | <b style="color:#d97706;">Tdk Dit: ${formatNumber(petugas.kl_tdk)}</b> | Men: ${formatNumber(petugas.kl_men)} | Tdk Ditemui: ${formatNumber(petugas.kl_tem)} | Tdk Eli: ${formatNumber(petugas.kl_eli)} | Khusus: ${formatNumber(petugas.kl_khu)}</span>
                    </div>
                    <div>
                        <span>⚖️ <b>Audit:</b> Status: <b>${formatNumber(petugas.tot_status)}</b> | Keb: <b>${formatNumber(petugas.tot_keb)}</b> | Selisih: <b style="color:${selisihColor};">${petugas.selisih} (${petugas.anomali_count} SLS)</b></span>
                    </div>
                </div>
            `;
        }

        // SLS Table Rows
        // Format of sls record:
        // [sls, sub, bu_dit, bu_bar, bu_tdk, bu_tut, bu_gan, bu_pus, kl_dit, kl_bar, kl_tdk, kl_men, kl_eli, kl_tem, kl_khu, status_sum, tot_keb, selisih]
        const slsList = petugas.sls || [];
        let rowsHtml = '';

        slsList.forEach((r, idx) => {
            const slsCode = r[0] || '';
            const subCode = r[1] || '';
            const buDit = r[2] || 0;
            const buBar = r[3] || 0;
            const buTdk = r[4] || 0;
            const buTut = r[5] || 0;
            const buGan = r[6] || 0;
            const buPus = r[7] || 0;

            const klDit = r[8] || 0;
            const klBar = r[9] || 0;
            const klTdk = r[10] || 0;
            const klMen = r[11] || 0;
            const klEli = r[12] || 0;
            const klTem = r[13] || 0;
            const klKhu = r[14] || 0;

            const statusSum = r[15] || 0;
            const totKeb = r[16] || 0;
            const sel = r[17] || 0;

            const isAnomali = (sel !== 0);

            // Grouped compact columns for modal table
            const buTutupLain = buTut + buGan + buPus;
            const buTutupTooltip = `Tutup: ${buTut} | Ganda: ${buGan} | Pusat: ${buPus}`;

            const klLain = klMen + klEli + klTem + klKhu;
            const klLainTooltip = `Meninggal: ${klMen} | Tdk Ditemui: ${klTem} | Tdk Eligible: ${klEli} | Khusus: ${klKhu}`;

            // Nice format for SLS: 72010300070001 -> 72.01.030.007 0001
            let formattedSls = slsCode;
            if (slsCode.length === 14) {
                formattedSls = `${slsCode.slice(0, 2)}.${slsCode.slice(2, 4)}.${slsCode.slice(4, 7)}.${slsCode.slice(7, 10)} ${slsCode.slice(10, 14)}`;
            }

            rowsHtml += `
            <tr style="border-bottom: 1px solid var(--border-light); ${isAnomali ? 'background: rgba(239,68,68,0.035);' : ''}">
                <td style="padding:0.6rem; text-align:center; color:var(--text-secondary);">${idx + 1}</td>
                <td style="padding:0.6rem 0.8rem; text-align:left;">
                    <div style="font-weight:700; font-family:monospace; color:var(--text-primary); font-size:0.86rem;">${formattedSls}</div>
                    <div style="font-size:0.75rem; color:var(--text-secondary);">Sub-SLS: <span class="badge" style="background:var(--bg-secondary); border:1px solid var(--border-light); font-weight:700;">${subCode}</span></div>
                </td>
                <!-- Usaha -->
                <td style="padding:0.6rem 0.5rem; text-align:center; font-weight:600; color:#047857; background:rgba(16,185,129,0.02);">${buDit}</td>
                <td style="padding:0.6rem 0.5rem; text-align:center; background:rgba(16,185,129,0.02);">
                    <span style="color:#059669; font-weight:700;">+${buBar}</span>
                </td>
                <td style="padding:0.6rem 0.5rem; text-align:center; background:rgba(245,158,11,0.04); font-weight:700; color:#d97706;">${buTdk}</td>
                <td style="padding:0.6rem 0.5rem; text-align:center; color:#dc2626; cursor:help;" title="${buTutupTooltip}">${buTutupLain}</td>
                <!-- Keluarga -->
                <td style="padding:0.6rem 0.5rem; text-align:center; font-weight:600; color:#1d4ed8; background:rgba(59,130,246,0.02);">${klDit}</td>
                <td style="padding:0.6rem 0.5rem; text-align:center; background:rgba(59,130,246,0.02);">
                    <span style="color:#2563eb; font-weight:700;">+${klBar}</span>
                </td>
                <td style="padding:0.6rem 0.5rem; text-align:center; background:rgba(245,158,11,0.04); font-weight:700; color:#d97706;">${klTdk}</td>
                <td style="padding:0.6rem 0.5rem; text-align:center; color:var(--text-secondary); cursor:help;" title="${klLainTooltip}">${klLain}</td>
                <!-- Totals & Audit -->
                <td style="padding:0.6rem 0.5rem; text-align:center; font-weight:700; color:var(--text-primary);">${statusSum}</td>
                <td style="padding:0.6rem 0.5rem; text-align:center; font-weight:700; color:var(--text-primary);">${totKeb}</td>
                <td style="padding:0.6rem 0.5rem; text-align:center;">
                    ${isAnomali ? `<span class="badge" style="background: rgba(239,68,68,0.15); color: #dc2626; font-weight: 800; font-family: monospace;">${sel > 0 ? '+' + sel : sel}</span>` : `<span class="badge" style="background: rgba(16,185,129,0.12); color: #059669; font-weight: 700;">0</span>`}
                </td>
            </tr>`;
        });

        tbody.innerHTML = rowsHtml;

        if (footerNote) {
            footerNote.textContent = `Menampilkan ${slsList.length} Sub-SLS. Arahkan kursor pada angka U-Tutup/Lain atau K-Lain untuk melihat rincian Tutup, Ganda, Meninggal, dll.`;
        }

        modal.style.display = 'flex';
    };

    // Export Excel (.xlsx) with ALL 13 categories
    window.exportKeberadaanExcel = function () {
        if (typeof XLSX === 'undefined') {
            alert('Library SheetJS (XLSX) belum dimuat.');
            return;
        }

        const data = window.lastKeberadaanFiltered || [];
        if (data.length === 0) {
            alert('Tidak ada data untuk diekspor.');
            return;
        }

        const headers = [
            'No', 'Nama Petugas', 'Email', 'Role', 'Kabupaten', 'Jml SLS',
            // Usaha
            'Usaha Ditemukan', 'Usaha Baru', 'Usaha Tidak Ditemukan', 'Usaha Tutup', 'Usaha Ganda', 'Usaha Kantor Pusat',
            'Total Usaha Aktif', 'Total Usaha Semua',
            // Keluarga
            'Keluarga Ditemukan', 'Keluarga Baru', 'Keluarga Tidak Ditemukan', 'Keluarga Meninggal', 'Keluarga Tdk Eligible', 'Keluarga Tdk Ditemui', 'Keluarga Khusus',
            'Total Keluarga Aktif', 'Total Keluarga Semua',
            // Audit
            'Total Status', 'Total Keberadaan', 'Selisih Audit', 'Status Sinkron'
        ];

        const rows = data.map((p, idx) => {
            const kabStr = (p.kabs || []).map(k => KAB_NAMES[k] || k).join(', ');
            const uAktif = (p.bu_dit || 0) + (p.bu_bar || 0);
            const uAll = uAktif + (p.bu_tdk || 0) + (p.bu_tut || 0) + (p.bu_gan || 0) + (p.bu_pus || 0);
            const kAktif = (p.kl_dit || 0) + (p.kl_bar || 0);
            const kAll = kAktif + (p.kl_tdk || 0) + (p.kl_men || 0) + (p.kl_eli || 0) + (p.kl_tem || 0) + (p.kl_khu || 0);
            const statusSync = (p.selisih === 0 && p.anomali_count === 0) ? 'Cocok' : `Selisih (${p.anomali_count} SLS)`;

            return [
                idx + 1,
                p.name,
                p.email,
                p.role,
                kabStr,
                p.sls_count,
                // Usaha
                p.bu_dit || 0,
                p.bu_bar || 0,
                p.bu_tdk || 0,
                p.bu_tut || 0,
                p.bu_gan || 0,
                p.bu_pus || 0,
                uAktif,
                uAll,
                // Keluarga
                p.kl_dit || 0,
                p.kl_bar || 0,
                p.kl_tdk || 0,
                p.kl_men || 0,
                p.kl_eli || 0,
                p.kl_tem || 0,
                p.kl_khu || 0,
                kAktif,
                kAll,
                // Audit
                p.tot_status || 0,
                p.tot_keb || 0,
                p.selisih || 0,
                statusSync
            ];
        });

        const wb = XLSX.utils.book_new();
        const ws = XLSX.utils.aoa_to_sheet([headers, ...rows]);

        // Auto column widths
        ws['!cols'] = headers.map(() => ({ wch: 16 }));
        ws['!cols'][1] = { wch: 28 }; // Name
        ws['!cols'][2] = { wch: 30 }; // Email
        ws['!cols'][4] = { wch: 24 }; // Kab

        XLSX.utils.book_append_sheet(wb, ws, 'Keberadaan ' + window.keberadaanRole);

        const ts = new Date().toISOString().slice(0, 10);
        XLSX.writeFile(wb, `Rekap_Keberadaan_Lengkap_${window.keberadaanRole}_${ts}.xlsx`);
    };

    // Export CSV with ALL 13 categories
    window.exportKeberadaanCSV = function () {
        const data = window.lastKeberadaanFiltered || [];
        if (data.length === 0) {
            alert('Tidak ada data untuk diekspor.');
            return;
        }

        const headers = [
            'No', 'Nama Petugas', 'Email', 'Role', 'Kabupaten', 'Jml SLS',
            'Usaha Ditemukan', 'Usaha Baru', 'Usaha Tidak Ditemukan', 'Usaha Tutup', 'Usaha Ganda', 'Usaha Kantor Pusat', 'Total Usaha Aktif',
            'Keluarga Ditemukan', 'Keluarga Baru', 'Keluarga Tidak Ditemukan', 'Keluarga Meninggal', 'Keluarga Tdk Eligible', 'Keluarga Tdk Ditemui', 'Keluarga Khusus', 'Total Keluarga Aktif',
            'Total Status', 'Total Keberadaan', 'Selisih Audit'
        ];

        let csv = '\uFEFF' + headers.join(',') + '\n';
        data.forEach((p, idx) => {
            const kabStr = '"' + (p.kabs || []).map(k => KAB_NAMES[k] || k).join('; ') + '"';
            const nameStr = '"' + (p.name || '').replace(/"/g, '""') + '"';
            const uAktif = (p.bu_dit || 0) + (p.bu_bar || 0);
            const kAktif = (p.kl_dit || 0) + (p.kl_bar || 0);

            const row = [
                idx + 1,
                nameStr,
                p.email,
                p.role,
                kabStr,
                p.sls_count,
                p.bu_dit || 0,
                p.bu_bar || 0,
                p.bu_tdk || 0,
                p.bu_tut || 0,
                p.bu_gan || 0,
                p.bu_pus || 0,
                uAktif,
                p.kl_dit || 0,
                p.kl_bar || 0,
                p.kl_tdk || 0,
                p.kl_men || 0,
                p.kl_eli || 0,
                p.kl_tem || 0,
                p.kl_khu || 0,
                kAktif,
                p.tot_status || 0,
                p.tot_keb || 0,
                p.selisih || 0
            ];
            csv += row.join(',') + '\n';
        });

        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        const ts = new Date().toISOString().slice(0, 10);
        link.setAttribute('href', url);
        link.setAttribute('download', `Rekap_Keberadaan_Lengkap_${window.keberadaanRole}_${ts}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    // Initialize automatically when DOM is ready
    document.addEventListener('DOMContentLoaded', () => {
        if (window.granularSummaryView === 'keberadaan') {
            window.renderKeberadaanTable();
        }
    });

})();
