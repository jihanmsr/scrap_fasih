let currentPage = 1;
const itemsPerPage = 20;
let filteredData = [];
let sortColumn = null;
let sortAsc = true;
let columnFilters = {};
let currentFilterKey = null;
let filterPopup = null;

let slsOpenMap = null;
let slsMapLayer = null;

function initSlsMap() {
    if (slsOpenMap) return;
    const mapContainer = document.getElementById("sls-open-map");
    if (!mapContainer) return;

    try {
        window._osmTile = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap'
        });
        window._esriTile = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
            attribution: '&copy; Esri World Imagery'
        });

        slsOpenMap = L.map('sls-open-map', {
            center: [-1.4300, 121.4456],
            zoom: 7,
            layers: [window._esriTile],
            zoomControl: true
        });

        const geoData = window.PETA_SLS;
        const highlightedData = window.HIGHLIGHTED_SUBSLS || {};

        // Only render the Open SLS polygons to avoid rendering 15,000+ duplicate/striped borders
        slsMapLayer = L.geoJSON(geoData, {
            filter: function (feature) {
                const p = feature.properties || {};
                const featureId = "72" + (p.kdkab || "") + (p.kdkec || "") + (p.kddesa || "") + (p.kdsls || "") + (p.kdsubsls || "");
                return Boolean(highlightedData[featureId]);
            },
            style: function (feature) {
                return {
                    color: "#ea580c",
                    weight: 3.5,
                    opacity: 1,
                    fillColor: "#f97316",
                    fillOpacity: 0.35
                };
            },
            onEachFeature: function (feature, layer) {
                if (feature.properties) {
                    const p = feature.properties;
                    const featureId = "72" + (p.kdkab || "") + (p.kdkec || "") + (p.kddesa || "") + (p.kdsls || "") + (p.kdsubsls || "");
                    const csv = highlightedData[featureId] || {};
                    
                    let popupContent = `
                        <div style="font-family: 'Outfit', sans-serif; padding: 4px; min-width: 180px;">
                            <div style="font-weight: 800; font-size: 0.95rem; color: #ea580c; margin-bottom: 6px;">🎯 SLS FULL OPEN</div>
                            <div style="font-size: 0.85rem; line-height: 1.45; color: #1e293b;">
                                <b>Kabupaten:</b> ${csv.kabupaten || p.nmkab || '-'}<br>
                                <b>Kecamatan:</b> ${csv.kecamatan || p.nmkec || '-'}<br>
                                <b>Desa:</b> ${csv.desa || p.nmdesa || '-'}<br>
                                <b>SLS:</b> ${csv.nama_sub_sls || csv.sls || p.nmsls || '-'}<br>
                                <b>Kode:</b> <code style="background:#f1f5f9;padding:1px 4px;border-radius:3px;font-size:0.8rem;">${featureId}</code><br>
                                <b>Petugas:</b> ${csv.nama_petugas || '<span style="color:#ef4444;font-weight:700;">(Belum Diassign)</span>'}<br>
                                <b>Jml Prelist:</b> <span style="font-weight:700;color:#ea580c;">${csv.jumlah_prelist || 0}</span>
                            </div>
                        </div>
                    `;
                    layer.bindPopup(popupContent);
                }
            }
        }).addTo(slsOpenMap);

        if (slsMapLayer.getLayers().length > 0) {
            slsOpenMap.fitBounds(slsMapLayer.getBounds(), { padding: [40, 40], maxZoom: 13 });
        }

        populateMapFilters();
        populateDrawerFilters();
        
    } catch(err) {
        console.error("Error loading map data:", err);
    }
}

function populateMapFilters() {
    const kabSelect = document.getElementById('map-filter-kab');
    if (!kabSelect) return;
    kabSelect.innerHTML = '<option value="">Semua Kabupaten</option>';

    if (!window.OPEN_SUBSLS_DATA) return;
    const kabSet = new Set();
    window.OPEN_SUBSLS_DATA.forEach(d => {
        if (d.kabupaten && d.kabupaten.trim()) kabSet.add(d.kabupaten.trim());
    });

    Array.from(kabSet).sort().forEach(kab => {
        const opt = document.createElement('option');
        opt.value = kab;
        opt.textContent = kab;
        kabSelect.appendChild(opt);
    });
}

