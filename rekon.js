// State Rekonsiliasi
let rekonSlsData = [];
let rekonPetugasData = [];
let currentRekonSubTab = 'sls';
let rekonSortConfig = {
    sls: { key: 'diff', dir: 'desc' },
    petugas: { key: 'diff', dir: 'desc' }
};

// Load Data

async function loadRekonData() {
    try {
        if (window.rekonSlsData) rekonSlsData = window.rekonSlsData;
        if (window.rekonPetugasData) rekonPetugasData = window.rekonPetugasData;

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
            let valA, valB;
            if (sortKey === 'muatan_utp') { valA = a.jml_utp_subsektor || 0; valB = b.jml_utp_subsektor || 0; }
            else if (sortKey === 'realisasi_utp') { valA = a.total_utp || 0; valB = b.total_utp || 0; }
            else if (sortKey === 'diff_utp') { valA = (a.total_utp || 0) - (a.jml_utp_subsektor || 0); valB = (b.total_utp || 0) - (b.jml_utp_subsektor || 0); }
            else if (sortKey === 'muatan_sbr') { valA = a.Total_usaha_SBR || 0; valB = b.Total_usaha_SBR || 0; }
            else if (sortKey === 'realisasi_sbr') { valA = a.total_sbr || 0; valB = b.total_sbr || 0; }
            else if (sortKey === 'diff_sbr') { valA = (a.total_sbr || 0) - (a.Total_usaha_SBR || 0); valB = (b.total_sbr || 0) - (b.Total_usaha_SBR || 0); }
            else if (sortKey === 'muatan_keluarga') { valA = a.keluarga || 0; valB = b.keluarga || 0; }
            else if (sortKey === 'realisasi_keluarga') { valA = 0; valB = 0; }
            else if (sortKey === 'diff_keluarga') { valA = -(a.keluarga || 0); valB = -(b.keluarga || 0); }
            else { valA = a[sortKey]; valB = b[sortKey]; }

            if (typeof valA === 'string') valA = valA.toLowerCase();
            if (typeof valB === 'string') valB = valB.toLowerCase();
            if (valA < valB) return -1 * sortDir;
            if (valA > valB) return 1 * sortDir;
            return 0;
        });

        const tbody = document.getElementById('rekon-table-sls');
        tbody.innerHTML = '';
        let m_utp_tot = 0, r_utp_tot = 0;
        let m_sbr_tot = 0, r_sbr_tot = 0;
        let m_kel_tot = 0, r_kel_tot = 0;

        filtered.forEach(d => {
            const m_utp = d.jml_utp_subsektor || 0;
            const m_sbr = d.Total_usaha_SBR || 0;
            const m_kel = d.keluarga || 0;
            
            const r_utp = d.total_utp || 0;
            const r_sbr = d.total_sbr || 0;
            const r_kel = 0; // Not available in SLS data
            
            m_utp_tot += m_utp; r_utp_tot += r_utp;
            m_sbr_tot += m_sbr; r_sbr_tot += r_sbr;
            m_kel_tot += m_kel; r_kel_tot += r_kel;

            const diff_utp = r_utp - m_utp;
            const diff_sbr = r_sbr - m_sbr;
            const diff_kel = r_kel - m_kel;

            const diffColorUTP = diff_utp < 0 ? '#b91c1c' : (diff_utp > 0 ? '#15803d' : 'inherit');
            const diffColorSBR = diff_sbr < 0 ? '#b91c1c' : (diff_sbr > 0 ? '#15803d' : 'inherit');
            const diffColorKel = diff_kel < 0 ? '#b91c1c' : (diff_kel > 0 ? '#15803d' : 'inherit');

            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${d.sls_id}</td>
                <td>${d.nmkab} - ${d.nmkec} - ${d.nmdesa} - ${d.nmsls}</td>
                <td style="text-align: right;">${m_utp.toLocaleString('id-ID')}</td>
                <td style="text-align: right;">${r_utp.toLocaleString('id-ID')}</td>
                <td style="text-align: right; color: ${diffColorUTP}; font-weight: bold;">${diff_utp.toLocaleString('id-ID')}</td>
                <td style="text-align: right;">${m_sbr.toLocaleString('id-ID')}</td>
                <td style="text-align: right;">${r_sbr.toLocaleString('id-ID')}</td>
                <td style="text-align: right; color: ${diffColorSBR}; font-weight: bold;">${diff_sbr.toLocaleString('id-ID')}</td>
                <td style="text-align: right;">${m_kel.toLocaleString('id-ID')}</td>
                <td style="text-align: right;">${r_kel.toLocaleString('id-ID')}</td>
                <td style="text-align: right; color: ${diffColorKel}; font-weight: bold;">${diff_kel.toLocaleString('id-ID')}</td>
            `;
            tbody.appendChild(tr);
        });

        // Update Summary Cards
        document.getElementById('rekon-summary').innerHTML = `
            <div class="summary-card"><div class="label">Total SLS Filtered</div><div class="value">${filtered.length}</div></div>
            <div class="summary-card"><div class="label">UTP (Rls/Muatan)</div><div class="value">${r_utp_tot.toLocaleString('id-ID')} / ${m_utp_tot.toLocaleString('id-ID')}</div></div>
            <div class="summary-card"><div class="label">SBR (Rls/Muatan)</div><div class="value">${r_sbr_tot.toLocaleString('id-ID')} / ${m_sbr_tot.toLocaleString('id-ID')}</div></div>
            <div class="summary-card"><div class="label">Keluarga (Rls/Muatan)</div><div class="value">${r_kel_tot.toLocaleString('id-ID')} / ${m_kel_tot.toLocaleString('id-ID')}</div></div>
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
            let valA, valB;
            if (sortKey === 'muatan_utp') { valA = a.total_muatan_assigned || 0; valB = b.total_muatan_assigned || 0; }
            else if (sortKey === 'realisasi_utp') { valA = a.total_usaha || 0; valB = b.total_usaha || 0; }
            else if (sortKey === 'diff_utp') { valA = (a.total_usaha || 0) - (a.total_muatan_assigned || 0); valB = (b.total_usaha || 0) - (b.total_muatan_assigned || 0); }
            else if (sortKey === 'muatan_sbr') { valA = 0; valB = 0; }
            else if (sortKey === 'realisasi_sbr') { valA = 0; valB = 0; }
            else if (sortKey === 'diff_sbr') { valA = 0; valB = 0; }
            else if (sortKey === 'muatan_keluarga') { valA = 0; valB = 0; }
            else if (sortKey === 'realisasi_keluarga') { valA = a.total_keluarga || 0; valB = b.total_keluarga || 0; }
            else if (sortKey === 'diff_keluarga') { valA = a.total_keluarga || 0; valB = b.total_keluarga || 0; }
            else { valA = a[sortKey]; valB = b[sortKey]; }

            if (typeof valA === 'string') valA = valA.toLowerCase();
            if (typeof valB === 'string') valB = valB.toLowerCase();
            if (valA < valB) return -1 * sortDir;
            if (valA > valB) return 1 * sortDir;
            return 0;
        });

        const tbody = document.getElementById('rekon-table-petugas');
        tbody.innerHTML = '';

        let m_utp_tot = 0, r_utp_tot = 0;
        let m_sbr_tot = 0, r_sbr_tot = 0;
        let m_kel_tot = 0, r_kel_tot = 0;

        filtered.forEach(d => {
            const m_utp = d.total_muatan_assigned || 0;
            const m_sbr = 0; // Not separated in data
            const m_kel = 0; // Not separated in data

            const r_utp = d.total_usaha || 0;
            const r_sbr = 0; // Not separated in data
            const r_kel = d.total_keluarga || 0;

            m_utp_tot += m_utp; r_utp_tot += r_utp;
            m_sbr_tot += m_sbr; r_sbr_tot += r_sbr;
            m_kel_tot += m_kel; r_kel_tot += r_kel;

            const diff_utp = r_utp - m_utp;
            const diff_sbr = r_sbr - m_sbr;
            const diff_kel = r_kel - m_kel;

            const diffColorUTP = diff_utp < 0 ? '#b91c1c' : (diff_utp > 0 ? '#15803d' : 'inherit');
            const diffColorSBR = diff_sbr < 0 ? '#b91c1c' : (diff_sbr > 0 ? '#15803d' : 'inherit');
            const diffColorKel = diff_kel < 0 ? '#b91c1c' : (diff_kel > 0 ? '#15803d' : 'inherit');

            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${d.email}</td>
                <td style="text-align: right;">${m_utp.toLocaleString('id-ID')}</td>
                <td style="text-align: right;">${r_utp.toLocaleString('id-ID')}</td>
                <td style="text-align: right; color: ${diffColorUTP}; font-weight: bold;">${diff_utp.toLocaleString('id-ID')}</td>
                <td style="text-align: right;">${m_sbr.toLocaleString('id-ID')}</td>
                <td style="text-align: right;">${r_sbr.toLocaleString('id-ID')}</td>
                <td style="text-align: right; color: ${diffColorSBR}; font-weight: bold;">${diff_sbr.toLocaleString('id-ID')}</td>
                <td style="text-align: right;">${m_kel.toLocaleString('id-ID')}</td>
                <td style="text-align: right;">${r_kel.toLocaleString('id-ID')}</td>
                <td style="text-align: right; color: ${diffColorKel}; font-weight: bold;">${diff_kel.toLocaleString('id-ID')}</td>
            `;
            tbody.appendChild(tr);
        });

        // Update Summary Cards
        document.getElementById('rekon-summary').innerHTML = `
            <div class="summary-card"><div class="label">Total Petugas</div><div class="value">${filtered.length}</div></div>
            <div class="summary-card"><div class="label">UTP (Rls/Muatan)</div><div class="value">${r_utp_tot.toLocaleString('id-ID')} / ${m_utp_tot.toLocaleString('id-ID')}</div></div>
            <div class="summary-card"><div class="label">SBR (Rls/Muatan)</div><div class="value">${r_sbr_tot.toLocaleString('id-ID')} / ${m_sbr_tot.toLocaleString('id-ID')}</div></div>
            <div class="summary-card"><div class="label">Keluarga (Rls/Muatan)</div><div class="value">${r_kel_tot.toLocaleString('id-ID')} / ${m_kel_tot.toLocaleString('id-ID')}</div></div>
        `;
    }
}

// Ensure data is loaded when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    loadRekonData();
});
