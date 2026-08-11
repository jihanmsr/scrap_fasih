import re

with open('rekon.js', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update rekonSortConfig
content = content.replace("petugas: { key: 'diff', dir: 'desc' }", "petugas: { key: 'diff', dir: 'desc' },\n    kabkot: { key: 'nmkab', dir: 'asc' }")

# 2. Update switchRekonSubTab
switch_logic = """
    document.getElementById('rekon-sub-btn-sls').classList.toggle('active', subTab === 'sls');
    document.getElementById('rekon-sub-btn-kabkot').classList.toggle('active', subTab === 'kabkot');
    document.getElementById('rekon-sub-btn-petugas').classList.toggle('active', subTab === 'petugas');

    document.getElementById('rekon-sub-sls').style.display = subTab === 'sls' ? 'block' : 'none';
    document.getElementById('rekon-sub-kabkot').style.display = subTab === 'kabkot' ? 'block' : 'none';
    document.getElementById('rekon-sub-petugas').style.display = subTab === 'petugas' ? 'block' : 'none';
"""

# Replace the active toggling inside switchRekonSubTab
content = re.sub(
    r"document\.getElementById\('rekon-sub-btn-sls'\)\.classList\.toggle\('active', subTab === 'sls'\);\s*document\.getElementById\('rekon-sub-btn-petugas'\)\.classList\.toggle\('active', subTab === 'petugas'\);\s*document\.getElementById\('rekon-sub-sls'\)\.style\.display = subTab === 'sls' \? 'block' : 'none';\s*document\.getElementById\('rekon-sub-petugas'\)\.style\.display = subTab === 'petugas' \? 'block' : 'none';",
    switch_logic,
    content
)

# 3. Update filters visibility in switchRekonSubTab
content = content.replace("const showSlsFilters = subTab === 'sls';", "const showSlsFilters = subTab === 'sls' || subTab === 'kabkot';")

# 4. Add kabkot logic in renderRekon
kabkot_render = """
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
            else if (sortKey === 'muatan_sbr') { valA = a.m_sbr; valB = b.m_sbr; }
            else if (sortKey === 'realisasi_sbr') { valA = a.r_sbr; valB = b.r_sbr; }
            else if (sortKey === 'diff_sbr') { valA = a.r_sbr - a.m_sbr; valB = b.r_sbr - b.m_sbr; }
            else if (sortKey === 'muatan_keluarga') { valA = a.m_kel; valB = b.m_kel; }
            else if (sortKey === 'realisasi_keluarga') { valA = a.r_kel; valB = b.r_kel; }
            else if (sortKey === 'diff_keluarga') { valA = a.r_kel - a.m_kel; valB = b.r_kel - b.m_kel; }
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

            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${d.nmkab}</td>
                <td style="text-align: right;">${d.m_utp.toLocaleString('id-ID')}</td>
                <td style="text-align: right;">${d.r_utp.toLocaleString('id-ID')}</td>
                <td style="text-align: right; color: ${diffColorUTP}; font-weight: bold;">${diff_utp.toLocaleString('id-ID')}</td>
                <td style="text-align: right;">${d.m_sbr.toLocaleString('id-ID')}</td>
                <td style="text-align: right;">${d.r_sbr.toLocaleString('id-ID')}</td>
                <td style="text-align: right; color: ${diffColorSBR}; font-weight: bold;">${diff_sbr.toLocaleString('id-ID')}</td>
                <td style="text-align: right;">${d.m_kel.toLocaleString('id-ID')}</td>
                <td style="text-align: right;">${d.r_kel.toLocaleString('id-ID')}</td>
                <td style="text-align: right; color: ${diffColorKel}; font-weight: bold;">${diff_kel.toLocaleString('id-ID')}</td>
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
"""
content = content.replace("} else {\n        // Petugas", kabkot_render)

# Download fixes
content = content.replace("const tableSelector = isSls ? '#rekon-sub-sls table' : '#rekon-sub-petugas table';", "const isKab = document.getElementById('rekon-sub-kabkot').style.display !== 'none';\n    const tableSelector = isSls ? '#rekon-sub-sls table' : (isKab ? '#rekon-sub-kabkot table' : '#rekon-sub-petugas table');")
content = content.replace("let typeName = isSls ? 'sls' : 'petugas';", "let typeName = isSls ? 'sls' : (isKab ? 'kabkot' : 'petugas');")

with open('rekon.js', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated rekon.js successfully")