window.updateMapKecFilter = function() {
    const kab = document.getElementById('map-filter-kab').value;
    const kecSelect = document.getElementById('map-filter-kec');
    if (!kecSelect) return;
    kecSelect.innerHTML = '<option value="">Semua Kecamatan</option>';
    
    if (!window.OPEN_SUBSLS_DATA) {
        window.searchMap();
        return;
    }
    
    const kecSet = new Set();
    window.OPEN_SUBSLS_DATA.forEach(d => {
        if ((!kab || d.kabupaten === kab) && d.kecamatan && d.kecamatan.trim()) {
            kecSet.add(d.kecamatan.trim());
        }
    });
    
    Array.from(kecSet).sort().forEach(kec => {
        const opt = document.createElement('option');
        opt.value = kec;
        opt.textContent = kec;
        kecSelect.appendChild(opt);
    });
    window.searchMap();
};

window.searchMap = function() {
    const query = document.getElementById('map-search-input').value.toLowerCase().trim();
    const filterKab = document.getElementById('map-filter-kab').value;
    const filterKec = document.getElementById('map-filter-kec').value;
    
    if (window.lastSearchedLayer && slsMapLayer) {
        slsMapLayer.resetStyle(window.lastSearchedLayer);
        window.lastSearchedLayer = null;
    }

    if (!slsMapLayer) return;

    if (!query && !filterKab && !filterKec) {
        if (slsMapLayer.getLayers().length > 0) {
            slsOpenMap.fitBounds(slsMapLayer.getBounds(), { padding: [40, 40], maxZoom: 13 });
        }
        return;
    }

    let foundLayers = [];
    const highlightedData = window.HIGHLIGHTED_SUBSLS || {};

    slsMapLayer.eachLayer(function(layer) {
        const p = layer.feature.properties || {};
        const featureId = "72" + (p.kdkab || "") + (p.kdkec || "") + (p.kddesa || "") + (p.kdsls || "") + (p.kdsubsls || "");
        const info = highlightedData[featureId] || {};
        
        const kabVal = (info.kabupaten || p.nmkab || '');
        const kecVal = (info.kecamatan || p.nmkec || '');

        let matchKab = !filterKab || (kabVal === filterKab);
        let matchKec = !filterKec || (kecVal === filterKec);
        
        let matchQuery = true;
        if (query) {
            matchQuery = false;
            if (featureId.includes(query)) matchQuery = true;
            if (!matchQuery) {
                const combined = [
                    kabVal,
                    kecVal,
                    info.desa || p.nmdesa || '',
                    info.nama_sub_sls || info.sls || p.nmsls || '',
                    info.nama_petugas || ''
                ].join(' ').toLowerCase();
                if (combined.includes(query)) matchQuery = true;
            }
        }
        
        if (matchKab && matchKec && matchQuery) {
            foundLayers.push(layer);
        }
    });

    if (foundLayers.length > 0) {
        let group = L.featureGroup(foundLayers);
        slsOpenMap.fitBounds(group.getBounds(), { maxZoom: 15, padding: [50, 50] });
        
        if (foundLayers.length === 1) { 
            let layer = foundLayers[0];
            window.lastSearchedLayer = layer;
            if (layer.setStyle) {
                layer.setStyle({
                    color: "#f59e0b", 
                    weight: 5,
                    opacity: 1,
                    fillColor: "#fbbf24", 
                    fillOpacity: 0.7
                });
            }
            layer.openPopup();
        }
    } else {
        if (query) alert("Pencarian tidak ditemukan di antara SLS Full Open.");
    }
};

const mapObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            if (typeof initSlsMap === 'function') initSlsMap();
            if (slsOpenMap) {
                setTimeout(() => {
                    slsOpenMap.invalidateSize();
                }, 100);
            }
        }
    });
});

document.addEventListener('DOMContentLoaded', () => {
    try {
        const mapContainer = document.getElementById('sls-open-map');
        if (mapContainer) {
            mapObserver.observe(mapContainer);
        }

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
    }
});

