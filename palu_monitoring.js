/**
 * palu_monitoring.js - Monitoring Terpadu Khusus Kota Palu
 * Memetakan dokumen OPEN, DRAFT, Bangunan Kosong, dan Tidak Ditemukan
 * pada 1.482 SLS Kota Palu dengan batas spasial resmi dan citra satelit.
 */

(function () {
    let paluMap = null;
    let paluGeoLayer = null;
    let selectedLayer = null;
    let currentMode = 'open'; // 'open', 'draft', 'tidak_ditemukan', 'bangkos', 'all'
    let currentAreaFilter = 'all'; // 'all', 'tondo', 'lasoani', 'kawatuna', 'merpati_maleo'
    let searchQuery = '';
    let sortField = 'open';
    let sortOrder = -1; // DESC
    let currentPage = 1;
    let perPage = 25;
    let filteredFeatures = [];
    let currentTableView = 'usaha'; // 'usaha' | 'sls'

    // Usaha table state (separate from SLS state)
    let usahaSearchQuery = '';
    let usahaPage = 1;
    let usahaPerPage = 25;
    let usahaKategoriFilter = ''; // '' | 'tidak_ditemukan' | 'nonaktif'
    let filteredUsaha = [];

    // Basemaps
    let esriTile = null;
    let osmTile = null;

    window.initPaluMonitoring = function () {
        const container = document.getElementById('palu-monitoring-map');
        if (!container) return;

        if (!paluMap) {
            esriTile = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
                attribution: '&copy; Esri World Imagery',
                maxZoom: 19
            });
            osmTile = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; OpenStreetMap',
                maxZoom: 19
            });

            paluMap = L.map('palu-monitoring-map', {
                center: [-0.8917, 119.8707],
                zoom: 13,
                layers: [esriTile],
                zoomControl: true
            });

            // Re-render layers on map ready
            renderPaluMapLayers();
        } else {
            setTimeout(() => {
                paluMap.invalidateSize();
            }, 200);
        }

        updatePaluSummaryCards();
        // Default: show unit usaha view
        window.setPaluTableView(currentTableView);
    };

    // Update Summary KPI Cards
    function updatePaluSummaryCards() {
        if (!window.PALU_MONITORING_DATA || !window.PALU_MONITORING_DATA.summary) return;
        const s = window.PALU_MONITORING_DATA.summary;

        const elOpen = document.getElementById('palu-kpi-open');
        if (elOpen) elOpen.textContent = (s.open || 0).toLocaleString('id-ID');
        const elOpenSls = document.getElementById('palu-kpi-open-sls');
        if (elOpenSls) elOpenSls.textContent = `${(s.open_sls || 0).toLocaleString('id-ID')} SLS`;

        const elDraft = document.getElementById('palu-kpi-draft');
        if (elDraft) elDraft.textContent = (s.draft || 0).toLocaleString('id-ID');
        const elDraftSls = document.getElementById('palu-kpi-draft-sls');
        if (elDraftSls) elDraftSls.textContent = `${(s.draft_sls || 0).toLocaleString('id-ID')} SLS`;

        const elBangkos = document.getElementById('palu-kpi-bangkos');
        if (elBangkos) elBangkos.textContent = (s.bangkos || 0).toLocaleString('id-ID');
        const elBangkosSls = document.getElementById('palu-kpi-bangkos-sls');
        if (elBangkosSls) elBangkosSls.textContent = `${(s.bangkos_sls || 0).toLocaleString('id-ID')} SLS`;

        const totalTdk = (s.bu_tdk || 0) + (s.kl_tdk || 0);
        const elTdk = document.getElementById('palu-kpi-tdk');
        if (elTdk) elTdk.textContent = totalTdk.toLocaleString('id-ID');
        const elTdkDetail = document.getElementById('palu-kpi-tdk-detail');
        if (elTdkDetail) elTdkDetail.textContent = `Keluarga: ${(s.kl_tdk || 0).toLocaleString('id-ID')} | Usaha: ${(s.bu_tdk || 0).toLocaleString('id-ID')}`;
    }

    // Basemap toggle
    window.setPaluBasemap = function (type) {
        if (!paluMap) return;
        if (type === 'satellite') {
            if (osmTile) paluMap.removeLayer(osmTile);
            if (esriTile) paluMap.addLayer(esriTile);
        } else {
            if (esriTile) paluMap.removeLayer(esriTile);
            if (osmTile) paluMap.addLayer(osmTile);
        }
        document.querySelectorAll('.btn-palu-basemap').forEach(b => {
            b.classList.toggle('active', b.getAttribute('data-base') === type);
        });
    };

    // Mode switch: 'open', 'draft', 'tidak_ditemukan', 'bangkos', 'all'
    window.setPaluMapMode = function (mode) {
        currentMode = mode;
        document.querySelectorAll('.btn-palu-mode').forEach(b => {
            b.classList.toggle('active', b.getAttribute('data-mode') === mode);
        });

        // Set default sorting based on mode
        if (mode === 'open') {
            sortField = 'open';
            sortOrder = -1;
        } else if (mode === 'draft') {
            sortField = 'draft';
            sortOrder = -1;
        } else if (mode === 'tidak_ditemukan') {
            sortField = 'tot_tdk';
            sortOrder = -1;
        } else if (mode === 'bangkos') {
            sortField = 'bangkos';
            sortOrder = -1;
        }

        renderPaluMapLayers();
        window.renderPaluTable();
    };

    // Quick Focus Areas (1-Klik Focus)
    window.focusPaluArea = function (areaKey) {
        currentAreaFilter = areaKey;
        currentPage = 1;

        document.querySelectorAll('.btn-palu-area-pill').forEach(b => {
            b.classList.toggle('active', b.getAttribute('data-area') === areaKey);
        });

        renderPaluMapLayers();
        window.renderPaluTable();

        // Fit map bounds to the focused area
        if (paluGeoLayer && paluMap) {
            const bounds = L.latLngBounds([]);
            paluGeoLayer.eachLayer(layer => {
                const p = layer.feature.properties;
                if (matchesArea(p, areaKey)) {
                    bounds.extend(layer.getBounds());
                }
            });
            if (bounds.isValid()) {
                paluMap.fitBounds(bounds, { padding: [50, 50], maxZoom: 16 });
            }
        }
    };

    function matchesArea(p, areaKey) {
        if (!areaKey || areaKey === 'all') return true;
        const desa = (p.nmdesa || '').toUpperCase();
        if (areaKey === 'tondo') return desa.includes('TONDO');
        if (areaKey === 'lasoani') return desa.includes('LASOANI');
        if (areaKey === 'kawatuna') return desa.includes('KAWATUNA');
        if (areaKey === 'merpati_maleo') return desa.includes('TANAMODINDI');
        return true;
    }

    // Map Styling Rule: Hanya menyorot SLS yang memiliki isu/target, SLS normal dibuat transparan bersih
    function getFeatureStyle(feature) {
        const p = feature.properties || {};
        const openVal = p.open || 0;
        const draftVal = p.draft || 0;
        const tdkVal = (p.kl_tdk || 0) + (p.bu_tdk || 0);
        const bangkosVal = p.bangkos || 0;

        // Is it matched by current area filter?
        const isAreaMatch = matchesArea(p, currentAreaFilter);

        if (!isAreaMatch) {
            return {
                color: 'rgba(255, 255, 255, 0.05)',
                weight: 0.3,
                opacity: 0.1,
                fillColor: '#000000',
                fillOpacity: 0
            };
        }

        // Default: Garis tipis transparan tanpa warna isi, sehingga citra satelit tetap terlihat jelas
        let strokeColor = 'rgba(255, 255, 255, 0.12)';
        let fillColor = 'transparent';
        let weight = 0.5;
        let opacity = 0.2;
        let fillOpacity = 0;

        if (currentMode === 'open') {
            if (openVal > 0) {
                strokeColor = '#ef4444';
                fillColor = '#ef4444';
                weight = openVal >= 20 ? 2.5 : 1.8;
                opacity = 0.95;
                fillOpacity = Math.min(0.65, 0.3 + (openVal / 60) * 0.35);
            }
        } else if (currentMode === 'draft') {
            if (draftVal > 0) {
                strokeColor = '#f59e0b';
                fillColor = '#f59e0b';
                weight = draftVal >= 10 ? 2.2 : 1.6;
                opacity = 0.92;
                fillOpacity = Math.min(0.65, 0.25 + (draftVal / 30) * 0.4);
            }
        } else if (currentMode === 'tidak_ditemukan') {
            // Hanya sorot hotspot anomali tinggi agar peta tidak tertutup penuh
            if (tdkVal >= 60) {
                strokeColor = '#dc2626';
                fillColor = '#ef4444';
                weight = 2.4;
                opacity = 0.95;
                fillOpacity = 0.48;
            } else if (tdkVal >= 30) {
                strokeColor = '#ea580c';
                fillColor = '#f97316';
                weight = 1.6;
                opacity = 0.85;
                fillOpacity = 0.26;
            }
        } else if (currentMode === 'bangkos') {
            // Tampilkan SEMUA SLS yang ada bangunan kosong, dengan gradasi intensitas warna
            if (bangkosVal >= 30) {
                strokeColor = '#7c3aed';
                fillColor = '#8b5cf6';
                weight = 2.5;
                opacity = 0.98;
                fillOpacity = 0.55;
            } else if (bangkosVal >= 15) {
                strokeColor = '#7c3aed';
                fillColor = '#8b5cf6';
                weight = 2.0;
                opacity = 0.92;
                fillOpacity = 0.40;
            } else if (bangkosVal >= 5) {
                strokeColor = '#6366f1';
                fillColor = '#818cf8';
                weight = 1.5;
                opacity = 0.85;
                fillOpacity = 0.25;
            } else if (bangkosVal >= 1) {
                strokeColor = '#a78bfa';
                fillColor = '#c4b5fd';
                weight = 1.2;
                opacity = 0.75;
                fillOpacity = 0.15;
            }
        } else {
            // Mode 'all': Sorot gabungan dokumen belum selesai (OPEN & DRAFT)
            if (openVal > 0) {
                strokeColor = '#ef4444';
                fillColor = '#ef4444';
                weight = 2.0;
                opacity = 0.92;
                fillOpacity = 0.38;
            } else if (draftVal > 0) {
                strokeColor = '#f59e0b';
                fillColor = '#f59e0b';
                weight = 1.5;
                opacity = 0.88;
                fillOpacity = 0.25;
            }
        }

        return {
            color: strokeColor,
            weight: weight,
            opacity: opacity,
            fillColor: fillColor,
            fillOpacity: fillOpacity
        };
    }

    // Render GeoJSON to map
    function renderPaluMapLayers() {
        if (!paluMap || !window.PALU_MONITORING_DATA) return;

        if (paluGeoLayer) {
            paluMap.removeLayer(paluGeoLayer);
        }

        paluGeoLayer = L.geoJSON(window.PALU_MONITORING_DATA, {
            style: getFeatureStyle,
            onEachFeature: function (feature, layer) {
                const p = feature.properties || {};
                const openVal = p.open || 0;
                const draftVal = p.draft || 0;
                const bangkosVal = p.bangkos || 0;
                const tdkVal = (p.kl_tdk || 0) + (p.bu_tdk || 0);

                // Tooltip
                const tooltipText = `<b>${p.nmsls || 'SLS'}</b> (${p.nmdesa})<br>OPEN: <b>${openVal}</b> | DRAFT: <b>${draftVal}</b> | B-Kos: <b>${bangkosVal}</b>`;
                layer.bindTooltip(tooltipText, { sticky: true, direction: 'top' });

                // Click event
                layer.on('click', function () {
                    selectPaluSLS(this, feature);
                });
            }
        }).addTo(paluMap);
    }

    // Select SLS and populate inspection card
    function selectPaluSLS(layer, feature) {
        if (selectedLayer && selectedLayer !== layer && paluGeoLayer) {
            paluGeoLayer.resetStyle(selectedLayer);
        }
        selectedLayer = layer;
        layer.setStyle({
            color: '#ffffff',
            weight: 4,
            fillOpacity: 0.65
        });

        const p = feature.properties || {};
        const openVal = p.open || 0;
        const draftVal = p.draft || 0;
        const bangkosVal = p.bangkos || 0;
        const klTdk = p.kl_tdk || 0;
        const buTdk = p.bu_tdk || 0;
        const totTdk = klTdk + buTdk;

        // Populate detail card
        const cardTitle = document.getElementById('palu-insp-title');
        if (cardTitle) cardTitle.textContent = p.nmsls || 'SLS';
        const cardSub = document.getElementById('palu-insp-sub');
        if (cardSub) cardSub.textContent = `${p.nmdesa}, Kec. ${p.nmkec} (Kode: ${p.idsls})`;

        const elOpen = document.getElementById('palu-insp-open');
        if (elOpen) elOpen.textContent = openVal.toLocaleString('id-ID');
        const elDraft = document.getElementById('palu-insp-draft');
        if (elDraft) elDraft.textContent = draftVal.toLocaleString('id-ID');
        const elBangkos = document.getElementById('palu-insp-bangkos');
        if (elBangkos) elBangkos.textContent = bangkosVal.toLocaleString('id-ID');
        const elTdk = document.getElementById('palu-insp-tdk');
        if (elTdk) elTdk.textContent = `${totTdk.toLocaleString('id-ID')} (Keluarga: ${klTdk} | Usaha: ${buTdk})`;

        const elPpl = document.getElementById('palu-insp-ppl');
        if (elPpl) elPpl.textContent = p.ppl || '(Belum Ada PPL)';
        const elPml = document.getElementById('palu-insp-pml');
        if (elPml) elPml.textContent = p.pml || '(Belum Ada PML)';

        // Status badge
        const badge = document.getElementById('palu-insp-badge');
        if (badge) {
            if (openVal > 0) {
                badge.style.background = 'rgba(239, 68, 68, 0.15)';
                badge.style.color = '#dc2626';
                badge.textContent = `🔴 ADA ${openVal} DOKUMEN OPEN`;
            } else if (draftVal > 0) {
                badge.style.background = 'rgba(245, 158, 11, 0.15)';
                badge.style.color = '#d97706';
                badge.textContent = `🟡 ADA ${draftVal} DOKUMEN DRAFT`;
            } else {
                badge.style.background = 'rgba(16, 185, 129, 0.15)';
                badge.style.color = '#059669';
                badge.textContent = `🟢 SELESAI (SUDAH DISUBMIT)`;
            }
        }

        // Zoom to layer
        paluMap.fitBounds(layer.getBounds(), { padding: [100, 100], maxZoom: 17 });
    }

    // Zoom to specific SLS from table button
    window.focusSlsOnPaluMap = function (idsls) {
        if (!paluGeoLayer || !paluMap) return;

        let targetLayer = null;
        let targetFeature = null;

        paluGeoLayer.eachLayer(layer => {
            if (layer.feature && layer.feature.properties && layer.feature.properties.idsls === idsls) {
                targetLayer = layer;
                targetFeature = layer.feature;
            }
        });

        if (targetLayer && targetFeature) {
            // Scroll smoothly to map
            const mapContainer = document.getElementById('palu-monitoring-map');
            if (mapContainer) {
                mapContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
            selectPaluSLS(targetLayer, targetFeature);
        }
    };

    // ====================================================================
    // VIEW SWITCHER: Unit Usaha vs SLS
    // ====================================================================
    window.setPaluTableView = function (view) {
        currentTableView = view;

        // Update button styles
        const btnUsaha = document.getElementById('palu-view-btn-usaha');
        const btnSls = document.getElementById('palu-view-btn-sls');
        if (btnUsaha) {
            btnUsaha.style.background = view === 'usaha' ? '#3b82f6' : 'var(--input-bg)';
            btnUsaha.style.color = view === 'usaha' ? '#fff' : 'var(--text-primary)';
            btnUsaha.style.borderColor = view === 'usaha' ? '#3b82f6' : 'var(--card-border)';
        }
        if (btnSls) {
            btnSls.style.background = view === 'sls' ? '#3b82f6' : 'var(--input-bg)';
            btnSls.style.color = view === 'sls' ? '#fff' : 'var(--text-primary)';
            btnSls.style.borderColor = view === 'sls' ? '#3b82f6' : 'var(--card-border)';
        }

        // Update search placeholder
        const searchInput = document.getElementById('palu-search-input');
        if (searchInput) {
            if (view === 'usaha') {
                searchInput.placeholder = '🔍 Cari Nama Usaha, Pemilik, Kelurahan, Kecamatan...';
                searchInput.oninput = function() { window.handleUsahaSearch(this.value); };
            } else {
                searchInput.placeholder = '🔍 Cari SLS, Kelurahan, Kecamatan, PPL...';
                searchInput.oninput = function() { window.searchPaluTable(this.value); };
            }
            searchInput.value = ''; // reset search
        }

        // Reset page & search states
        usahaPage = 1;
        usahaSearchQuery = '';
        currentPage = 1;
        searchQuery = '';

        window.renderPaluTable();
    };

    // ====================================================================
    // USAHA VIEW: Render unit usaha table
    // ====================================================================
    function renderUsahaTable() {
        const tbody = document.getElementById('palu-table-body');
        const thead = document.getElementById('palu-table-head');
        if (!tbody) return;

        const rawData = window.PALU_UNIT_USAHA_DATA || [];

        // Render thead
        if (thead) {
            thead.innerHTML = `<tr>
                <th style="padding:0.6rem 0.75rem; text-align:center; width:40px; font-size:0.78rem; color:var(--text-secondary); font-weight:600;">No</th>
                <th style="padding:0.6rem 0.75rem; text-align:left; font-size:0.78rem; color:var(--text-secondary); font-weight:600;">Kecamatan</th>
                <th style="padding:0.6rem 0.75rem; text-align:left; font-size:0.78rem; color:var(--text-secondary); font-weight:600;">Kelurahan</th>
                <th style="padding:0.6rem 0.75rem; text-align:left; font-size:0.78rem; color:var(--text-secondary); font-weight:600;">Kode SubSLS</th>
                <th style="padding:0.6rem 0.75rem; text-align:left; font-size:0.78rem; color:var(--text-secondary); font-weight:600;">Nama Usaha</th>
                <th style="padding:0.6rem 0.75rem; text-align:left; font-size:0.78rem; color:var(--text-secondary); font-weight:600;">Pemilik</th>
                <th style="padding:0.6rem 0.75rem; text-align:center; font-size:0.78rem; color:var(--text-secondary); font-weight:600;">Kategori</th>
                <th style="padding:0.6rem 0.75rem; text-align:center; font-size:0.78rem; color:var(--text-secondary); font-weight:600;">Aksi</th>
            </tr>`;
        }

        // Filter
        filteredUsaha = rawData.filter(u => {
            if (usahaKategoriFilter && u.kategori !== usahaKategoriFilter) return false;
            if (usahaSearchQuery) {
                const hay = `${u.nama_usaha} ${u.pemilik} ${u.desa} ${u.kec} ${u.subsls}`.toLowerCase();
                if (!hay.includes(usahaSearchQuery)) return false;
            }
            return true;
        });

        // Update count
        const countInfo = document.getElementById('palu-table-count-info');
        const totalItems = filteredUsaha.length;
        const totalPages = Math.max(1, Math.ceil(totalItems / usahaPerPage));
        if (usahaPage > totalPages) usahaPage = totalPages;

        const startIndex = (usahaPage - 1) * usahaPerPage;
        const pageItems = filteredUsaha.slice(startIndex, startIndex + usahaPerPage);

        if (countInfo) {
            const startDisplay = totalItems === 0 ? 0 : startIndex + 1;
            const endDisplay = Math.min(startIndex + usahaPerPage, totalItems);
            const tdkCount = rawData.filter(u => u.kategori === 'tidak_ditemukan').length;
            const nonaktifCount = rawData.filter(u => u.kategori === 'nonaktif').length;
            countInfo.innerHTML = `Menampilkan <b>${startDisplay} - ${endDisplay}</b> dari <b>${totalItems.toLocaleString('id-ID')} unit usaha</b>
                &nbsp;|&nbsp;
                <span style="color:#ef4444; font-weight:700; cursor:pointer;" onclick="window.filterUsahaKategori('tidak_ditemukan')" title="Klik untuk filter">🔴 Tidak Ditemukan: ${tdkCount}</span>
                &nbsp;
                <span style="color:#f59e0b; font-weight:700; cursor:pointer;" onclick="window.filterUsahaKategori('nonaktif')" title="Klik untuk filter">🟡 Nonaktif: ${nonaktifCount}</span>
                &nbsp;
                <span style="color:var(--text-secondary); font-size:0.75rem; cursor:pointer;" onclick="window.filterUsahaKategori('')" title="Reset filter">[Reset]</span>`;
        }

        renderPaluPagination(totalPages, usahaPage, true);

        if (pageItems.length === 0) {
            tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding:2rem; color:var(--text-secondary);">Tidak ada data unit usaha yang cocok.</td></tr>`;
            return;
        }

        let html = '';
        pageItems.forEach((u, idx) => {
            const rowNo = startIndex + idx + 1;
            const isTdk = u.kategori === 'tidak_ditemukan';
            const isNonaktif = u.kategori === 'nonaktif';

            const kategoriBadge = isTdk
                ? `<span style="display:inline-block; padding:0.2rem 0.55rem; border-radius:9999px; background:rgba(239,68,68,0.12); color:#dc2626; font-size:0.75rem; font-weight:700;">🔴 Tdk Ditemukan</span>`
                : isNonaktif
                ? `<span style="display:inline-block; padding:0.2rem 0.55rem; border-radius:9999px; background:rgba(245,158,11,0.12); color:#d97706; font-size:0.75rem; font-weight:700;">🟡 Nonaktif</span>`
                : `<span style="color:var(--text-secondary); font-size:0.75rem;">${u.kategori || '-'}</span>`;

            html += `
            <tr style="border-bottom:1px solid var(--border-light,#e2e8f0); ${isTdk ? 'background:rgba(239,68,68,0.02);' : isNonaktif ? 'background:rgba(245,158,11,0.02);' : ''}">
                <td style="text-align:center; font-size:0.78rem; color:var(--text-secondary); padding:0.55rem 0.5rem;">${rowNo}</td>
                <td style="padding:0.55rem 0.75rem; font-size:0.82rem; color:var(--text-secondary);">${u.kec || '-'}</td>
                <td style="padding:0.55rem 0.75rem; font-size:0.82rem; font-weight:600; color:var(--text-primary);">${u.desa || '-'}</td>
                <td style="padding:0.55rem 0.75rem; font-size:0.75rem;">
                    <code style="color:var(--text-secondary); background:var(--input-bg); padding:0.1rem 0.35rem; border-radius:3px;">${u.subsls || '-'}</code>
                </td>
                <td style="padding:0.55rem 0.75rem; max-width:200px;">
                    <div style="font-weight:700; color:var(--text-primary); font-size:0.85rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;" title="${u.nama_usaha || ''}">` +
                        (u.nama_usaha || '-') +
                    `</div>
                </td>
                <td style="padding:0.55rem 0.75rem; font-size:0.82rem; color:var(--text-secondary); white-space:nowrap;">` +
                    (u.pemilik || '-') +
                `</td>
                <td style="padding:0.55rem 0.75rem; text-align:center;">${kategoriBadge}</td>
                <td style="padding:0.55rem 0.75rem; text-align:center;">
                    ${u.link
                        ? `<a href="${u.link}" target="_blank" rel="noopener" style="display:inline-flex; align-items:center; gap:0.25rem; padding:0.25rem 0.6rem; border-radius:6px; font-size:0.78rem; font-weight:700; background:linear-gradient(135deg,#3b82f6,#2563eb); color:#fff; text-decoration:none;">🔗 Buka</a>`
                        : '-'}
                </td>
            </tr>`;
        });

        tbody.innerHTML = html;
    }

    // Filter usaha by kategori (clickable from count bar)
    window.filterUsahaKategori = function (kat) {
        usahaKategoriFilter = kat;
        usahaPage = 1;
        renderUsahaTable();
    };

    // Usaha search handler
    window.handleUsahaSearch = function (val) {
        clearTimeout(searchTimer);
        searchTimer = setTimeout(() => {
            usahaSearchQuery = (val || '').trim().toLowerCase();
            usahaPage = 1;
            renderUsahaTable();
        }, 200);
    };

    // ====================================================================
    // SLS VIEW: Render SLS table
    // ====================================================================
    function renderSlsView() {
        const thead = document.getElementById('palu-table-head');
        if (thead) {
            const th = (label, field, extra) =>
                `<th onclick="window.sortPaluTable('${field}')" style="padding:0.6rem 0.75rem; text-align:${extra || 'center'}; font-size:0.78rem; color:var(--text-secondary); font-weight:600; cursor:pointer; white-space:nowrap;" title="Klik untuk sort">${label} <span style="opacity:0.5;">↕</span></th>`;

            thead.innerHTML = `<tr>
                <th style="padding:0.6rem 0.75rem; text-align:center; width:40px; font-size:0.78rem; color:var(--text-secondary); font-weight:600;">No</th>
                ${th('Kelurahan', 'nmdesa', 'left')}
                ${th('SLS', 'nmsls', 'left')}
                ${th('OPEN', 'open')}
                ${th('DRAFT', 'draft')}
                ${th('B-Kos', 'bangkos')}
                ${th('Tdk Tmk', 'tot_tdk')}
                ${th('PPL / PML', 'ppl', 'left')}
                <th style="padding:0.6rem 0.75rem; text-align:center; font-size:0.78rem; color:var(--text-secondary); font-weight:600;">Aksi</th>
            </tr>`;
        }
        renderSlsTable();
    }

    function renderSlsTable() {
        const tbody = document.getElementById('palu-table-body');
        if (!tbody || !window.PALU_MONITORING_DATA) return;

        const rawFeatures = window.PALU_MONITORING_DATA.features || [];

        // 1. Filter
        filteredFeatures = rawFeatures.map(f => {
            const p = f.properties || {};
            const tot_tdk = (p.kl_tdk || 0) + (p.bu_tdk || 0);
            const tot_uncompleted = (p.open || 0) + (p.draft || 0);
            return { ...p, tot_tdk, tot_uncompleted };
        }).filter(p => {
            if (!matchesArea(p, currentAreaFilter)) return false;
            if (searchQuery) {
                const haystack = `${p.nmkec} ${p.nmdesa} ${p.nmsls} ${p.idsls} ${p.ppl} ${p.pml}`.toLowerCase();
                if (!haystack.includes(searchQuery)) return false;
            }
            if (currentMode === 'open') return (p.open || 0) > 0;
            if (currentMode === 'draft') return (p.draft || 0) > 0;
            if (currentMode === 'tidak_ditemukan') return searchQuery ? (p.tot_tdk || 0) > 0 : (p.tot_tdk || 0) >= 30;
            if (currentMode === 'bangkos') return searchQuery ? (p.bangkos || 0) > 0 : (p.bangkos || 0) >= 12;
            if (currentMode === 'all') return (p.open || 0) > 0 || (p.draft || 0) > 0;
            return true;
        });

        // 2. Sort
        filteredFeatures.sort((a, b) => {
            let va = a[sortField] ?? 0;
            let vb = b[sortField] ?? 0;
            if (typeof va === 'string') return sortOrder * va.localeCompare(vb);
            if (va !== vb) return sortOrder * (va - vb);
            return (b.open || 0) - (a.open || 0);
        });

        // 3. Pagination
        const totalItems = filteredFeatures.length;
        const totalPages = Math.max(1, Math.ceil(totalItems / perPage));
        if (currentPage > totalPages) currentPage = totalPages;

        const startIndex = (currentPage - 1) * perPage;
        const pageItems = filteredFeatures.slice(startIndex, startIndex + perPage);

        const countInfo = document.getElementById('palu-table-count-info');
        if (countInfo) {
            const startDisplay = totalItems === 0 ? 0 : startIndex + 1;
            const endDisplay = Math.min(startIndex + perPage, totalItems);
            countInfo.innerHTML = `Menampilkan <b>${startDisplay} - ${endDisplay}</b> dari <b>${totalItems.toLocaleString('id-ID')} SLS</b>`;
        }

        renderPaluPagination(totalPages, currentPage, false);

        if (pageItems.length === 0) {
            tbody.innerHTML = `<tr><td colspan="9" style="text-align:center; padding:2rem; color:var(--text-secondary);">Tidak ada data SLS yang cocok dengan filter aktif.</td></tr>`;
            return;
        }

        let html = '';
        pageItems.forEach((p, idx) => {
            const rowNo = startIndex + idx + 1;
            const openBadge = p.open > 0
                ? `<span class="badge" style="background:rgba(239,68,68,0.15); color:#dc2626; font-weight:800;">${p.open}</span>`
                : `<span style="color:var(--text-secondary); opacity:0.6;">-</span>`;
            const draftBadge = p.draft > 0
                ? `<span class="badge" style="background:rgba(245,158,11,0.15); color:#d97706; font-weight:800;">${p.draft}</span>`
                : `<span style="color:var(--text-secondary); opacity:0.6;">-</span>`;
            const bangkosBadge = p.bangkos > 0
                ? `<span class="badge" style="background:rgba(99,102,241,0.12); color:#4f46e5; font-weight:700;">${p.bangkos}</span>`
                : `<span style="color:var(--text-secondary); opacity:0.6;">-</span>`;
            const tdkBadge = p.tot_tdk > 0
                ? `<span style="color:#d97706; font-weight:700;" title="Keluarga: ${p.kl_tdk} | Usaha: ${p.bu_tdk}">${p.tot_tdk}</span>`
                : `<span style="color:var(--text-secondary); opacity:0.6;">-</span>`;

            html += `
            <tr style="border-bottom:1px solid var(--border-light,#e2e8f0); ${p.open > 0 ? 'background:rgba(239,68,68,0.02);' : ''}">
                <td style="text-align:center; font-size:0.8rem; color:var(--text-secondary); padding:0.55rem 0.5rem;">${rowNo}</td>
                <td style="text-align:left; padding:0.55rem 0.75rem;">
                    <span style="font-weight:700; color:var(--text-primary); font-size:0.88rem;">${p.nmdesa}</span>
                    <div style="font-size:0.75rem; color:var(--text-secondary);">Kec. ${p.nmkec}</div>
                </td>
                <td style="text-align:left; padding:0.55rem 0.75rem;">
                    <div style="font-weight:700; color:var(--text-primary); font-size:0.88rem;">${p.nmsls || '-'}</div>
                    <code style="font-size:0.75rem; color:var(--text-secondary);">${p.idsls}</code>
                </td>
                <td style="text-align:center; padding:0.55rem 0.5rem;">${openBadge}</td>
                <td style="text-align:center; padding:0.55rem 0.5rem;">${draftBadge}</td>
                <td style="text-align:center; padding:0.55rem 0.5rem;">${bangkosBadge}</td>
                <td style="text-align:center; padding:0.55rem 0.5rem;">${tdkBadge}</td>
                <td style="text-align:left; font-size:0.78rem; padding:0.55rem 0.75rem;">
                    <div style="font-weight:700; color:var(--text-primary); max-width:140px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;" title="${p.ppl || '-'}">${p.ppl || '-'}</div>
                    <div style="font-size:0.72rem; color:var(--text-secondary); max-width:140px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;" title="${p.pml || '-'}">PML: ${p.pml || '-'}</div>
                </td>
                <td style="text-align:center; padding:0.55rem 0.5rem;">
                    <button class="btn btn-sm" onclick="window.focusSlsOnPaluMap('${p.idsls}')" style="padding:0.25rem 0.6rem; border-radius:6px; font-size:0.78rem; font-weight:700; background:linear-gradient(135deg,#3b82f6,#2563eb); color:#fff; border:none; cursor:pointer;" title="Lihat SLS di Peta">📍 Peta</button>
                </td>
            </tr>`;
        });

        tbody.innerHTML = html;
    }

    // Main renderPaluTable dispatcher
    window.renderPaluTable = function () {
        if (currentTableView === 'usaha') {
            renderUsahaTable();
        } else {
            renderSlsView();
        }
    };

    // Sort table
    window.sortPaluTable = function (field) {
        if (sortField === field) {
            sortOrder *= -1;
        } else {
            sortField = field;
            sortOrder = (field === 'nmdesa' || field === 'nmsls') ? 1 : -1;
        }
        window.renderPaluTable();
    };

    // Search input
    let searchTimer = null;
    window.handlePaluSearch = function (val) {
        clearTimeout(searchTimer);
        searchTimer = setTimeout(() => {
            searchQuery = (val || '').trim().toLowerCase();
            currentPage = 1;
            window.renderPaluTable();
        }, 200);
    };

    // Pagination
    function renderPaluPagination(totalPages, curPage, isUsahaView) {
        const container = document.getElementById('palu-pagination-container');
        if (!container) return;

        if (totalPages <= 1) {
            container.innerHTML = '';
            return;
        }

        const changeFn = isUsahaView ? 'window.changeUsahaPage' : 'window.changePaluPage';

        let btns = '';
        btns += `<button class="btn btn-sm" onclick="${changeFn}(${curPage - 1})" ${curPage === 1 ? 'disabled style="opacity:0.4;cursor:not-allowed;"' : 'style="cursor:pointer;"'}>‹</button>`;

        for (let i = 1; i <= totalPages; i++) {
            if (i === 1 || i === totalPages || (i >= curPage - 2 && i <= curPage + 2)) {
                const isActive = (i === curPage);
                btns += `<button class="btn btn-sm" onclick="${changeFn}(${i})" style="padding:0.25rem 0.55rem; border-radius:4px; border:1px solid ${isActive ? 'var(--primary)' : 'var(--border-light)'}; background:${isActive ? 'var(--primary)' : 'var(--card-bg)'}; color:${isActive ? '#fff' : 'var(--text-primary)'}; font-weight:${isActive ? '700' : '500'}; font-size:0.8rem; cursor:pointer;">${i}</button>`;
            } else if (i === curPage - 3 || i === curPage + 3) {
                btns += `<span style="padding:0.25rem; color:var(--text-secondary); font-size:0.8rem;">...</span>`;
            }
        }

        btns += `<button class="btn btn-sm" onclick="${changeFn}(${curPage + 1})" ${curPage === totalPages ? 'disabled style="opacity:0.4;cursor:not-allowed;"' : 'style="cursor:pointer;"'}>›</button>`;
        container.innerHTML = btns;
    }

    window.changePaluPage = function (page) {
        currentPage = page;
        renderSlsTable();
    };

    window.changeUsahaPage = function (page) {
        usahaPage = page;
        renderUsahaTable();
    };

    // Export Excel (.xlsx)
    window.exportPaluExcel = function () {
        if (typeof XLSX === 'undefined') {
            alert('Library SheetJS (XLSX) belum dimuat.');
            return;
        }

        const data = filteredFeatures || [];
        if (data.length === 0) {
            alert('Tidak ada data untuk diekspor.');
            return;
        }

        const headers = [
            'No', 'Kecamatan', 'Kelurahan', 'Kode SLS', 'Nama SLS',
            'Status OPEN', 'Status DRAFT', 'Status SUBMITTED',
            'Bangunan Kosong', 'Keluarga Tidak Ditemukan', 'Usaha Tidak Ditemukan', 'Total Tidak Ditemukan',
            'Nama PPL', 'Nama PML'
        ];

        const rows = data.map((p, idx) => [
            idx + 1,
            p.nmkec,
            p.nmdesa,
            p.idsls,
            p.nmsls,
            p.open || 0,
            p.draft || 0,
            p.submitted || 0,
            p.bangkos || 0,
            p.kl_tdk || 0,
            p.bu_tdk || 0,
            (p.kl_tdk || 0) + (p.bu_tdk || 0),
            p.ppl || '',
            p.pml || ''
        ]);

        const wb = XLSX.utils.book_new();
        const ws = XLSX.utils.aoa_to_sheet([headers, ...rows]);
        ws['!cols'] = headers.map(() => ({ wch: 18 }));
        ws['!cols'][1] = { wch: 22 };
        ws['!cols'][2] = { wch: 22 };
        ws['!cols'][4] = { wch: 28 };
        ws['!cols'][12] = { wch: 28 };

        XLSX.utils.book_append_sheet(wb, ws, 'Palu Monitoring');
        const ts = new Date().toISOString().slice(0, 10);
        XLSX.writeFile(wb, `Monitoring_Khusus_Kota_Palu_${ts}.xlsx`);
    };

    // Export CSV
    window.exportPaluCSV = function () {
        const data = filteredFeatures || [];
        if (data.length === 0) {
            alert('Tidak ada data untuk diekspor.');
            return;
        }

        const headers = [
            'No', 'Kecamatan', 'Kelurahan', 'Kode SLS', 'Nama SLS',
            'Status OPEN', 'Status DRAFT', 'Bangunan Kosong', 'Total Tidak Ditemukan', 'PPL', 'PML'
        ];

        let csv = '\uFEFF' + headers.join(',') + '\n';
        data.forEach((p, idx) => {
            const row = [
                idx + 1,
                `"${p.nmkec}"`,
                `"${p.nmdesa}"`,
                `"${p.idsls}"`,
                `"${(p.nmsls || '').replace(/"/g, '""')}"`,
                p.open || 0,
                p.draft || 0,
                p.bangkos || 0,
                (p.kl_tdk || 0) + (p.bu_tdk || 0),
                `"${p.ppl || ''}"`,
                `"${p.pml || ''}"`
            ];
            csv += row.join(',') + '\n';
        });

        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        const ts = new Date().toISOString().slice(0, 10);
        link.setAttribute('href', url);
        link.setAttribute('download', `Monitoring_Khusus_Kota_Palu_${ts}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    // Aliases for HTML bindings
    window.setPaluMode = window.setPaluMapMode;
    window.filterPaluArea = window.focusPaluArea;
    window.searchPaluTable = window.handlePaluSearch;

})();
