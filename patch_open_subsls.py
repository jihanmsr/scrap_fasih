import re

with open('open_subsls.js', 'r', encoding='utf-8') as f:
    js = f.read()

new_leaflet_code = '''
    try {
        window._osmTile = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap'
        });
        window._esriTile = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
            attribution: '&copy; Esri World Imagery'
        });

        slsOpenMap = L.map('sls-open-map', {
            center: [-1.4300, 121.4456],
            zoom: 6,
            layers: [window._esriTile],
            zoomControl: true
        });

        const geoData = window.PETA_SLS;
        const highlightedData = window.HIGHLIGHTED_SUBSLS || {};

        slsMapLayer = L.geoJSON(geoData, {
            style: function (feature) {
                const p = feature.properties || {};
                const featureId = "72" + (p.kdkab || "") + (p.kdkec || "") + (p.kddesa || "") + (p.kdsls || "") + (p.kdsubsls || "");
                
                if (highlightedData[featureId]) {
                    return {
                        color: "#ff6b00",
                        weight: 3.5,
                        opacity: 1,
                        fillColor: "#ff6b00",
                        fillOpacity: 0.12
                    };
                } else {
                    return {
                        color: "#3b82f6",
                        weight: 1.5,
                        opacity: 0.8,
                        fillColor: "#60a5fa",
                        fillOpacity: 0.05
                    };
                }
            },
            onEachFeature: function (feature, layer) {
                if (feature.properties) {
                    const p = feature.properties;
                    const featureId = "72" + (p.kdkab || "") + (p.kdkec || "") + (p.kddesa || "") + (p.kdsls || "") + (p.kdsubsls || "");
                    
                    let popupContent = '<div style="max-height: 220px; overflow-y: auto; font-family: sans-serif;"><b>Detail SLS</b><br>';
                    for (let key in feature.properties) {
                        popupContent += `<b>${key}</b>: ${feature.properties[key]}<br>`;
                    }
                    popupContent += `<b>Kode Sub SLS Lengkap</b>: ${featureId}<br>`;
                    
                    if (highlightedData[featureId]) {
                        const csv = highlightedData[featureId];
                        popupContent += `<br><div style="padding: 8px; background: #fff7ed; border: 1px solid #ffedd5; border-radius: 6px; font-size: 0.9em; margin-top: 5px;">`;
                        popupContent += `<b style="color:#ea580c;">🎯 SLS FULL OPEN:</b><br>`;
                        popupContent += `<b>Petugas:</b> ${csv.nama_petugas || '-'}<br>`;
                        popupContent += `<b>Nama Sub SLS:</b> ${csv.nama_sub_sls || csv.sls || '-'}<br>`;
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
        populateDrawerFilters();
        
    } catch(err) {
        console.error("Error loading map data:", err);
    }
'''

init_idx = js.find('function initSlsMap() {')
if init_idx != -1:
    end_init = js.find('function populateMapFilters()', init_idx)
    if end_init != -1:
        prefix = js[:init_idx]
        suffix = js[end_init:]
        js = prefix + 'function initSlsMap() {\n    if (slsOpenMap) return;\n    const mapContainer = document.getElementById("sls-open-map");\n    if (!mapContainer) return;\n' + new_leaflet_code + '\n}\n\n' + suffix

handlers_code = '''
// ── Map Floating Pill Overlay Handlers ─────────────────────────────────────
window.toggleWilayahDrawer = function() {
    const drawer = document.getElementById("map-wilayah-drawer");
    if (!drawer) return;
    const isVisible = drawer.style.display !== "none";
    drawer.style.display = isVisible ? "none" : "block";
    document.getElementById("map-keberadaan-popup").style.display = "none";
    document.getElementById("map-basemap-popup").style.display = "none";
};

window.toggleKeberadaanPopup = function() {
    const popup = document.getElementById("map-keberadaan-popup");
    if (!popup) return;
    const isVisible = popup.style.display !== "none";
    popup.style.display = isVisible ? "none" : "block";
    document.getElementById("map-wilayah-drawer").style.display = "none";
    document.getElementById("map-basemap-popup").style.display = "none";
};

window.toggleBaseMapPopup = function() {
    const popup = document.getElementById("map-basemap-popup");
    if (!popup) return;
    const isVisible = popup.style.display !== "none";
    popup.style.display = isVisible ? "none" : "block";
    document.getElementById("map-wilayah-drawer").style.display = "none";
    document.getElementById("map-keberadaan-popup").style.display = "none";
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

window.filterKeberadaan = function(type) {
    document.querySelectorAll(".btn-keb-filter").forEach(btn => {
        if (btn.getAttribute("data-keb") === type) {
            btn.style.background = "#4f46e5";
            btn.style.color = "#ffffff";
            btn.style.border = "none";
        } else {
            btn.style.background = "#f8fafc";
            btn.style.color = "#334155";
            btn.style.border = "1px solid #e2e8f0";
        }
    });
    document.getElementById("map-keberadaan-popup").style.display = "none";
};

window.onSqlLabClick = function() {
    alert("SQL Lab Data: Menampilkan data usaha terhubung database SQL Lab.");
};

function populateDrawerFilters() {
    if (!window.PETA_SLS) return;
    const kabSet = new Set();
    window.PETA_SLS.features.forEach(f => {
        if (f.properties && f.properties.nmkab) kabSet.add(f.properties.nmkab);
    });
    const kabSel = document.getElementById("drawer-map-filter-kab");
    if (kabSel && kabSel.options.length === 1) {
        Array.from(kabSet).sort().forEach(kab => {
            const opt = document.createElement("option");
            opt.value = kab;
            opt.textContent = kab;
            kabSel.appendChild(opt);
        });
    }
}

window.onDrawerKabChange = function() {
    const kab = document.getElementById("drawer-map-filter-kab").value;
    const kecSel = document.getElementById("drawer-map-filter-kec");
    const desaSel = document.getElementById("drawer-map-filter-desa");
    const slsSel = document.getElementById("drawer-map-filter-sls");
    
    kecSel.innerHTML = "<option value=''>Semua Kecamatan</option>";
    desaSel.innerHTML = "<option value=''>Semua Desa</option>";
    slsSel.innerHTML = "<option value=''>--- Pilih SLS ---</option>";
    
    if (!kab || !window.PETA_SLS) return;
    
    const kecSet = new Set();
    window.PETA_SLS.features.forEach(f => {
        if (f.properties && f.properties.nmkab === kab && f.properties.nmkec) kecSet.add(f.properties.nmkec);
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
    
    if (!kec || !window.PETA_SLS) return;
    
    const desaSet = new Set();
    window.PETA_SLS.features.forEach(f => {
        if (f.properties && f.properties.nmkab === kab && f.properties.nmkec === kec && f.properties.nmdesa) desaSet.add(f.properties.nmdesa);
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
    if (!desa || !window.PETA_SLS) return;
    
    const slsSet = new Set();
    window.PETA_SLS.features.forEach(f => {
        if (f.properties && f.properties.nmkab === kab && f.properties.nmkec === kec && f.properties.nmdesa === desa) {
            slsSet.add(f.properties.nmsls || f.properties.sls || f.properties.kdsls);
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
'''

if 'toggleWilayahDrawer' not in js:
    js += '\n' + handlers_code

with open('open_subsls.js', 'w', encoding='utf-8') as f:
    f.write(js)

print('Updated open_subsls.js OK!')