function initFilters() {
    const kabFilter = document.getElementById('subsls-filter-kab');
    if (!kabFilter) return;
    kabFilter.innerHTML = '<option value="">Semua Kabupaten</option>';
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
        tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; padding: 2rem; color: var(--text-secondary);">Tidak ada data SLS Open ditemukan</td></tr>';
        if(pagination) pagination.innerHTML = '';
        return;
    }

    const marked = JSON.parse(localStorage.getItem('marked_subsls_open') || '[]');

    paginatedData.forEach(item => {
        const tr = document.createElement('tr');
        const isUnassigned = !item.nama_petugas;
        const petugasHtml = isUnassigned 
            ? '<span style="color: #ef4444; font-weight: 600; font-size: 0.8rem; background: rgba(239, 68, 68, 0.1); padding: 2px 6px; border-radius: 4px;">BELUM DIASSIGN</span>'
            : `<span style="color: var(--text-primary); font-weight: 500;">${item.nama_petugas}</span>`;

        const isMarked = marked.includes(item.kode_sub_sls);
        if (isMarked) {
            tr.style.opacity = '0.5';
            tr.style.backgroundColor = '#f9fafb';
        }

        tr.innerHTML = `
            <td style="font-family: monospace; font-weight: 600; ${isMarked ? 'text-decoration: line-through;' : ''}">${item.kode_sub_sls || '-'}</td>
            <td style="${isMarked ? 'text-decoration: line-through;' : ''}">${item.kabupaten || '-'}</td>
            <td style="${isMarked ? 'text-decoration: line-through;' : ''}">${item.kecamatan || '-'}</td>
            <td style="${isMarked ? 'text-decoration: line-through;' : ''}">${item.desa || '-'}</td>
            <td style="${isMarked ? 'text-decoration: line-through;' : ''}">${item.nama_sub_sls || item.sls || '-'}</td>
            <td>${petugasHtml}</td>
            <td style="text-align: right; font-weight: 600;">${item.jumlah_prelist || 0}</td>
            <td style="text-align: center;">
                <input type="checkbox" style="width: 18px; height: 18px; cursor: pointer;" 
                       ${isMarked ? 'checked' : ''} 
                       onchange="window.toggleSelesai('${item.kode_sub_sls}', this.checked, this)">
            </td>
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

window.downloadSubSlsExcel = function() {
    if (!filteredData || filteredData.length === 0) {
        alert('Tidak ada data untuk diunduh.');
        return;
    }

    const exportData = filteredData.map(item => ({
        'Kode Sub-SLS': item.kode_sub_sls || '',
        'Kabupaten': item.kabupaten || '',
        'Kecamatan': item.kecamatan || '',
        'Desa': item.desa || '',
        'SLS': item.sls || item.nama_sub_sls || '',
        'Nama Petugas': item.nama_petugas || 'BELUM DIASSIGN',
        'Jumlah Prelist': parseInt(item.jumlah_prelist) || 0
    }));

    const ws = XLSX.utils.json_to_sheet(exportData);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "SLS_Open");
    XLSX.writeFile(wb, "Data_SLS_Open.xlsx");
};

window.toggleSelesai = function(kodeSubSls, isChecked, checkboxEl) {
    let marked = JSON.parse(localStorage.getItem('marked_subsls_open') || '[]');
    if (isChecked) {
        if (!marked.includes(kodeSubSls)) marked.push(kodeSubSls);
    } else {
        marked = marked.filter(k => k !== kodeSubSls);
    }
    localStorage.setItem('marked_subsls_open', JSON.stringify(marked));
    
    const tr = checkboxEl.closest('tr');
    if (tr) {
        if (isChecked) {
            tr.style.opacity = '0.5';
            tr.style.backgroundColor = '#f9fafb';
            Array.from(tr.children).forEach((td, idx) => {
                if(idx < 5) td.style.textDecoration = 'line-through';
            });
        } else {
            tr.style.opacity = '1';
            tr.style.backgroundColor = '';
            Array.from(tr.children).forEach((td, idx) => {
                if(idx < 5) td.style.textDecoration = 'none';
            });
        }
    }
};

// ── Map Floating Pill Overlay Handlers ─────────────────────────────────────
window.toggleWilayahDrawer = function() {
    const drawer = document.getElementById("map-wilayah-drawer");
    if (!drawer) return;
    const isVisible = drawer.style.display !== "none";
    drawer.style.display = isVisible ? "none" : "block";
    const pop = document.getElementById("map-basemap-popup");
    if (pop) pop.style.display = "none";
};

window.toggleBaseMapPopup = function() {
    const popup = document.getElementById("map-basemap-popup");
    if (!popup) return;
    const isVisible = popup.style.display !== "none";
    popup.style.display = isVisible ? "none" : "block";
    const drw = document.getElementById("map-wilayah-drawer");
    if (drw) drw.style.display = "none";
};

window.setBaseMapTile = function(type) {
    if (!slsOpenMap) return;
    if (type === 'satellite') {
        if (window._osmTile) slsOpenMap.removeLayer(window._osmTile);
        if (window._esriTile) slsOpenMap.addLayer(window._esriTile);
    } else {
        if (window._esriTile) slsOpenMap.removeLayer(window._esriTile);
        if (window._osmTile) slsOpenMap.addLayer(window._osmTile);
    }
    document.getElementById("map-basemap-popup").style.display = "none";
};

function populateDrawerFilters() {
    const kabSel = document.getElementById("drawer-map-filter-kab");
    if (!kabSel) return;
    kabSel.innerHTML = "<option value=''>Semua Kabupaten</option>";

    if (!window.OPEN_SUBSLS_DATA) return;
    const kabSet = new Set();
    window.OPEN_SUBSLS_DATA.forEach(d => {
        if (d.kabupaten && d.kabupaten.trim()) kabSet.add(d.kabupaten.trim());
    });

    Array.from(kabSet).sort().forEach(kab => {
        const opt = document.createElement("option");
        opt.value = kab;
        opt.textContent = kab;
        kabSel.appendChild(opt);
    });
}

window.onDrawerKabChange = function() {
    const kab = document.getElementById("drawer-map-filter-kab").value;
    const kecSel = document.getElementById("drawer-map-filter-kec");
    const desaSel = document.getElementById("drawer-map-filter-desa");
    const slsSel = document.getElementById("drawer-map-filter-sls");
    
    kecSel.innerHTML = "<option value=''>Semua Kecamatan</option>";
    desaSel.innerHTML = "<option value=''>Semua Desa</option>";
    slsSel.innerHTML = "<option value=''>--- Pilih SLS ---</option>";
    
    if (!window.OPEN_SUBSLS_DATA) return;
    
    const kecSet = new Set();
    window.OPEN_SUBSLS_DATA.forEach(d => {
        if ((!kab || d.kabupaten === kab) && d.kecamatan && d.kecamatan.trim()) {
            kecSet.add(d.kecamatan.trim());
        }
    });
    Array.from(kecSet).sort().forEach(k => {
        const opt = document.createElement("option");
        opt.value = k;
        opt.textContent = k;
        kecSel.appendChild(opt);
    });
    
    const mainKab = document.getElementById("map-filter-kab");
    if (mainKab) { mainKab.value = kab; window.updateMapKecFilter(); }
};

window.onDrawerKecChange = function() {
    const kab = document.getElementById("drawer-map-filter-kab").value;
    const kec = document.getElementById("drawer-map-filter-kec").value;
    const desaSel = document.getElementById("drawer-map-filter-desa");
    const slsSel = document.getElementById("drawer-map-filter-sls");
    
    desaSel.innerHTML = "<option value=''>Semua Desa</option>";
    slsSel.innerHTML = "<option value=''>--- Pilih SLS ---</option>";
    
    if (!window.OPEN_SUBSLS_DATA) return;
    
    const desaSet = new Set();
    window.OPEN_SUBSLS_DATA.forEach(d => {
        if ((!kab || d.kabupaten === kab) && (!kec || d.kecamatan === kec) && d.desa && d.desa.trim()) {
            desaSet.add(d.desa.trim());
        }
    });
    Array.from(desaSet).sort().forEach(d => {
        const opt = document.createElement("option");
        opt.value = d;
        opt.textContent = d;
        desaSel.appendChild(opt);
    });
    
    const mainKec = document.getElementById("map-filter-kec");
    if (mainKec) { mainKec.value = kec; window.searchMap(); }
};

window.onDrawerDesaChange = function() {
    const kab = document.getElementById("drawer-map-filter-kab").value;
    const kec = document.getElementById("drawer-map-filter-kec").value;
    const desa = document.getElementById("drawer-map-filter-desa").value;
    const slsSel = document.getElementById("drawer-map-filter-sls");
    
    slsSel.innerHTML = "<option value=''>--- Pilih SLS ---</option>";
    if (!window.OPEN_SUBSLS_DATA) return;
    
    const slsSet = new Set();
    window.OPEN_SUBSLS_DATA.forEach(d => {
        if ((!kab || d.kabupaten === kab) && (!kec || d.kecamatan === kec) && (!desa || d.desa === desa)) {
            const sName = d.sls || d.nama_sub_sls || d.kode_sub_sls;
            if (sName) slsSet.add(sName);
        }
    });
    Array.from(slsSet).sort().forEach(s => {
        const opt = document.createElement("option");
        opt.value = s;
        opt.textContent = s;
        slsSel.appendChild(opt);
    });
};

window.onDrawerSlsChange = function() {
    const sls = document.getElementById("drawer-map-filter-sls").value;
    if (sls) {
        const input = document.getElementById("map-search-input");
        if (input) { input.value = sls; window.searchMap(); }
    }
};

window.setCustomCoord = function() {
    alert("Klik di mana saja pada peta untuk menyetel koordinat kustom.");
};

window.applyCustomCoord = function() {
    const lat = parseFloat(document.getElementById("map-lat-input").value);
    const lng = parseFloat(document.getElementById("map-lng-input").value);
    if (!isNaN(lat) && !isNaN(lng) && slsOpenMap) {
        slsOpenMap.setView([lat, lng], 15);
        L.marker([lat, lng]).addTo(slsOpenMap).bindPopup("<b>Koordinat Kustom</b><br>" + lat + ", " + lng).openPopup();
    } else {
        alert("Masukkan koordinat Latitude dan Longitude yang valid.");
    }
};
