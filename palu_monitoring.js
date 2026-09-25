/**
 * palu_monitoring.js - Monitoring Lanjutan Wilayah Prioritas Sulawesi Tengah
 * Memetakan dokumen OPEN, DRAFT, Bangunan Kosong, BANR, dan Titik Geotagging
 * pada 8.980 SLS di Kota Palu, Kab. Banggai, Kab. Poso, Kab. Sigi, Kab. Donggala, Kab. Morowali Utara.
 */

(function () {
    let paluMap = null;
    let paluGeoLayer = null;
    let selectedLayer = null;
    let currentMode = 'all'; // 'all', 'open', 'draft', 'tidak_ditemukan', 'bangkos', 'banr'
    let currentKabFilter = 'all'; // 'all', '7271', '7202', '7204', '7210', '7205', '7212', '7209', '7208'
    let currentAreaFilter = 'all'; // 'all', 'lolu_utara', 'tatura_selatan', etc. (for Palu clusters)
    let searchQuery = '';
    let sortField = '__urgent__';
    let sortOrder = -1; // DESC
    let currentPage = 1;
    let perPage = 25;
    let filteredFeatures = [];
    let currentTableView = 'sls'; // 'sls' | 'usaha'

    const KAB_CONFIG = {
        'all':  { name: 'Semua Wilayah Prioritas', center: [-1.2000, 120.8000], zoom: 8 },
        '7271': { name: 'Kota Palu', center: [-0.8917, 119.8707], zoom: 12 },
        '7202': { name: 'Kab. Banggai', center: [-1.1500, 122.6500], zoom: 10 },
        '7204': { name: 'Kab. Poso', center: [-1.6000, 120.7000], zoom: 10 },
        '7210': { name: 'Kab. Sigi', center: [-1.2800, 119.9500], zoom: 10 },
        '7205': { name: 'Kab. Donggala', center: [-0.5500, 119.8000], zoom: 10 },
        '7212': { name: 'Kab. Morowali Utara', center: [-2.0000, 121.3500], zoom: 10 },
        '7209': { name: 'Kab. Tojo Una-Una', center: [-0.8727, 121.6418], zoom: 9 },
        '7208': { name: 'Kab. Parigi Moutong', center: [-0.4500, 120.4500], zoom: 9 }
    };

    // Usaha table state (separate from SLS state)
    let usahaSearchQuery = '';
    let usahaPage = 1;
    let usahaPerPage = 25;
    let usahaKategoriFilter = ''; // '' | 'tidak_ditemukan' | 'nonaktif'
    let filteredUsaha = [];

    // Basemaps: Google Hybrid & Google Roadmap (Peta Jalan Resmi Google Maps, Anti-Block 403)
    let hybridTile = null;
    let roadTile = null;

    // Geotagging Layer (API Titik Lapangan Kak Ical IPDS: https://ause.bpssulteng.id/api/sqllab_geotagging/sls)
    let geotagLayer = null;
    let currentGeotagData = null;
    let currentGeotagFilter = 'all'; // 'all' | 'usaha' | 'keluarga' | 'bangkos'

    window.initPaluMonitoring = function () {
        const container = document.getElementById('palu-monitoring-map');
        if (!container) return;

        // Hide duplicate top header
        const topHeader = document.querySelector('.main-content > header') || document.querySelector('header');
        if (topHeader) topHeader.style.display = 'none';

        if (!paluMap) {
            // Google Hybrid: Citra satelit jernih dengan label jalan, lorong, dan nama tempat
            hybridTile = L.tileLayer('https://mt{s}.google.com/vt/lyrs=y&hl=id&x={x}&y={y}&z={z}', {
                subdomains: ['0', '1', '2', '3'],
                attribution: '&copy; Google Maps Hybrid',
                maxZoom: 20
            });
            // Google Roadmap: Peta jalan resmi Google Maps, cepat, lengkap, dan bebas blokir 403
            roadTile = L.tileLayer('https://mt{s}.google.com/vt/lyrs=m&hl=id&x={x}&y={y}&z={z}', {
                subdomains: ['0', '1', '2', '3'],
                attribution: '&copy; Google Maps',
                maxZoom: 20
            });

            paluMap = L.map('palu-monitoring-map', {
                center: [-1.2000, 120.8000],
                zoom: 8,
                layers: [hybridTile],
                zoomControl: true
            });

            if (!geotagLayer) {
                geotagLayer = L.layerGroup().addTo(paluMap);
            }

            // Auto-resize on container dimension change to eliminate any gaps
            if (window.ResizeObserver && container) {
                const ro = new ResizeObserver(() => {
                    if (paluMap) paluMap.invalidateSize();
                });
                ro.observe(container);
            }

            // Render layer features
            renderPaluMapLayers();
            setTimeout(() => {
                if (paluMap) paluMap.invalidateSize();
            }, 150);
        } else {
            setTimeout(() => {
                if (paluMap) paluMap.invalidateSize();
            }, 150);
        }

        updatePaluSummaryCards(currentKabFilter);
        window.setPaluTableView(currentTableView);
    };

    // Filter Regency (Kabupaten/Kota)
    window.filterMonitoringKab = function (kabCode) {
        currentKabFilter = kabCode || 'all';
        currentAreaFilter = 'all';
        currentPage = 1;
        selectedLayer = null;

        // Highlight active tab
        document.querySelectorAll('.btn-monitoring-kab-tab, .btn-monitoring-kab-pill').forEach(b => {
            const isActive = b.getAttribute('data-kab') === currentKabFilter;
            b.classList.toggle('active', isActive);
        });

        // Reset Palu cluster pills if any exist
        document.querySelectorAll('.btn-palu-area-pill').forEach(b => {
            const isAll = b.getAttribute('data-area') === 'all';
            b.classList.toggle('active', isAll);
        });

        // Show/hide Palu clusters row if present
        const paluClustersRow = document.getElementById('palu-cluster-pills-row');
        if (paluClustersRow) {
            paluClustersRow.style.display = (currentKabFilter === '7271' || currentKabFilter === 'all') ? 'flex' : 'none';
        }

        // Update cards & sorot badges
        updatePaluSummaryCards(currentKabFilter);

        // Pan/zoom map to the selected regency
        const conf = KAB_CONFIG[currentKabFilter] || KAB_CONFIG['all'];
        if (paluMap) {
            paluMap.flyTo(conf.center, conf.zoom, { duration: 1.0 });
        }

        // Re-render polygons
        renderPaluMapLayers(true);

        // Re-render SLS table
        window.renderPaluTable();
    };

    // Update Summary KPI Cards and Sorot Badges
    function updatePaluSummaryCards(targetKab) {
        const data = window.PALU_MONITORING_DATA || window.MONITORING_LANJUTAN_DATA;
        if (!data) return;

        const activeKab = targetKab || currentKabFilter || 'all';
        let s = data.summary;
        let kabTitle = '6 Wilayah Prioritas';

        if (activeKab !== 'all' && data.kab_summary && data.kab_summary[activeKab]) {
            s = data.kab_summary[activeKab];
            kabTitle = s.nmkab || activeKab;
        }

        if (!s) return;

        // Badge in header & active text
        const badgeEl = document.getElementById('monitoring-lanjutan-badge');
        if (badgeEl) {
            badgeEl.textContent = `${(s.sls_count || 0).toLocaleString('id-ID')} SLS • ${kabTitle}`;
        }
        const summaryTextEl = document.getElementById('monitoring-active-summary-text');
        if (summaryTextEl) {
            if (activeKab === 'all') {
                const totalKab = Object.keys(KAB_CONFIG).length - 1;
                summaryTextEl.textContent = `Menampilkan seluruh ${totalKab} kabupaten/kota prioritas (${(s.sls_count || 0).toLocaleString('id-ID')} SLS)`;
            } else {
                summaryTextEl.textContent = `Menampilkan ${kabTitle} (${(s.sls_count || 0).toLocaleString('id-ID')} SLS)`;
            }
        }

        // Executive KPI cards
        const elOpen = document.getElementById('palu-kpi-open');
        if (elOpen) elOpen.textContent = (s.open || 0).toLocaleString('id-ID');
        const elOpenSls = document.getElementById('palu-kpi-open-sls');
        if (elOpenSls) elOpenSls.textContent = `${(s.open_sls || 0).toLocaleString('id-ID')} SLS terdampak`;

        const elDraft = document.getElementById('palu-kpi-draft');
        if (elDraft) elDraft.textContent = (s.draft || 0).toLocaleString('id-ID');
        const elDraftSls = document.getElementById('palu-kpi-draft-sls');
        if (elDraftSls) elDraftSls.textContent = `${(s.draft_sls || 0).toLocaleString('id-ID')} SLS terdampak`;

        const elBangkos = document.getElementById('palu-kpi-bangkos');
        if (elBangkos) elBangkos.textContent = (s.bangkos || 0).toLocaleString('id-ID');
        const elBangkosSls = document.getElementById('palu-kpi-bangkos-sls');
        if (elBangkosSls) elBangkosSls.textContent = `${(s.bangkos_sls || 0).toLocaleString('id-ID')} SLS terlapor`;

        const elBanr = document.getElementById('palu-kpi-banr');
        if (elBanr) elBanr.textContent = (s.banr || 0).toLocaleString('id-ID');
        const elBanrSls = document.getElementById('palu-kpi-banr-sls');
        if (elBanrSls) elBanrSls.textContent = `${(s.banr_sls || 0).toLocaleString('id-ID')} SLS terlapor`;

        const totalTdk = (s.bu_tdk || 0) + (s.kl_tdk || 0);
        const elTdk = document.getElementById('palu-kpi-tdk');
        if (elTdk) elTdk.textContent = totalTdk.toLocaleString('id-ID');
        const elTdkDetail = document.getElementById('palu-kpi-tdk-detail');
        if (elTdkDetail) elTdkDetail.textContent = `Keluarga: ${(s.kl_tdk || 0).toLocaleString('id-ID')} | Usaha: ${(s.bu_tdk || 0).toLocaleString('id-ID')}`;

        // Sorot Layer Mode Counts
        const scAll = document.getElementById('sorot-count-all');
        if (scAll) scAll.textContent = (s.sls_count || 0).toLocaleString('id-ID');
        const scOpen = document.getElementById('sorot-count-open');
        if (scOpen) scOpen.textContent = (s.open || 0).toLocaleString('id-ID');
        const scDraft = document.getElementById('sorot-count-draft');
        if (scDraft) scDraft.textContent = (s.draft || 0).toLocaleString('id-ID');
        const scBangkos = document.getElementById('sorot-count-bangkos');
        if (scBangkos) scBangkos.textContent = (s.bangkos || 0).toLocaleString('id-ID');
        const scBanr = document.getElementById('sorot-count-banr');
        if (scBanr) scBanr.textContent = (s.banr || 0).toLocaleString('id-ID');
    }

    // Basemap toggle: Hybrid vs Google Roadmap
    window.setPaluBasemap = function (type) {
        if (!paluMap) return;
        if (type === 'satellite' || type === 'hybrid') {
            if (roadTile && paluMap.hasLayer(roadTile)) paluMap.removeLayer(roadTile);
            if (hybridTile && !paluMap.hasLayer(hybridTile)) paluMap.addLayer(hybridTile);
        } else {
            if (hybridTile && paluMap.hasLayer(hybridTile)) paluMap.removeLayer(hybridTile);
            if (roadTile && !paluMap.hasLayer(roadTile)) paluMap.addLayer(roadTile);
        }
        document.querySelectorAll('.btn-palu-basemap').forEach(b => {
            const dataBase = b.getAttribute('data-base');
            const isActive = (type === 'satellite' || type === 'hybrid') 
                ? (dataBase === 'satellite' || dataBase === 'hybrid') 
                : (dataBase === type || dataBase === 'osm' || dataBase === 'road');
            b.classList.toggle('active', isActive);
            if (isActive) {
                b.style.background = '#2563eb';
                b.style.color = '#fff';
            } else {
                b.style.background = 'transparent';
                b.style.color = 'var(--text-secondary)';
            }
        });
    };
    window.togglePaluBasemap = window.setPaluBasemap;

    // Mode switch: 'open', 'draft', 'tidak_ditemukan', 'bangkos', 'banr', 'all'
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
        } else if (mode === 'banr') {
            sortField = 'banr';
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
        if (areaKey === 'lolu_utara') return desa.includes('LOLU UTARA');
        if (areaKey === 'tatura_selatan') return desa.includes('TATURA SELATAN');
        if (areaKey === 'lasoani') return desa.includes('LASOANI');
        if (areaKey === 'besusu_timur') return desa.includes('BESUSU TIMUR');
        if (areaKey === 'kayumalue') return desa.includes('KAYUMALUE');
        if (areaKey === 'tondo') return desa.includes('TONDO');
        if (areaKey === 'kawatuna') return desa.includes('KAWATUNA');
        return true;
    }

    // Map Styling: Seluruh batas SLS terlihat jelas, warna tegas untuk isu (OPEN, DRAFT, Bangkos, Selesai)
    function getFeatureStyle(feature) {
        const p = feature.properties || {};
        const openVal = p.open || 0;
        const draftVal = p.draft || 0;
        const tdkVal = (p.kl_tdk || 0) + (p.bu_tdk || 0);
        const bangkosVal = p.bangkos || 0;
        const gapSatelit = p.gap_satelit !== undefined ? p.gap_satelit : 0;

        // Is it matched by current area filter?
        const isAreaMatch = matchesArea(p, currentAreaFilter);

        if (!isAreaMatch) {
            return {
                color: 'rgba(255, 255, 255, 0.08)',
                weight: 0.4,
                opacity: 0.15,
                fillColor: '#000000',
                fillOpacity: 0.15
            };
        }

        // Base style for completed SLS:
        // Visible emerald outline + soft green tint so ALL 1.482 SLS are clearly visible on the map!
        let strokeColor = 'rgba(16, 185, 129, 0.65)';
        let fillColor = '#10b981';
        let weight = 1.2;
        let opacity = 0.85;
        let fillOpacity = 0.18;

        if (currentMode === 'open') {
            if (openVal > 0) {
                strokeColor = '#ffffff';
                fillColor = '#ef4444';
                weight = 3.2;
                opacity = 1;
                fillOpacity = Math.min(0.88, 0.45 + (openVal / 40) * 0.4);
            }
        } else if (currentMode === 'draft') {
            if (draftVal > 0) {
                strokeColor = '#ffffff';
                fillColor = '#f59e0b';
                weight = 2.6;
                opacity = 1;
                fillOpacity = Math.min(0.82, 0.4 + (draftVal / 30) * 0.4);
            }
        } else if (currentMode === 'tidak_ditemukan') {
            if (tdkVal >= 60) {
                strokeColor = '#ffffff';
                fillColor = '#dc2626';
                weight = 3.0;
                opacity = 1;
                fillOpacity = 0.7;
            } else if (tdkVal >= 30) {
                strokeColor = '#ea580c';
                fillColor = '#f97316';
                weight = 2.2;
                opacity = 0.95;
                fillOpacity = 0.55;
            } else if (tdkVal > 0) {
                strokeColor = '#fb923c';
                fillColor = '#fdba74';
                weight = 1.2;
                opacity = 0.8;
                fillOpacity = 0.3;
            }
        } else if (currentMode === 'bangkos') {
            if (bangkosVal >= 30) {
                strokeColor = '#ffffff';
                fillColor = '#7c3aed';
                weight = 2.8;
                opacity = 1;
                fillOpacity = 0.65;
            } else if (bangkosVal >= 15) {
                strokeColor = '#7c3aed';
                fillColor = '#8b5cf6';
                weight = 2.2;
                opacity = 0.95;
                fillOpacity = 0.45;
            } else if (bangkosVal >= 1) {
                strokeColor = '#8b5cf6';
                fillColor = '#c4b5fd';
                weight = 1.2;
                opacity = 0.85;
                fillOpacity = 0.25;
            }
        } else if (currentMode === 'banr') {
            const banrVal = p.banr || 0;
            if (banrVal >= 10) {
                strokeColor = '#ffffff';
                fillColor = '#0891b2';
                weight = 2.8;
                opacity = 1;
                fillOpacity = 0.70;
            } else if (banrVal >= 3) {
                strokeColor = '#0891b2';
                fillColor = '#06b6d4';
                weight = 2.2;
                opacity = 0.95;
                fillOpacity = 0.50;
            } else if (banrVal >= 1) {
                strokeColor = '#06b6d4';
                fillColor = '#67e8f9';
                weight = 1.4;
                opacity = 0.85;
                fillOpacity = 0.30;
            }
        } else {
            // Mode 'all': Status lengkap seluruh SLS Kota Palu
            if (openVal > 0) {
                strokeColor = '#ffffff';
                fillColor = '#ef4444';
                weight = 3.0;
                opacity = 1;
                fillOpacity = 0.72;
            } else if (draftVal > 0) {
                strokeColor = '#ffffff';
                fillColor = '#f59e0b';
                weight = 2.4;
                opacity = 1;
                fillOpacity = 0.60;
            } else if (gapSatelit >= 50) {
                strokeColor = '#6366f1';
                fillColor = '#818cf8';
                weight = 1.8;
                opacity = 0.9;
                fillOpacity = 0.45;
            } else if (bangkosVal >= 15) {
                strokeColor = '#8b5cf6';
                fillColor = '#a78bfa';
                weight = 1.4;
                opacity = 0.85;
                fillOpacity = 0.35;
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

    // Render GeoJSON to map (filtered by active kabupaten)
    function renderPaluMapLayers(skipFitBounds) {
        if (!paluMap) return;
        const data = window.PALU_MONITORING_DATA || window.MONITORING_LANJUTAN_DATA;
        if (!data) return;

        if (paluGeoLayer) {
            paluMap.removeLayer(paluGeoLayer);
        }

        let rawFeatures = data.features || [];
        let featuresToRender = rawFeatures;

        if (currentKabFilter && currentKabFilter !== 'all') {
            featuresToRender = rawFeatures.filter(f => {
                const p = f.properties || {};
                return p.kdkab4 === currentKabFilter || p.kdkab === currentKabFilter.slice(2);
            });
        }

        const filteredGeoJSON = {
            type: 'FeatureCollection',
            features: featuresToRender
        };

        paluGeoLayer = L.geoJSON(filteredGeoJSON, {
            style: getFeatureStyle,
            onEachFeature: function (feature, layer) {
                const p = feature.properties || {};
                const openVal = p.open || 0;
                const draftVal = p.draft || 0;
                const bangkosVal = p.bangkos || 0;
                const banrVal = p.banr || 0;

                // Tooltip
                const tooltipText = `<b>${p.nmsls || 'SLS'}</b> (${p.nmdesa}, ${p.nmkab})<br>OPEN: <b>${openVal}</b> | DRAFT: <b>${draftVal}</b> | B-Kos: <b>${bangkosVal}</b> | BANR: <b>${banrVal}</b>`;
                layer.bindTooltip(tooltipText, { sticky: true, direction: 'top' });

                // Click event
                layer.on('click', function () {
                    selectPaluSLS(this, feature);
                });
            }
        }).addTo(paluMap);

        // Auto-fit bounds on load if no specific layer is selected and not explicitly skipped
        if (!selectedLayer && paluGeoLayer && !skipFitBounds) {
            const b = paluGeoLayer.getBounds();
            if (b.isValid()) {
                paluMap.fitBounds(b, { padding: [30, 30] });
            }
        }
    }

    // Select SLS and populate inspection card
    function selectPaluSLS(layer, feature) {
        if (selectedLayer && selectedLayer !== layer && paluGeoLayer) {
            paluGeoLayer.resetStyle(selectedLayer);
        }
        selectedLayer = layer;

        const p = feature.properties || {};

        // If currentAreaFilter dims out this SLS, reset filter to 'all' so it's fully visible
        if (currentAreaFilter && currentAreaFilter !== 'all' && !matchesArea(p, currentAreaFilter)) {
            currentAreaFilter = 'all';
            document.querySelectorAll('.btn-palu-area-pill').forEach(b => {
                b.classList.toggle('active', b.getAttribute('data-area') === 'all');
            });
            renderPaluMapLayers(true);
            paluGeoLayer.eachLayer(l => {
                if (l.feature && l.feature.properties && l.feature.properties.idsls === p.idsls) {
                    layer = l;
                    selectedLayer = l;
                }
            });
        }

        layer.setStyle({
            color: '#facc15', // Luminous gold border
            weight: 5,
            opacity: 1,
            fillColor: '#38bdf8', // Light cyan-blue tint
            fillOpacity: 0.12 // Semi-transparent so satellite roofs and buildings are clearly visible
        });
        if (layer.bringToFront) {
            layer.bringToFront();
        }
        paluMap.fitBounds(layer.getBounds(), { padding: [60, 60], maxZoom: 17 });

        // Open Leaflet popup directly on top of the SLS polygon
        const openVal = p.open || 0;
        const draftVal = p.draft || 0;
        const statusBadge = openVal > 0 
            ? '<span style="background: #fee2e2; color: #b91c1c; font-weight: 800; padding: 2px 6px; border-radius: 4px; font-size: 0.7rem;">OPEN</span>'
            : (draftVal > 0 ? '<span style="background: #fef3c7; color: #b45309; font-weight: 800; padding: 2px 6px; border-radius: 4px; font-size: 0.7rem;">DRAFT</span>'
            : '<span style="background: #dcfce7; color: #15803d; font-weight: 800; padding: 2px 6px; border-radius: 4px; font-size: 0.7rem;">SELESAI</span>');

        const popupHtml = `
            <div style="font-family: inherit; font-size: 0.8rem; min-width: 170px;">
                <div style="font-weight: 800; font-size: 0.95rem; color: #0f172a; margin-bottom: 2px;">${p.nmsls || 'SLS'}</div>
                <div style="font-size: 0.75rem; color: #64748b; margin-bottom: 4px;">${p.nmdesa}, Kec. ${p.nmkec}</div>
                <div style="display: flex; gap: 4px; align-items: center; margin-bottom: 6px;">${statusBadge}</div>
                <div style="font-size: 0.72rem; color: #475569; border-top: 1px solid #e2e8f0; padding-top: 4px;">Kode: <code>${p.idsls}</code></div>
            </div>
        `;
        layer.bindPopup(popupHtml, { autoPan: false }).openPopup();

        const bangkosVal = p.bangkos || 0;
        const klTdk = p.kl_tdk || 0;
        const buTdk = p.bu_tdk || 0;
        const totTdk = klTdk + buTdk;

        // Populate detail card
        const cardTitle = document.getElementById('palu-insp-title');
        if (cardTitle) cardTitle.textContent = p.nmsls || 'SLS';
        const cardSub = document.getElementById('palu-insp-sub');
        if (cardSub) cardSub.textContent = `${p.nmkab || ''} • ${p.nmdesa}, Kec. ${p.nmkec} (Kode: ${p.idsls})`;

        const elOpen = document.getElementById('palu-insp-open');
        if (elOpen) elOpen.textContent = openVal.toLocaleString('id-ID');
        const elDraft = document.getElementById('palu-insp-draft');
        if (elDraft) elDraft.textContent = draftVal.toLocaleString('id-ID');
        const elBangkos = document.getElementById('palu-insp-bangkos');
        if (elBangkos) elBangkos.textContent = bangkosVal.toLocaleString('id-ID');
        const elBanr = document.getElementById('palu-insp-banr');
        if (elBanr) elBanr.textContent = (p.banr || 0).toLocaleString('id-ID');
        const elTdk = document.getElementById('palu-insp-tdk');
        if (elTdk) elTdk.textContent = `${totTdk.toLocaleString('id-ID')} (Keluarga: ${klTdk} | Usaha: ${buTdk})`;

        // Target Prelist vs Realisasi Fisik Lapangan Comparison
        const prelistVal = p.prelist !== undefined ? p.prelist : (p.satelit_count || 0);
        const banrVal = p.banr || 0;
        const realisasiVal = p.realisasi_fisik || ((p.submitted || 0) + bangkosVal + banrVal);
        const gapVal = p.gap_prelist !== undefined ? p.gap_prelist : (prelistVal - realisasiVal);
        const pctCov = prelistVal > 0 ? Math.round((realisasiVal / prelistVal) * 100) : (realisasiVal > 0 ? 100 : 0);

        const elPrelist = document.getElementById('palu-insp-prelist');
        if (elPrelist) elPrelist.textContent = prelistVal.toLocaleString('id-ID');
        const elReal = document.getElementById('palu-insp-realisasi');
        if (elReal) elReal.textContent = realisasiVal.toLocaleString('id-ID');
        const elGap = document.getElementById('palu-insp-gap');
        if (elGap) {
            elGap.textContent = (gapVal > 0 ? `-${gapVal}` : `+${Math.abs(gapVal)}`).toLocaleString('id-ID');
            elGap.style.color = gapVal > 25 ? '#ef4444' : (gapVal > 5 ? '#ea580c' : '#10b981');
        }
        const elCov = document.getElementById('palu-insp-coverage');
        if (elCov) {
            elCov.textContent = `Cakupan: ${pctCov}%`;
            elCov.style.background = pctCov >= 80 ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)';
            elCov.style.color = pctCov >= 80 ? '#10b981' : '#ef4444';
        }
        const elInsight = document.getElementById('palu-insp-insight');
        if (elInsight) {
            if (gapVal > 30) {
                elInsight.innerHTML = `<strong>Perhatian:</strong> Target prelist sebesar <strong>${prelistVal}</strong>, realisasi fisik baru <strong>${realisasiVal}</strong> (masih kurang <strong>${gapVal}</strong> muatan belum tersurvei). Disarankan penyisiran ulang oleh PPL.`;
            } else if (totTdk > 20) {
                elInsight.innerHTML = `<strong>Perhatian:</strong> Terdapat <strong>${totTdk}</strong> responden berstatus 'Tidak Ditemukan' (Keluarga: ${klTdk}, Usaha: ${buTdk}).`;
            } else if (gapVal > 5) {
                elInsight.innerHTML = `<strong>Progres:</strong> Terdapat selisih <strong>${gapVal}</strong> muatan antara target prelist (${prelistVal}) dan realisasi lapangan (${realisasiVal}).`;
            } else {
                elInsight.innerHTML = `<strong>Sesuai:</strong> Realisasi lapangan (<strong>${realisasiVal}</strong>) telah mencakup target prelist (<strong>${prelistVal}</strong>) dengan capaian <strong>${pctCov}%</strong>.`;
            }
        }

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
                badge.textContent = `OPEN (${openVal})`;
            } else if (draftVal > 0) {
                badge.style.background = 'rgba(245, 158, 11, 0.15)';
                badge.style.color = '#d97706';
                badge.textContent = `DRAFT (${draftVal})`;
            } else {
                badge.style.background = 'rgba(16, 185, 129, 0.15)';
                badge.style.color = '#059669';
                badge.textContent = `SELESAI`;
            }
        }

        // Zoom to layer
        paluMap.fitBounds(layer.getBounds(), { padding: [100, 100], maxZoom: 17 });

        // Load & Render Geotagging Points from API Kak Ical IPDS
        loadAndRenderGeotagPoints(feature);
    }

    // ==========================================
    // GEOTAGGING LAPANGAN SYSTEM (API Kak Ical)
    // ==========================================
    function loadAndRenderGeotagPoints(feature) {
        if (!paluMap) return;
        if (!geotagLayer) {
            geotagLayer = L.layerGroup().addTo(paluMap);
        } else if (!paluMap.hasLayer(geotagLayer)) {
            paluMap.addLayer(geotagLayer);
        }
        geotagLayer.clearLayers();
        currentGeotagData = null;

        const p = feature.properties || {};
        const idsls = p.idsls;
        const badgeEl = document.getElementById('palu-geotag-badge');
        const summaryEl = document.getElementById('palu-geotag-summary');
        const pillsEl = document.getElementById('palu-geotag-pills');
        const unvisitedBoxEl = document.getElementById('palu-unvisited-box');
        const unvisitedListEl = document.getElementById('palu-unvisited-list');

        if (badgeEl) badgeEl.textContent = 'Memuat...';
        if (summaryEl) summaryEl.innerHTML = '<span style="color:#6366f1;">Mengambil titik lapangan dari server...</span>';
        if (pillsEl) pillsEl.style.display = 'none';
        if (unvisitedBoxEl) unvisitedBoxEl.style.display = 'none';
        if (unvisitedListEl) unvisitedListEl.style.display = 'none';

        // 1. Cek Offline Cache lokal
        const checkAndRender = () => {
            const cache = window.PALU_GEOTAGGING_CACHE || {};
            if (cache[idsls] && Array.isArray(cache[idsls])) {
                renderGeotagPoints(cache[idsls], feature);
                return true;
            }
            return false;
        };

        if (checkAndRender()) return;

        // 2. Coba Live Fetch via Local Proxy (CORS-free) atau langsung ke Server
        const tryLiveFetch = () => {
            const payload = {
                kdkab: p.kdkab || "71",
                kdkec: p.kdkec || "",
                kddesa: p.kddesa || "",
                kdsls: (p.kdsls || '') + (p.kdsubsls || '00')
            };

            const fetchViaProxy = () => fetch('http://127.0.0.1:5050/api/sls', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const fetchDirect = () => fetch('https://ause.bpssulteng.id/api/sqllab_geotagging/sls', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            fetchViaProxy()
                .catch(() => fetchDirect())
                .then(res => {
                    if (!res.ok) throw new Error(`HTTP ${res.status}`);
                    return res.json();
                })
                .then(json => {
                    const feats = (json && json.data && json.data.features) ? json.data.features : [];
                    if (!window.PALU_GEOTAGGING_CACHE) window.PALU_GEOTAGGING_CACHE = {};
                    window.PALU_GEOTAGGING_CACHE[idsls] = feats;
                    renderGeotagPoints(feats, feature);
                })
                .catch(err => {
                    console.warn("Geotag live fetch failed:", err);
                    if (badgeEl) {
                        badgeEl.textContent = 'Offline';
                        badgeEl.style.background = 'rgba(239, 68, 68, 0.15)';
                        badgeEl.style.color = '#ef4444';
                    }
                    if (summaryEl) {
                        summaryEl.innerHTML = `
                            <div style="background: rgba(245, 158, 11, 0.08); border-radius: 0.4rem; padding: 0.45rem; border-left: 2px solid #f59e0b; color: var(--text-primary); font-size: 0.7rem; line-height: 1.35;">
                                Titik tidak dapat dimuat langsung karena pembatasan jaringan / SSL. Jalankan <code>python3 proxy_server.py</code> di terminal atau klik SLS prioritas yang berdokumen Open/Draft/BANR.
                            </div>
                        `;
                    }
                });
        };

        if (window.PALU_GEOTAGGING_PROMISE) {
            window.PALU_GEOTAGGING_PROMISE.then(() => {
                if (!checkAndRender()) tryLiveFetch();
            }).catch(() => tryLiveFetch());
            return;
        }

        tryLiveFetch();
    }

    function renderGeotagPoints(features, slsFeature) {
        if (!geotagLayer) return;
        geotagLayer.clearLayers();
        currentGeotagData = { features, slsFeature };

        const p = slsFeature.properties || {};
        const pointsWithCoords = [];
        const unvisitedList = [];

        let usahaCount = 0;
        let keluargaCount = 0;
        let bangkosCount = 0;
        let draftCount = 0;

        features.forEach(f => {
            const props = f.properties || {};
            const geom = f.geometry;
            const isBangkos = (props.data1 === 'BANGUNAN KOSONG') || (props.ada_bang_usaha_value === 2 && !props.ada_keluarga_value);
            const isUsaha = (props.ada_bang_usaha_value === 1) || (props.jumlah_usaha_ditemukan > 0) || (props.jumlah_usaha > 0);
            const isKeluarga = Boolean(props.ada_keluarga_value && props.ada_keluarga_value !== 0);
            const isDraft = (props.assignment_status_alias === 2);

            if (geom && geom.type === 'Point' && Array.isArray(geom.coordinates) && geom.coordinates.length >= 2) {
                const lng = geom.coordinates[0];
                const lat = geom.coordinates[1];
                pointsWithCoords.push({ feature: f, lat, lng, isUsaha, isKeluarga, isBangkos, isDraft });
                if (isUsaha) usahaCount++;
                else if (isBangkos) bangkosCount++;
                else keluargaCount++;
                if (isDraft) draftCount++;
            } else {
                unvisitedList.push(props);
            }
        });

        const badgeEl = document.getElementById('palu-geotag-badge');
        const summaryEl = document.getElementById('palu-geotag-summary');
        const pillsEl = document.getElementById('palu-geotag-pills');
        const unvisitedBoxEl = document.getElementById('palu-unvisited-box');
        const unvisitedListEl = document.getElementById('palu-unvisited-list');
        const unvisitedLabelEl = document.getElementById('palu-unvisited-label');

        if (badgeEl) {
            badgeEl.textContent = `${pointsWithCoords.length} Titik Lapangan`;
            badgeEl.style.background = pointsWithCoords.length > 0 ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)';
            badgeEl.style.color = pointsWithCoords.length > 0 ? '#10b981' : '#ef4444';
        }

        if (summaryEl) {
            summaryEl.innerHTML = `
                <div style="display: flex; justify-content: space-between; font-size: 0.72rem; margin-bottom: 0.3rem;">
                    <span>Sudah berkoordinat: <b style="color:#10b981;">${pointsWithCoords.length}</b></span>
                    <span>Belum tersurvei: <b style="color:#ef4444;">${unvisitedList.length}</b></span>
                </div>
                <div style="font-size: 0.68rem; color: var(--text-secondary); line-height: 1.35;">
                    Area satelit di dalam batas SLS yang tidak bertitik merupakan bangunan yang <b>belum didata</b> petugas.
                </div>
            `;
        }

        if (pillsEl) {
            pillsEl.style.display = 'flex';
            currentGeotagFilter = 'all';
            document.querySelectorAll('.btn-geotag-pill').forEach(b => {
                const isAll = b.getAttribute('data-type') === 'all';
                b.classList.toggle('active', isAll);
                b.style.background = isAll ? '#10b981' : 'transparent';
                b.style.color = isAll ? '#fff' : 'var(--text-secondary)';
            });
        }

        // Tampilkan daftar prelist yang belum didata
        if (unvisitedBoxEl) {
            if (unvisitedList.length > 0) {
                unvisitedBoxEl.style.display = 'block';
                if (unvisitedLabelEl) unvisitedLabelEl.textContent = `Prelist Belum Didata (${unvisitedList.length})`;
                if (unvisitedListEl) {
                    unvisitedListEl.innerHTML = unvisitedList.slice(0, 30).map((u, i) => `
                        <div style="background: rgba(239,68,68,0.06); padding: 0.3rem 0.45rem; border-radius: 0.35rem; border-left: 2px solid #ef4444;">
                            <div style="font-weight: 700; color: var(--text-primary); font-size: 0.72rem;">${i+1}. ${u.data1 || 'Tanpa Nama'}</div>
                            <div style="color: var(--text-secondary); font-size: 0.65rem;">${u.alamat_prelist || 'Alamat prelist'}</div>
                        </div>
                    `).join('') + (unvisitedList.length > 30 ? `<div style="text-align: center; color: var(--text-secondary); font-size: 0.65rem; padding: 0.2rem;">+${unvisitedList.length - 30} prelist lainnya...</div>` : '');
                }
            } else {
                unvisitedBoxEl.style.display = 'none';
            }
        }

        drawGeotagMarkers(pointsWithCoords, 'all');
    }

    function drawGeotagMarkers(points, filter) {
        if (!geotagLayer) return;
        geotagLayer.clearLayers();

        points.forEach(pt => {
            if (filter === 'usaha' && !pt.isUsaha) return;
            if (filter === 'keluarga' && (!pt.isKeluarga || pt.isBangkos)) return;
            if (filter === 'bangkos' && !pt.isBangkos) return;

            const props = pt.feature.properties || {};
            let color = '#10b981'; // Hijau Keluarga
            let labelType = 'Keluarga';

            if (pt.isUsaha) {
                color = '#2563eb'; // Biru Usaha
                labelType = 'Unit Usaha';
            } else if (pt.isBangkos) {
                color = '#f59e0b'; // Kuning Bangkos
                labelType = 'Bangunan Kosong';
            }

            if (pt.isDraft) {
                color = '#ea580c'; // Oranye Draft
                labelType += ' (Draft)';
            }

            const marker = L.circleMarker([pt.lat, pt.lng], {
                pane: 'markerPane',
                radius: 7,
                fillColor: color,
                color: '#ffffff',
                weight: 2,
                opacity: 1,
                fillOpacity: 0.95
            });

            const statusBadge = pt.isDraft 
                ? '<span style="background:#fef3c7;color:#b45309;padding:1px 5px;border-radius:3px;font-weight:700;font-size:0.68rem;">DRAFT</span>'
                : '<span style="background:#dcfce7;color:#15803d;padding:1px 5px;border-radius:3px;font-weight:700;font-size:0.68rem;">APPROVED</span>';

            const popupContent = `
                <div style="font-family: inherit; font-size: 0.78rem; min-width: 180px; padding: 2px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                        <span style="font-weight: 800; color: ${color}; font-size: 0.72rem; text-transform: uppercase;">${labelType}</span>
                        ${statusBadge}
                    </div>
                    <div style="font-weight: 800; font-size: 0.88rem; color: #0f172a; margin-bottom: 3px;">${props.data1 || 'Tanpa Nama'}</div>
                    <div style="font-size: 0.72rem; color: #475569; margin-bottom: 4px;">Bangunan Fisik No: <b>${props.no_bang || '-'}</b></div>
                    ${props.alamat_prelist ? `<div style="font-size: 0.7rem; color: #64748b; margin-bottom: 4px;">📍 ${props.alamat_prelist}</div>` : ''}
                    <div style="font-size: 0.65rem; color: #94a3b8; border-top: 1px solid #e2e8f0; padding-top: 3px;">Koordinat: ${pt.lat.toFixed(6)}, ${pt.lng.toFixed(6)}</div>
                </div>
            `;

            marker.bindPopup(popupContent);
            geotagLayer.addLayer(marker);
        });
    }

    window.filterGeotagPoints = function (type) {
        currentGeotagFilter = type;
        document.querySelectorAll('.btn-geotag-pill').forEach(b => {
            const isActive = b.getAttribute('data-type') === type;
            b.classList.toggle('active', isActive);
            if (isActive) {
                b.style.background = (type === 'usaha' ? '#3b82f6' : (type === 'keluarga' ? '#16a34a' : (type === 'bangkos' ? '#eab308' : '#10b981')));
                b.style.color = '#fff';
            } else {
                b.style.background = 'transparent';
                b.style.color = 'var(--text-secondary)';
            }
        });

        if (currentGeotagData && currentGeotagData.features) {
            const points = [];
            currentGeotagData.features.forEach(f => {
                const props = f.properties || {};
                const geom = f.geometry;
                if (geom && geom.type === 'Point' && Array.isArray(geom.coordinates) && geom.coordinates.length >= 2) {
                    const lng = geom.coordinates[0];
                    const lat = geom.coordinates[1];
                    const isBangkos = (props.data1 === 'BANGUNAN KOSONG') || (props.ada_bang_usaha_value === 2 && !props.ada_keluarga_value);
                    const isUsaha = (props.ada_bang_usaha_value === 1) || (props.jumlah_usaha_ditemukan > 0) || (props.jumlah_usaha > 0);
                    const isKeluarga = Boolean(props.ada_keluarga_value && props.ada_keluarga_value !== 0);
                    const isDraft = (props.assignment_status_alias === 2);
                    points.push({ feature: f, lat, lng, isUsaha, isKeluarga, isBangkos, isDraft });
                }
            });
            drawGeotagMarkers(points, type);
        }
    };

    window.toggleUnvisitedList = function () {
        const listEl = document.getElementById('palu-unvisited-list');
        const arrowEl = document.getElementById('palu-unvisited-arrow');
        if (!listEl) return;
        const isHidden = (listEl.style.display === 'none' || !listEl.style.display);
        listEl.style.display = isHidden ? 'flex' : 'none';
        if (arrowEl) arrowEl.textContent = isHidden ? '▲' : '▼';
    };

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

        // Show/hide urgency sort bar
        const urgencyBar = document.getElementById('palu-urgency-sort-bar');
        if (urgencyBar) {
            urgencyBar.style.display = view === 'sls' ? 'flex' : 'none';
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
            searchInput.value = '';
        }

        // Reset page & search states
        usahaPage = 1;
        usahaSearchQuery = '';
        currentPage = 1;
        searchQuery = '';

        // Default sort for SLS view: urgency composite
        if (view === 'sls') {
            sortField = '__urgent__';
            sortOrder = -1;
            updateUrgencySortBtnState('urgent');
        }

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
                `<th onclick="window.sortPaluTable('${field}')" style="padding:0.6rem 0.55rem; text-align:${extra || 'center'}; font-size:0.78rem; color:var(--text-secondary); font-weight:600; cursor:pointer; white-space:nowrap;" title="Klik untuk sort">${label} <span style="opacity:0.5;">↕</span></th>`;

            thead.innerHTML = `<tr>
                <th style="padding:0.6rem 0.45rem; text-align:center; width:35px; font-size:0.78rem; color:var(--text-secondary); font-weight:600;">No</th>
                ${th('Kabupaten', 'nmkab', 'left')}
                ${th('Kelurahan / Desa', 'nmdesa', 'left')}
                ${th('SLS', 'nmsls', 'left')}
                ${th('OPEN', 'open')}
                ${th('DRAFT', 'draft')}
                ${th('B-Kos', 'bangkos')}
                ${th('BANR', 'banr')}
                ${th('Tdk Tmk', 'tot_tdk')}
                ${th('Target Prelist', 'prelist')}
                ${th('Realisasi', 'realisasi_fisik')}
                ${th('Sisa (Gap)', 'gap_prelist')}
                ${th('PPL / PML', 'ppl', 'left')}
                <th style="padding:0.6rem 0.45rem; text-align:center; font-size:0.78rem; color:var(--text-secondary); font-weight:600;">Aksi</th>
            </tr>`;
        }
        renderSlsTable();
    }

    function renderSlsTable() {
        const tbody = document.getElementById('palu-table-body');
        if (!tbody) return;
        const data = window.PALU_MONITORING_DATA || window.MONITORING_LANJUTAN_DATA;
        if (!data) return;

        const rawFeatures = data.features || [];

        // 1. Filter
        filteredFeatures = rawFeatures.map(f => {
            const p = f.properties || {};
            const tot_tdk = (p.kl_tdk || 0) + (p.bu_tdk || 0);
            const tot_uncompleted = (p.open || 0) + (p.draft || 0);
            return { ...p, tot_tdk, tot_uncompleted };
        }).filter(p => {
            // Regency filter
            if (currentKabFilter && currentKabFilter !== 'all') {
                if (p.kdkab4 !== currentKabFilter && p.kdkab !== currentKabFilter.slice(2)) {
                    return false;
                }
            }
            if (!matchesArea(p, currentAreaFilter)) return false;
            if (searchQuery) {
                const haystack = `${p.nmkab || ''} ${p.nmkec} ${p.nmdesa} ${p.nmsls} ${p.idsls} ${p.ppl} ${p.pml}`.toLowerCase();
                if (!haystack.includes(searchQuery)) return false;
                // Jika user sedang mencari teks / kode tertentu, tampilkan semua yang cocok tanpa dipangkas filter lain
                return true;
            }

            // Filter berdasarkan Quick-Sort / Mode yang aktif jika tidak sedang mencari
            if (activeQuickSort === 'gap_satelit' || activeQuickSort === 'gap_cv') return (p.gap_cv || 0) > 0 || (p.gap_satelit || 0) > 0;
            if (activeQuickSort === 'open') return (p.open || 0) > 0;
            if (activeQuickSort === 'draft') return (p.draft || 0) > 0;
            if (activeQuickSort === 'bangkos') return (p.bangkos || 0) > 0;
            if (activeQuickSort === 'banr') return (p.banr || 0) > 0;
            if (activeQuickSort === 'tot_tdk') return (p.tot_tdk || 0) > 0;
            if (activeQuickSort === 'urgent' || activeQuickSort === '__urgent__') return ((p.open || 0) > 0 || (p.draft || 0) > 0 || (p.tot_tdk || 0) > 0 || (p.bangkos || 0) > 0 || (p.banr || 0) > 0 || (p.gap_cv || 0) >= 20);

            if (currentMode === 'open') return (p.open || 0) > 0;
            if (currentMode === 'draft') return (p.draft || 0) > 0;
            if (currentMode === 'bangkos') return (p.bangkos || 0) >= 12;
            if (currentMode === 'banr') return (p.banr || 0) > 0;
            if (currentMode === 'tidak_ditemukan') return (p.tot_tdk || 0) >= 30;
            
            // Mode 'all': tampilkan semua SLS
            return true;
        });

        // 2. Sort
        filteredFeatures.sort((a, b) => {
            if (sortField === '__urgent__' || sortField === 'default') {
                const uA = (a.open || 0) * 10 + (a.draft || 0) * 5 + (a.tot_tdk || 0) * 2 + Math.max(0, a.gap_cv || 0);
                const uB = (b.open || 0) * 10 + (b.draft || 0) * 5 + (b.tot_tdk || 0) * 2 + Math.max(0, b.gap_cv || 0);
                return uB - uA;
            }
            if (sortField === 'nmkab') return sortOrder * (a.nmkab || '').localeCompare(b.nmkab || '');
            if (sortField === 'prelist') return sortOrder * ((a.prelist || 0) - (b.prelist || 0));
            if (sortField === 'bangunan_cv') return sortOrder * ((a.bangunan_cv || 0) - (b.bangunan_cv || 0));
            if (sortField === 'gap_cv' || sortField === 'gap_satelit') return sortOrder * ((a.gap_cv || 0) - (b.gap_cv || 0));
            if (sortField === 'banr') return sortOrder * ((a.banr || 0) - (b.banr || 0));
            if (sortField === 'nmdesa') return sortOrder * (a.nmdesa || '').localeCompare(b.nmdesa || '');
            if (sortField === 'nmsls') return sortOrder * (a.nmsls || '').localeCompare(b.nmsls || '');
            if (sortField === 'ppl') return sortOrder * (a.ppl || '').localeCompare(b.ppl || '');
            let va = a[sortField] ?? 0;
            let vb = b[sortField] ?? 0;
            if (typeof va === 'string') return sortOrder * va.localeCompare(vb);
            return sortOrder * (Number(va) - Number(vb));
        });

        // 3. Paginate
        const totalItems = filteredFeatures.length;
        const totalPages = Math.ceil(totalItems / perPage) || 1;
        if (currentPage > totalPages) currentPage = 1;

        const startIndex = (currentPage - 1) * perPage;
        const pageItems = filteredFeatures.slice(startIndex, startIndex + perPage);

        // Update info counter
        const countInfo = document.getElementById('palu-count-info');
        if (countInfo) {
            const startDisplay = totalItems === 0 ? 0 : startIndex + 1;
            const endDisplay = Math.min(startIndex + perPage, totalItems);
            countInfo.innerHTML = `Menampilkan <b>${startDisplay} - ${endDisplay}</b> dari <b>${totalItems.toLocaleString('id-ID')} SLS</b>`;
        }

        renderPaluPagination(totalPages, currentPage, false);

        // 4. Render Rows
        let html = '';
        if (pageItems.length === 0) {
            html = `<tr><td colspan="15" style="text-align:center; padding:2rem; color:var(--text-secondary);">Tidak ada data SLS yang cocok dengan filter atau pencarian</td></tr>`;
            tbody.innerHTML = html;
            return;
        }

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
            const banrBadge = p.banr > 0
                ? `<span class="badge" style="background:rgba(6,182,212,0.15); color:#0891b2; font-weight:700;">${p.banr}</span>`
                : `<span style="color:var(--text-secondary); opacity:0.6;">-</span>`;
            const tdkBadge = p.tot_tdk > 0
                ? `<span style="color:#d97706; font-weight:700;" title="Keluarga: ${p.kl_tdk} | Usaha: ${p.bu_tdk}">${p.tot_tdk}</span>`
                : `<span style="color:var(--text-secondary); opacity:0.6;">-</span>`;

            // Prelist vs Realisasi Lapangan
            const prelistVal = p.prelist !== undefined ? p.prelist : (p.satelit_count || 0);
            const banrVal = p.banr || 0;
            const realisasiVal = p.realisasi_fisik || ((p.submitted || 0) + (p.bangkos || 0) + banrVal);
            const gapPrelist = p.gap_prelist !== undefined ? p.gap_prelist : (prelistVal - realisasiVal);
            const gapCv = p.gap_cv !== undefined ? p.gap_cv : gapPrelist;

            let gapBadge = `<span style="color:#10b981; font-weight:700; font-size:0.8rem;">0</span>`;
            if (gapCv >= 40) {
                gapBadge = `<span class="badge" style="background:rgba(239,68,68,0.15); color:#dc2626; font-weight:800; font-size:0.75rem;" title="Target Prelist ${prelistVal}, Realisasi ${realisasiVal}">+${gapCv}</span>`;
            } else if (gapCv > 0) {
                gapBadge = `<span class="badge" style="background:rgba(245,158,11,0.15); color:#d97706; font-weight:700; font-size:0.75rem;" title="Selisih ${gapCv} muatan">+${gapCv}</span>`;
            } else if (gapCv < 0) {
                gapBadge = `<span style="color:var(--text-secondary); font-weight:600; font-size:0.78rem;">${gapCv}</span>`;
            }

            const kabBadge = `<span style="display:inline-block; font-size:0.72rem; font-weight:700; color:#2563eb; background:rgba(37,99,235,0.08); padding:0.15rem 0.4rem; border-radius:0.3rem; white-space:nowrap;">${p.nmkab || ''}</span>`;

            html += `
            <tr style="border-bottom:1px solid var(--border-light,#e2e8f0); ${p.open > 0 ? 'background:rgba(239,68,68,0.02);' : ''}">
                <td style="text-align:center; font-size:0.8rem; color:var(--text-secondary); padding:0.55rem 0.45rem;">${rowNo}</td>
                <td style="text-align:left; padding:0.55rem 0.55rem;">${kabBadge}</td>
                <td style="text-align:left; padding:0.55rem 0.55rem;">
                    <span style="font-weight:700; color:var(--text-primary); font-size:0.85rem;">${p.nmdesa}</span>
                    <div style="font-size:0.72rem; color:var(--text-secondary);">Kec. ${p.nmkec}</div>
                </td>
                <td style="text-align:left; padding:0.55rem 0.55rem;">
                    <div style="font-weight:700; color:var(--text-primary); font-size:0.85rem; cursor:pointer;" onclick="window.focusSlsOnPaluMap('${p.idsls}')" title="Klik untuk zoom di peta">${p.nmsls || '-'}</div>
                    <code style="font-size:0.72rem; color:var(--text-secondary);">${p.idsls}</code>
                </td>
                <td style="text-align:center; padding:0.55rem 0.4rem;">${openBadge}</td>
                <td style="text-align:center; padding:0.55rem 0.4rem;">${draftBadge}</td>
                <td style="text-align:center; padding:0.55rem 0.4rem;">${bangkosBadge}</td>
                <td style="text-align:center; padding:0.55rem 0.4rem;">${banrBadge}</td>
                <td style="text-align:center; padding:0.55rem 0.4rem;">${tdkBadge}</td>
                <td style="text-align:center; padding:0.55rem 0.4rem; font-weight:700; color:#3b82f6;" title="Prelist Muatan BPS: ${prelistVal}">${prelistVal.toLocaleString('id-ID')}</td>
                <td style="text-align:center; padding:0.55rem 0.4rem; font-weight:700; color:#10b981;">${realisasiVal.toLocaleString('id-ID')}</td>
                <td style="text-align:center; padding:0.55rem 0.4rem;">${gapBadge}</td>
                <td style="text-align:left; font-size:0.78rem; padding:0.55rem 0.55rem;">
                    <div style="font-weight:700; color:var(--text-primary); max-width:130px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;" title="${p.ppl || '-'}">${p.ppl || '-'}</div>
                    <div style="font-size:0.72rem; color:var(--text-secondary); max-width:130px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;" title="${p.pml || '-'}">PML: ${p.pml || '-'}</div>
                </td>
                <td style="text-align:center; padding:0.55rem 0.45rem;">
                    <button class="btn btn-sm" onclick="window.focusSlsOnPaluMap('${p.idsls}')" style="padding:0.25rem 0.6rem; border-radius:6px; font-size:0.78rem; font-weight:700; background:linear-gradient(135deg,#3b82f6,#2563eb); color:#fff; border:none; cursor:pointer;" title="Lihat SLS di Peta">Peta</button>
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

    window.sortPaluTable = function (field) {
        if (sortField === field) {
            sortOrder = -sortOrder;
        } else {
            sortField = field;
            sortOrder = 1;
        }
        currentPage = 1;
        window.renderPaluTable();
    };

    // Quick-sort from urgency bar with toggle support
    let activeQuickSort = null;
    window.quickSortPalu = function (factor) {
        if (activeQuickSort === factor) {
            // Toggle off back to default
            activeQuickSort = null;
            sortField = 'default';
            sortOrder = 1;
        } else {
            activeQuickSort = factor;
            if (factor === 'urgent') {
                sortField = '__urgent__';
            } else {
                sortField = factor;
            }
            sortOrder = -1;
        }
        currentPage = 1;
        updateUrgencySortBtnState(activeQuickSort);
        window.renderPaluTable();
    };

    function updateUrgencySortBtnState(activeKey) {
        const allIds = [
            'sort-btn-gapsat', 'sort-btn-open', 'sort-btn-draft', 
            'sort-btn-bangkos', 'sort-btn-banr', 'sort-btn-tdk', 'sort-btn-urgent'
        ];
        allIds.forEach(id => {
            const btn = document.getElementById(id);
            if (btn) {
                btn.style.boxShadow = 'none';
                btn.style.transform = 'none';
                btn.style.opacity = '0.85';
            }
        });

        const map = {
            'gap_satelit': 'sort-btn-gapsat',
            'gap_cv': 'sort-btn-gapsat',
            'open': 'sort-btn-open',
            'draft': 'sort-btn-draft',
            'bangkos': 'sort-btn-bangkos',
            'banr': 'sort-btn-banr',
            'tot_tdk': 'sort-btn-tdk',
            'urgent': 'sort-btn-urgent',
            '__urgent__': 'sort-btn-urgent'
        };

        const activeId = map[activeKey];
        if (activeId) {
            const btn = document.getElementById(activeId);
            if (btn) {
                btn.style.opacity = '1';
                btn.style.boxShadow = '0 0 0 2px #2563eb, 0 2px 6px rgba(37,99,235,0.3)';
                btn.style.transform = 'translateY(-1px)';
            }
        }
    }

    // Clear search input
    window.clearPaluSearch = function () {
        const searchInput = document.getElementById('palu-search-input');
        if (searchInput) {
            searchInput.value = '';
            searchInput.focus();
        }
        const clearBtn = document.getElementById('palu-search-clear-btn');
        if (clearBtn) clearBtn.style.display = 'none';

        searchQuery = '';
        currentPage = 1;
        window.renderPaluTable();
    };

    // Reset Table Filters
    window.resetPaluTableFilters = function () {
        const searchInput = document.getElementById('palu-search-input');
        if (searchInput) searchInput.value = '';
        const clearBtn = document.getElementById('palu-search-clear-btn');
        if (clearBtn) clearBtn.style.display = 'none';

        searchQuery = '';
        activeQuickSort = null;
        sortField = 'default';
        sortOrder = 1;
        currentAreaFilter = 'all';
        currentMode = 'all';
        currentPage = 1;

        // Reset mode buttons to 'all'
        document.querySelectorAll('.btn-palu-mode').forEach(b => {
            b.classList.toggle('active', b.getAttribute('data-mode') === 'all');
        });

        updateUrgencySortBtnState(null);
        if (typeof updatePaluStatsCard === 'function') updatePaluStatsCard();
        if (typeof updatePaluLayer === 'function') updatePaluLayer();
        window.renderPaluTable();
    };

    // Search input handler
    let searchTimer = null;
    window.handlePaluSearch = function (query) {
        const clearBtn = document.getElementById('palu-search-clear-btn');
        if (clearBtn) {
            clearBtn.style.display = (query && query.trim().length > 0) ? 'block' : 'none';
        }
        clearTimeout(searchTimer);
        searchTimer = setTimeout(() => {
            searchQuery = (query || '').trim().toLowerCase();
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
            'No', 'Kabupaten', 'Kecamatan', 'Kelurahan / Desa', 'Kode SLS', 'Nama SLS',
            'Status OPEN', 'Status DRAFT', 'Status SUBMITTED',
            'Bangunan Kosong', 'BANR', 'Keluarga Tidak Ditemukan', 'Usaha Tidak Ditemukan', 'Total Tidak Ditemukan',
            'Prelist Muatan (BPS)', 'Bangunan Fisik (CV Satelit)', 'Realisasi Fisik Lapangan', 'Gap Fisik vs CV',
            'Nama PPL', 'Nama PML'
        ];

        const rows = data.map((p, idx) => {
            const prelistVal = p.prelist !== undefined ? p.prelist : (p.satelit_count || 0);
            const cvVal = p.bangunan_cv || Math.round(prelistVal * 0.88);
            const banrVal = p.banr || 0;
            const realisasiVal = p.realisasi_fisik || ((p.submitted || 0) + (p.bangkos || 0) + banrVal);
            const gapCv = p.gap_cv !== undefined ? p.gap_cv : (cvVal - realisasiVal);

            return [
                idx + 1,
                p.nmkab || '',
                p.nmkec,
                p.nmdesa,
                p.idsls,
                p.nmsls,
                p.open || 0,
                p.draft || 0,
                p.submitted || 0,
                p.bangkos || 0,
                banrVal,
                p.kl_tdk || 0,
                p.bu_tdk || 0,
                (p.kl_tdk || 0) + (p.bu_tdk || 0),
                prelistVal,
                cvVal,
                realisasiVal,
                gapCv,
                p.ppl || '',
                p.pml || ''
            ];
        });

        const wb = XLSX.utils.book_new();
        const ws = XLSX.utils.aoa_to_sheet([headers, ...rows]);
        ws['!cols'] = headers.map(() => ({ wch: 18 }));
        ws['!cols'][1] = { wch: 22 };
        ws['!cols'][2] = { wch: 22 };
        ws['!cols'][3] = { wch: 22 };
        ws['!cols'][5] = { wch: 28 };
        ws['!cols'][18] = { wch: 28 };

        XLSX.utils.book_append_sheet(wb, ws, 'Monitoring Lanjutan');
        const ts = new Date().toISOString().slice(0, 10);
        const kabSuffix = currentKabFilter === 'all' ? 'Semua_Wilayah' : (KAB_CONFIG[currentKabFilter]?.name || currentKabFilter).replace(/[^a-zA-Z0-9]/g, '_');
        XLSX.writeFile(wb, `Monitoring_Lanjutan_${kabSuffix}_${ts}.xlsx`);
    };

    // Export CSV
    window.exportPaluCSV = function () {
        const data = filteredFeatures || [];
        if (data.length === 0) {
            alert('Tidak ada data untuk diekspor.');
            return;
        }

        const headers = [
            'No', 'Kabupaten', 'Kecamatan', 'Kelurahan', 'Kode SLS', 'Nama SLS',
            'Status OPEN', 'Status DRAFT', 'Bangunan Kosong', 'BANR', 'Total Tidak Ditemukan',
            'Prelist Muatan (BPS)', 'Bangunan Fisik (CV Satelit)', 'Realisasi Lapangan', 'Gap Fisik vs CV',
            'PPL', 'PML'
        ];

        let csv = '\uFEFF' + headers.join(',') + '\n';
        data.forEach((p, idx) => {
            const prelistVal = p.prelist !== undefined ? p.prelist : (p.satelit_count || 0);
            const cvVal = p.bangunan_cv || Math.round(prelistVal * 0.88);
            const banrVal = p.banr || 0;
            const realisasiVal = p.realisasi_fisik || ((p.submitted || 0) + (p.bangkos || 0) + banrVal);
            const gapCv = p.gap_cv !== undefined ? p.gap_cv : (cvVal - realisasiVal);

            const row = [
                idx + 1,
                `"${p.nmkab || ''}"`,
                `"${p.nmkec}"`,
                `"${p.nmdesa}"`,
                `"${p.idsls}"`,
                `"${(p.nmsls || '').replace(/"/g, '""')}"`,
                p.open || 0,
                p.draft || 0,
                p.bangkos || 0,
                banrVal,
                (p.kl_tdk || 0) + (p.bu_tdk || 0),
                prelistVal,
                cvVal,
                realisasiVal,
                gapCv,
                `"${p.ppl || ''}"`,
                `"${p.pml || ''}"`
            ];
            csv += row.join(',') + '\n';
        });

        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        const ts = new Date().toISOString().slice(0, 10);
        const kabSuffix = currentKabFilter === 'all' ? 'Semua_Wilayah' : (KAB_CONFIG[currentKabFilter]?.name || currentKabFilter).replace(/[^a-zA-Z0-9]/g, '_');
        link.setAttribute('href', url);
        link.setAttribute('download', `Monitoring_Lanjutan_${kabSuffix}_${ts}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    // Fullscreen Toggle for Map
    window.togglePaluMapFullscreen = function (forceState) {
        const mapBox = document.querySelector('.monitoring-map-box');
        if (!mapBox) return;

        const isCurrentlyFs = mapBox.classList.contains('is-fullscreen');
        const willBeFs = typeof forceState === 'boolean' ? forceState : !isCurrentlyFs;

        if (willBeFs) {
            // Enter Fullscreen
            mapBox.classList.add('is-fullscreen');
            document.body.style.overflow = 'hidden';
            const fsBtnLabel = document.getElementById('palu-fs-label');
            if (fsBtnLabel) fsBtnLabel.textContent = 'Keluar Layar Penuh';
            const fsBtnIcon = document.getElementById('palu-fs-icon');
            if (fsBtnIcon) fsBtnIcon.textContent = '✕';
            const fsControls = document.getElementById('palu-map-fs-controls');
            if (fsControls) fsControls.style.display = 'flex';

            // Try HTML5 requestFullscreen if supported
            if (mapBox.requestFullscreen && !document.fullscreenElement) {
                mapBox.requestFullscreen().catch(() => {});
            }
        } else {
            // Exit Fullscreen
            mapBox.classList.remove('is-fullscreen');
            document.body.style.overflow = '';
            const fsBtnLabel = document.getElementById('palu-fs-label');
            if (fsBtnLabel) fsBtnLabel.textContent = 'Layar Penuh';
            const fsBtnIcon = document.getElementById('palu-fs-icon');
            if (fsBtnIcon) fsBtnIcon.textContent = '⛶';
            const fsControls = document.getElementById('palu-map-fs-controls');
            if (fsControls) fsControls.style.display = 'none';

            if (document.exitFullscreen && document.fullscreenElement) {
                document.exitFullscreen().catch(() => {});
            }
        }

        // Leaflet recalculates dimensions
        setTimeout(() => {
            if (paluMap) {
                paluMap.invalidateSize();
                if (selectedLayer && selectedLayer.getBounds) {
                    paluMap.fitBounds(selectedLayer.getBounds(), { padding: [50, 50], maxZoom: 17 });
                }
            }
        }, 150);
    };

    // Listen for native escape / fullscreen exit
    document.addEventListener('fullscreenchange', () => {
        if (!document.fullscreenElement) {
            const mapBox = document.querySelector('.monitoring-map-box');
            if (mapBox && mapBox.classList.contains('is-fullscreen')) {
                window.togglePaluMapFullscreen(false);
            }
        }
    });

    // Also listen for Escape key in case CSS fullscreen was used without native fullscreen
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            const mapBox = document.querySelector('.monitoring-map-box');
            if (mapBox && mapBox.classList.contains('is-fullscreen')) {
                window.togglePaluMapFullscreen(false);
            }
        }
    });

    // Aliases for HTML bindings
    window.setPaluMode = window.setPaluMapMode;
    window.filterPaluArea = window.focusPaluArea;
    window.searchPaluTable = window.handlePaluSearch;
    window.initMonitoringLanjutan = window.initPaluMonitoring;

})();
