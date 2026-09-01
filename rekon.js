// State Rekonsiliasi
let rekonSlsData = [];
let rekonPetugasData = [];
let currentRekonSubTab = 'sls';
let rekonSortConfig = {
    sls: { key: 'diff', dir: 'desc' },
    petugas: { key: 'diff', dir: 'desc' },
    kabkot: { key: 'nmkab', dir: 'asc' }
};

// Load Data


async function loadRekonData() {
    try {
        if (window.rekonSlsData) {
            // Clean up garbage rows (e.g., nmkab is 0 or '-')
            rekonSlsData = window.rekonSlsData.filter(d => d.nmkab && d.nmkab !== 0 && d.nmkab !== '-');
            
            rekonSlsData.forEach(d => {
                if (typeof d.nmkab === 'string') {
                    d.nmkab = d.nmkab.replace(/^\[\d+\]\s*/, '');
                }
            });
            
            // Remove .0 from sls_id if present
            rekonSlsData.forEach(d => {
                if (typeof d.sls_id === 'number') {
                    d.sls_id = d.sls_id.toString().replace(/\.0$/, '');
                } else if (typeof d.sls_id === 'string') {
                    d.sls_id = d.sls_id.replace(/\.0$/, '');
                }
            });
        }
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
    let arr = Array.from(set).sort();
    if (key === 'nmkab' || key === 'kab_name' || key === 'kab') {
        arr.sort(window.sortKabupatenCallback);
    }
    return arr;
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
    document.getElementById('rekon-sub-btn-kabkot').classList.toggle('active', subTab === 'kabkot');
    document.getElementById('rekon-sub-btn-petugas').classList.toggle('active', subTab === 'petugas');

    document.getElementById('rekon-sub-sls').style.display = subTab === 'sls' ? 'block' : 'none';
    document.getElementById('rekon-sub-kabkot').style.display = subTab === 'kabkot' ? 'block' : 'none';
    document.getElementById('rekon-sub-petugas').style.display = subTab === 'petugas' ? 'block' : 'none';


    // Toggle relevant filters
    const showSlsFilters = subTab === 'sls' || subTab === 'kabkot';
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
            else if (sortKey === 'realisasi_keluarga') { valA = a.total_keluarga || 0; valB = b.total_keluarga || 0; }
            else if (sortKey === 'diff_keluarga') { valA = (a.total_keluarga || 0) - (a.keluarga || 0); valB = (b.total_keluarga || 0) - (b.keluarga || 0); }
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
                <td>${d.sls_id}</td>
                <td>${d.nmkab}</td>
                <td>${d.nmkec}</td>
                <td>${d.nmdesa}</td>
                <td>${d.nmsls}</td>
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

    
    } else if (currentRekonSubTab === 'kabkot') {
        const kab = document.getElementById('rekon-filter-kab').value;
        const search = document.getElementById('rekon-filter-search').value.toLowerCase();

        let filtered = rekonSlsData.filter(d => {
            const matchSearch = String(d.nmkab).toLowerCase().includes(search);
            const matchKab = !kab || d.nmkab === kab;
            return matchSearch && matchKab;
        });

        // Group by nmkab
        let kabkotMap = {};
        filtered.forEach(d => {
            if (!d.nmkab) return;
            if (!kabkotMap[d.nmkab]) {
                kabkotMap[d.nmkab] = { nmkab: d.nmkab, m_utp: 0, r_utp: 0, m_sbr: 0, r_sbr: 0, m_kel: 0, r_kel: 0 };
            }
            kabkotMap[d.nmkab].m_utp += (d.jml_utp_subsektor || 0);
            kabkotMap[d.nmkab].r_utp += (d.total_utp || 0);
            kabkotMap[d.nmkab].m_sbr += (d.Total_usaha_SBR || 0);
            kabkotMap[d.nmkab].r_sbr += (d.total_sbr || 0);
            kabkotMap[d.nmkab].m_kel += (d.keluarga || 0);
            kabkotMap[d.nmkab].r_kel += (d.total_keluarga || 0);
        });

        let grouped = Object.values(kabkotMap);

        const sortKey = rekonSortConfig.kabkot.key;
        const sortDir = rekonSortConfig.kabkot.dir === 'asc' ? 1 : -1;
        grouped.sort((a, b) => {
            let valA, valB;
            if (sortKey === 'muatan_utp') { valA = a.m_utp; valB = b.m_utp; }
            else if (sortKey === 'realisasi_utp') { valA = a.r_utp; valB = b.r_utp; }
            else if (sortKey === 'diff_utp') { valA = a.r_utp - a.m_utp; valB = b.r_utp - b.m_utp; }
            else if (sortKey === 'pct_utp') { valA = a.m_utp ? (a.r_utp/a.m_utp)*100 : 0; valB = b.m_utp ? (b.r_utp/b.m_utp)*100 : 0; }
            else if (sortKey === 'muatan_sbr') { valA = a.m_sbr; valB = b.m_sbr; }
            else if (sortKey === 'realisasi_sbr') { valA = a.r_sbr; valB = b.r_sbr; }
            else if (sortKey === 'diff_sbr') { valA = a.r_sbr - a.m_sbr; valB = b.r_sbr - b.m_sbr; }
            else if (sortKey === 'pct_sbr') { valA = a.m_sbr ? (a.r_sbr/a.m_sbr)*100 : 0; valB = b.m_sbr ? (b.r_sbr/b.m_sbr)*100 : 0; }
            else if (sortKey === 'muatan_keluarga') { valA = a.m_kel; valB = b.m_kel; }
            else if (sortKey === 'realisasi_keluarga') { valA = a.r_kel; valB = b.r_kel; }
            else if (sortKey === 'diff_keluarga') { valA = a.r_kel - a.m_kel; valB = b.r_kel - b.m_kel; }
            else if (sortKey === 'pct_keluarga') { valA = a.m_kel ? (a.r_kel/a.m_kel)*100 : 0; valB = b.m_kel ? (b.r_kel/b.m_kel)*100 : 0; }
            else { valA = a[sortKey]; valB = b[sortKey]; }

            if (typeof valA === 'string') valA = valA.toLowerCase();
            if (typeof valB === 'string') valB = valB.toLowerCase();
            if (valA < valB) return -1 * sortDir;
            if (valA > valB) return 1 * sortDir;
            return 0;
        });

        const tbody = document.getElementById('rekon-table-kabkot');
        tbody.innerHTML = '';
        let m_utp_tot = 0, r_utp_tot = 0;
        let m_sbr_tot = 0, r_sbr_tot = 0;
        let m_kel_tot = 0, r_kel_tot = 0;

        grouped.forEach(d => {
            m_utp_tot += d.m_utp; r_utp_tot += d.r_utp;
            m_sbr_tot += d.m_sbr; r_sbr_tot += d.r_sbr;
            m_kel_tot += d.m_kel; r_kel_tot += d.r_kel;

            const diff_utp = d.r_utp - d.m_utp;
            const diff_sbr = d.r_sbr - d.m_sbr;
            const diff_kel = d.r_kel - d.m_kel;

            const diffColorUTP = diff_utp < 0 ? '#b91c1c' : (diff_utp > 0 ? '#15803d' : 'inherit');
            const diffColorSBR = diff_sbr < 0 ? '#b91c1c' : (diff_sbr > 0 ? '#15803d' : 'inherit');
            const diffColorKel = diff_kel < 0 ? '#b91c1c' : (diff_kel > 0 ? '#15803d' : 'inherit');

            const pct_utp = d.m_utp ? ((d.r_utp / d.m_utp) * 100).toFixed(2) : 0;
            const pct_sbr = d.m_sbr ? ((d.r_sbr / d.m_sbr) * 100).toFixed(2) : 0;
            const pct_kel = d.m_kel ? ((d.r_kel / d.m_kel) * 100).toFixed(2) : 0;
            
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${d.nmkab}</td>
                <td style="text-align: right;">${d.m_utp.toLocaleString('id-ID')}</td>
                <td style="text-align: right;">${d.r_utp.toLocaleString('id-ID')}</td>
                <td style="text-align: right; color: ${diffColorUTP}; font-weight: bold;">${diff_utp.toLocaleString('id-ID')}</td>
                <td style="text-align: right;">${pct_utp}%</td>
                <td style="text-align: right;">${d.m_sbr.toLocaleString('id-ID')}</td>
                <td style="text-align: right;">${d.r_sbr.toLocaleString('id-ID')}</td>
                <td style="text-align: right; color: ${diffColorSBR}; font-weight: bold;">${diff_sbr.toLocaleString('id-ID')}</td>
                <td style="text-align: right;">${pct_sbr}%</td>
                <td style="text-align: right;">${d.m_kel.toLocaleString('id-ID')}</td>
                <td style="text-align: right;">${d.r_kel.toLocaleString('id-ID')}</td>
                <td style="text-align: right; color: ${diffColorKel}; font-weight: bold;">${diff_kel.toLocaleString('id-ID')}</td>
                <td style="text-align: right;">${pct_kel}%</td>
            `;
            tbody.appendChild(tr);
        });

        document.getElementById('rekon-summary').innerHTML = `
            <div class="summary-card"><div class="label">Total Kab/Kota Filtered</div><div class="value">${grouped.length}</div></div>
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
            else if (sortKey === 'muatan_sbr') { valA = a.Total_usaha_SBR || 0; valB = b.Total_usaha_SBR || 0; }
            else if (sortKey === 'realisasi_sbr') { valA = a.total_sbr || 0; valB = b.total_sbr || 0; }
            else if (sortKey === 'diff_sbr') { valA = (a.total_sbr || 0) - (a.Total_usaha_SBR || 0); valB = (b.total_sbr || 0) - (b.Total_usaha_SBR || 0); }
            else if (sortKey === 'muatan_keluarga') { valA = a.keluarga || 0; valB = b.keluarga || 0; }
            else if (sortKey === 'realisasi_keluarga') { valA = a.total_keluarga || 0; valB = b.total_keluarga || 0; }
            else if (sortKey === 'diff_keluarga') { valA = (a.total_keluarga || 0) - (a.keluarga || 0); valB = (b.total_keluarga || 0) - (b.keluarga || 0); }
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
            const m_sbr = d.Total_usaha_SBR || 0;
            const m_kel = d.keluarga || 0;

            const r_utp = d.total_usaha || 0;
            const r_sbr = d.total_sbr || 0;
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


window.downloadRekonData = function (format = 'xlsx') {
    const isSls = document.getElementById('rekon-sub-sls') && document.getElementById('rekon-sub-sls').style.display !== 'none';
    const isKab = document.getElementById('rekon-sub-kabkot') && document.getElementById('rekon-sub-kabkot').style.display !== 'none';
    const tableSelector = isSls ? '#rekon-sub-sls table' : (isKab ? '#rekon-sub-kabkot table' : '#rekon-sub-petugas table');
    const table = document.querySelector(tableSelector);
    if (!table) {
        alert("Tabel tidak ditemukan!");
        return;
    }
    const typeName = isSls ? 'sls' : (isKab ? 'kabkot' : 'petugas');
    const dateStr = new Date().toISOString().slice(0, 10);

    if (format === 'xlsx' || format === 'excel') {
        const wb = XLSX.utils.table_to_book(table, { sheet: `Rekon_${typeName}` });
        XLSX.writeFile(wb, `Tabel_Rekon_${typeName}_${dateStr}.xlsx`);
    } else {
        let csv = [];
        let rows = table.querySelectorAll('tr');
        for (let i = 0; i < rows.length; i++) {
            let row = [], cols = rows[i].querySelectorAll('td, th');
            for (let j = 0; j < cols.length; j++) {
                let data = cols[j].innerText.replace(/(\r\n|\n|\r)/gm, ' ').replace(/"/g, '""');
                row.push('"' + data + '"');
            }
            csv.push(row.join(','));
        }
        let blob = new Blob(['\uFEFF' + csv.join('\r\n')], { type: 'text/csv;charset=utf-8;' });
        let link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = `Tabel_Rekon_${typeName}_${dateStr}.csv`;
        link.style.display = "none";
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(link.href);
    }
};
