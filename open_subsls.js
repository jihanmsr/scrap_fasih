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
    const mapContainer = document.getElementById('sls-open-map');
    if (!mapContainer) return;
    
    // Default view for Sulawesi Tengah
    const osm = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    });
    const satellite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        attribution: '&copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
    });

    slsOpenMap = L.map('sls-open-map', {
        center: [-1.4300, 121.4456],
        zoom: 6,
        layers: [satellite] // Default
    });

    L.control.layers({
        "Peta Satelit (Esri)": satellite,
        "Peta Biasa (OSM)": osm
    }).addTo(slsOpenMap);

    if (!window.PETA_SLS) {
        console.error("Data peta tidak ditemukan. Pastikan petasls.js sudah dimuat.");
        return;
    }

    const geoData = window.PETA_SLS;
    const highlightedData = window.HIGHLIGHTED_SUBSLS || {};

    try {
        slsMapLayer = L.geoJSON(geoData, {
            style: function (feature) {
                const p = feature.properties || {};
                const featureId = "72" + (p.kdkab || "") + (p.kdkec || "") + (p.kddesa || "") + (p.kdsls || "") + (p.kdsubsls || "");
                
                if (highlightedData[featureId]) {
                    return {
                        color: "#ef4444", // Bright Red outline
                        weight: 3.5,      // Thicker outline
                        opacity: 1,
                        fillColor: "#ef4444",
                        fillOpacity: 0.15 // Highly transparent so satellite imagery is visible
                    };
                } else {
                    return {
                        color: "#3b82f6", // Blue for default
                        weight: 1.5,
                        opacity: 0.8,
                        fillColor: "#60a5fa",
                        fillOpacity: 0.05 // Very transparent
                    };
                }
            },
            onEachFeature: function (feature, layer) {
                if (feature.properties) {
                    const p = feature.properties;
                    const featureId = "72" + (p.kdkab || "") + (p.kdkec || "") + (p.kddesa || "") + (p.kdsls || "") + (p.kdsubsls || "");
                    
                    let popupContent = '<div style="max-height: 200px; overflow-y: auto;"><b>Detail SLS</b><br>';
                    for (let key in feature.properties) {
                        popupContent += `<b>${key}</b>: ${feature.properties[key]}<br>`;
                    }
                    popupContent += `<b>Kode Sub SLS Lengkap</b>: ${featureId}<br>`;
                    
                    if (highlightedData[featureId]) {
                        const csv = highlightedData[featureId];
                        popupContent += `<br><div style="padding: 6px; background: #fee2e2; border-radius: 4px; font-size: 0.9em; margin-top: 5px;">`;
                        popupContent += `<b style="color:#dc2626;">🎯 DATA DARI CSV:</b><br>`;
                        popupContent += `<b>Petugas:</b> ${csv.nama_petugas || '-'}<br>`;
                        popupContent += `<b>Nama Sub SLS (CSV):</b> ${csv.nama_sub_sls || csv.sls || '-'}<br>`;
                        popupContent += `<b>Jml Prelist:</b> ${csv.jumlah_prelist || 0}<br>`;
                        popupContent += `</div>`;
                    }
                    
                    popupContent += '</div>';
                    layer.bindPopup(popupContent);
                }
            }
        }).addTo(slsOpenMap);
        slsOpenMap.fitBounds(slsMapLayer.getBounds());
        populateMapFilters();
    } catch(err) {
        console.error("Error loading map data:", err);
    }
}

const mapObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            initSlsMap();
            if (slsOpenMap) {
                setTimeout(() => {
                    slsOpenMap.invalidateSize();
                }, 100);
            }
        }
    });
});

window.lastSearchedLayer = null;

function populateMapFilters() {
    if (!window.PETA_SLS) return;
    const kabSet = new Set();
    window.PETA_SLS.features.forEach(f => {
        if (f.properties && f.properties.nmkab) kabSet.add(f.properties.nmkab);
    });
    const kabSelect = document.getElementById('map-filter-kab');
    if (kabSelect) {
        Array.from(kabSet).sort().forEach(kab => {
            const opt = document.createElement('option');
            opt.value = kab;
            opt.textContent = kab;
            kabSelect.appendChild(opt);
        });
    }
}

window.updateMapKecFilter = function() {
    const kab = document.getElementById('map-filter-kab').value;
    const kecSelect = document.getElementById('map-filter-kec');
    kecSelect.innerHTML = '<option value="">Semua Kecamatan</option>';
    if (!kab || !window.PETA_SLS) {
        window.searchMap();
        return;
    }
    
    const kecSet = new Set();
    window.PETA_SLS.features.forEach(f => {
        if (f.properties && f.properties.nmkab === kab && f.properties.nmkec) {
            kecSet.add(f.properties.nmkec);
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
        slsOpenMap.fitBounds(slsMapLayer.getBounds());
        return;
    }

    let foundLayers = [];
    slsMapLayer.eachLayer(function(layer) {
        const p = layer.feature.properties || {};
        
        let matchKab = !filterKab || (p.nmkab === filterKab);
        let matchKec = !filterKec || (p.nmkec === filterKec);
        
        let matchQuery = true;
        if (query) {
            const featureId = "72" + (p.kdkab || "") + (p.kdkec || "") + (p.kddesa || "") + (p.kdsls || "") + (p.kdsubsls || "");
            matchQuery = false;
            if (featureId.includes(query)) matchQuery = true;
            if (!matchQuery) {
                for (let key in p) {
                    if (String(p[key]).toLowerCase().includes(query)) {
                        matchQuery = true;
                        break;
                    }
                }
            }
        }
        
        if (matchKab && matchKec && matchQuery) {
            foundLayers.push(layer);
        }
    });

    if (foundLayers.length > 0) {
        let group = L.featureGroup(foundLayers);
        slsOpenMap.fitBounds(group.getBounds(), { maxZoom: 15 });
        
        if (foundLayers.length === 1 && query) { 
            let layer = foundLayers[0];
            window.lastSearchedLayer = layer;
            if (layer.setStyle) {
                layer.setStyle({
                    color: "#fde047", 
                    weight: 4,
                    opacity: 1,
                    fillColor: "#fef08a", 
                    fillOpacity: 0.9
                });
            }
            layer.openPopup();
        }
    } else {
        if (query) alert("Pencarian tidak ditemukan di peta.");
    }
};

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
    
    // Style the row immediately without full re-render to avoid losing focus
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
