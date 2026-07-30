// State Rekonsiliasi
let rekonSlsData = [];
let rekonPetugasData = [];
let currentRekonSubTab = 'sls';
let rekonSortConfig = {
    sls: { key: 'diff_fasih_vs_muatan_total', dir: 'desc' },
    petugas: { key: 'diff_fasih_vs_muatan', dir: 'desc' }
};

// Load Data

async function loadRekonData() {
    try {
        const resSls = await fetch('rekon_sls.json?v=' + Date.now());
        rekonSlsData = await resSls.json();
        const resPetugas = await fetch('rekon_petugas.json?v=' + Date.now());
        rekonPetugasData = await resPetugas.json();
        
        initRekonFilters();
        renderRekon();
    } catch (e) {
        console.error("Gagal load data rekon:", e);
    }
}


function getUniqueValues(data, key, filters = {}) {
    let filtered = data;
    for (const [k, v] of Object.entries(filters)) {
        if (v) {
            filtered = filtered.filter(item => item[k] === v);
        }
    }
    const set = new Set();
    filtered.forEach(d => {
        if (d[key]) set.add(d[key]);
    });
    return Array.from(set).sort();
}

function populateSelect(id, values, defaultText) {
    const select = document.getElementById(id);
    select.innerHTML = `<option value="">${defaultText}</option>`;
    values.forEach(v => {
        const opt = document.createElement('option');
        opt.value = v;
        opt.textContent = v;
        select.appendChild(opt);
    });
}

function initRekonFilters() {
    // Populate Kab
    const kabs = getUniqueValues(rekonSlsData, 'nmkab');
    populateSelect('rekon-filter-kab', kabs, 'Semua Kab');
    
    // Populate Petugas for Petugas Tab
    const petugasSet = new Set();
    rekonPetugasData.forEach(d => petugasSet.add(d.email));
    populateSelect('rekon-filter-petugas', Array.from(petugasSet).sort(), 'Semua Petugas');
}

function updateKec() {
    const kab = document.getElementById('rekon-filter-kab').value;
    const kecs = getUniqueValues(rekonSlsData, 'nmkec', { nmkab: kab });
    populateSelect('rekon-filter-kec', kecs, 'Semua Kec');
    updateDesa();
}

function updateDesa() {
    const kab = document.getElementById('rekon-filter-kab').value;
    const kec = document.getElementById('rekon-filter-kec').value;
    const desas = getUniqueValues(rekonSlsData, 'nmdesa', { nmkab: kab, nmkec: kec });
    populateSelect('rekon-filter-desa', desas, 'Semua Desa');
    updateSls();
}

function updateSls() {
    const kab = document.getElementById('rekon-filter-kab').value;
    const kec = document.getElementById('rekon-filter-kec').value;
    const desa = document.getElementById('rekon-filter-desa').value;
    const slss = getUniqueValues(rekonSlsData, 'nmsls', { nmkab: kab, nmkec: kec, nmdesa: desa });
    populateSelect('rekon-filter-sls', slss, 'Semua SLS');
}


function switchRekonSubTab(subTab) {
    currentRekonSubTab = subTab;
    document.getElementById('rekon-sub-btn-sls').classList.toggle('active', subTab === 'sls');
    document.getElementById('rekon-sub-btn-petugas').classList.toggle('active', subTab === 'petugas');
    
    document.getElementById('rekon-sub-sls').style.display = subTab === 'sls' ? 'block' : 'none';
    document.getElementById('rekon-sub-petugas').style.display = subTab === 'petugas' ? 'block' : 'none';
    
    // Toggle relevant filters
    const showSlsFilters = subTab === 'sls';
    document.getElementById('rekon-filter-kab').style.display = showSlsFilters ? 'inline-block' : 'none';
    document.getElementById('rekon-filter-kec').style.display = showSlsFilters ? 'inline-block' : 'none';
    document.getElementById('rekon-filter-desa').style.display = showSlsFilters ? 'inline-block' : 'none';
    document.getElementById('rekon-filter-sls').style.display = showSlsFilters ? 'inline-block' : 'none';
    document.getElementById('rekon-filter-petugas').style.display = !showSlsFilters ? 'inline-block' : 'none';
    
    renderRekon();
}

function sortRekon(type, key) {
    if (rekonSortConfig[type].key === key) {
        rekonSortConfig[type].dir = rekonSortConfig[type].dir === 'asc' ? 'desc' : 'asc';
    } else {
        rekonSortConfig[type].key = key;
        rekonSortConfig[type].dir = 'desc';
    }
    renderRekon();
}

function renderRekon() {
    const search = document.getElementById('rekon-filter-search').value.toLowerCase();
    
    if (currentRekonSubTab === 'sls') {
        const kab = document.getElementById('rekon-filter-kab').value;
        const kec = document.getElementById('rekon-filter-kec').value;
        const desa = document.getElementById('rekon-filter-desa').value;
        const sls = document.getElementById('rekon-filter-sls').value;

        let filtered = rekonSlsData.filter(d => {
            const matchSearch = String(d.sls_id).toLowerCase().includes(search) || 
                                (d.nmdesa && String(d.nmdesa).toLowerCase().includes(search));
            const matchKab = !kab || d.nmkab === kab;
            const matchKec = !kec || d.nmkec === kec;
            const matchDesa = !desa || d.nmdesa === desa;
            const matchSls = !sls || d.nmsls === sls;
            return matchSearch && matchKab && matchKec && matchDesa && matchSls;
        });

        const sortKey = rekonSortConfig.sls.key;
        const sortDir = rekonSortConfig.sls.dir === 'asc' ? 1 : -1;
        filtered.sort((a, b) => {
            let valA = a[sortKey];
            let valB = b[sortKey];
            if (typeof valA === 'string') valA = valA.toLowerCase();
            if (typeof valB === 'string') valB = valB.toLowerCase();
            if (valA < valB) return -1 * sortDir;
            if (valA > valB) return 1 * sortDir;
            return 0;
        });

        const tbody = document.getElementById('rekon-table-sls');
        tbody.innerHTML = '';
        let totMuatan = 0, totFasih = 0;

        filtered.forEach(d => {
            totMuatan += d.total_muatan || 0;
            totFasih += d.fasih_target_pencacah || 0;
            const diff = d.diff_fasih_vs_muatan_total || 0;
            const diffColor = diff > 0 ? '#b91c1c' : (diff < 0 ? '#0369a1' : 'inherit');
            
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${d.sls_id}</td>
                <td>${d.nmkab} - ${d.nmkec} - ${d.nmdesa} - ${d.nmsls}</td>
                <td style="text-align: right;">${d.total_muatan.toLocaleString('id-ID')}</td>
                <td style="text-align: right;">${d.fasih_target_pencacah.toLocaleString('id-ID')}</td>
                <td style="text-align: right; color: ${diffColor}; font-weight: bold;">${diff.toLocaleString('id-ID')}</td>
            `;
            tbody.appendChild(tr);
        });

        // Update Summary Cards
        document.getElementById('rekon-summary').innerHTML = `
            <div class="summary-card"><div class="label">Total SLS Filtered</div><div class="value">${filtered.length}</div></div>
            <div class="summary-card"><div class="label">Total Muatan (UTP+SBR+Kel)</div><div class="value">${totMuatan.toLocaleString('id-ID')}</div></div>
            <div class="summary-card"><div class="label">Total Target Fasih</div><div class="value">${totFasih.toLocaleString('id-ID')}</div></div>
            <div class="summary-card"><div class="label">Total Selisih (Fasih - Muatan)</div><div class="value" style="color: ${totFasih - totMuatan > 0 ? '#b91c1c' : 'inherit'}">${(totFasih - totMuatan).toLocaleString('id-ID')}</div></div>
        `;

    } else {
        // Petugas
        const emailFilter = document.getElementById('rekon-filter-petugas').value;
        
        let filtered = rekonPetugasData.filter(d => {
            const matchSearch = String(d.email).toLowerCase().includes(search);
            const matchEmail = !emailFilter || d.email === emailFilter;
            return matchSearch && matchEmail;
        });

        const sortKey = rekonSortConfig.petugas.key;
        const sortDir = rekonSortConfig.petugas.dir === 'asc' ? 1 : -1;
        filtered.sort((a, b) => {
            let valA = a[sortKey];
            let valB = b[sortKey];
            if (valA < valB) return -1 * sortDir;
            if (valA > valB) return 1 * sortDir;
            return 0;
        });

        const tbody = document.getElementById('rekon-table-petugas');
        tbody.innerHTML = '';
        
        let totMuatan = 0, totFasih = 0, totSql = 0;

        filtered.forEach(d => {
            totMuatan += d.total_muatan_assigned || 0;
            totFasih += d.total_fasih || 0;
            totSql += d.total_sqllab || 0;

            const diffMuatan = d.diff_fasih_vs_muatan || 0;
            const diffSql = d.diff_fasih_vs_sqllab || 0;
            
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${d.email}</td>
                <td style="text-align: right;">${d.total_muatan_assigned.toLocaleString('id-ID')}</td>
                <td style="text-align: right;">${d.total_fasih.toLocaleString('id-ID')}</td>
                <td style="text-align: right;">${d.total_sqllab.toLocaleString('id-ID')}</td>
                <td style="text-align: right; color: ${diffMuatan > 0 ? '#b91c1c' : 'inherit'}">${diffMuatan.toLocaleString('id-ID')}</td>
                <td style="text-align: right; color: ${diffSql > 0 ? '#b91c1c' : 'inherit'}">${diffSql.toLocaleString('id-ID')}</td>
            `;
            tbody.appendChild(tr);
        });

        // Update Summary Cards
        document.getElementById('rekon-summary').innerHTML = `
            <div class="summary-card"><div class="label">Total Petugas</div><div class="value">${filtered.length}</div></div>
            <div class="summary-card"><div class="label">Total Beban Muatan</div><div class="value">${totMuatan.toLocaleString('id-ID')}</div></div>
            <div class="summary-card"><div class="label">Total Target Fasih</div><div class="value">${totFasih.toLocaleString('id-ID')}</div></div>
            <div class="summary-card"><div class="label">Selisih Fasih vs Muatan</div><div class="value" style="color: ${totFasih - totMuatan > 0 ? '#b91c1c' : 'inherit'}">${(totFasih - totMuatan).toLocaleString('id-ID')}</div></div>
        `;
    }
}

// Ensure data is loaded when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    loadRekonData();
});
