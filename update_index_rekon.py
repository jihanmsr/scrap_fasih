import re

with open('index.html', 'r') as f:
    content = f.read()

# Replace SLS Table Headers
old_sls_thead = """                    <tr>
                        <th class="sortable" onclick="sortRekon('sls', 'sls_id')">ID SLS</th>
                        <th class="sortable" onclick="sortRekon('sls', 'nmkab')">Kab/Kec/Desa</th>
                        <th class="sortable" onclick="sortRekon('sls', 'total_muatan')">Total Muatan (UTP+SBR)</th>
                        <th class="sortable" onclick="sortRekon('sls', 'total_sqllab')">Target SQL Lab</th>
                        <th class="sortable" onclick="sortRekon('sls', 'diff_muatan_vs_sqllab')">Selisih (Muatan - SQL Lab)</th>
                    </tr>"""
new_sls_thead = """                    <tr>
                        <th class="sortable" onclick="sortRekon('sls', 'sls_id')">ID SLS</th>
                        <th class="sortable" onclick="sortRekon('sls', 'nmkab')">Kab/Kec/Desa</th>
                        <th class="sortable" onclick="sortRekon('sls', 'target_awal')">Target Awal (UTP+SBR)</th>
                        <th class="sortable" onclick="sortRekon('sls', 'realisasi')">Realisasi (UTP+SBR)</th>
                        <th class="sortable" onclick="sortRekon('sls', 'diff')">Selisih (Realisasi - Target Awal)</th>
                    </tr>"""

# Replace Petugas Table Headers
old_petugas_thead = """                    <tr>
                        <th class="sortable" onclick="sortRekon('petugas', 'email')">Email Petugas</th>
                        <th class="sortable" onclick="sortRekon('petugas', 'total_muatan_assigned')">Beban Muatan (Assign)</th>
                        <th class="sortable" onclick="sortRekon('petugas', 'total_sqllab')">Target SQL Lab</th>
                        <th class="sortable" onclick="sortRekon('petugas', 'diff_muatan_vs_sqllab')">Selisih (Muatan - SQL Lab)</th>
                    </tr>"""
new_petugas_thead = """                    <tr>
                        <th class="sortable" onclick="sortRekon('petugas', 'email')">Email Petugas</th>
                        <th class="sortable" onclick="sortRekon('petugas', 'target_awal')">Target Awal (UTP+SBR)</th>
                        <th class="sortable" onclick="sortRekon('petugas', 'realisasi')">Realisasi (UTP+SBR)</th>
                        <th class="sortable" onclick="sortRekon('petugas', 'diff')">Selisih (Realisasi - Target Awal)</th>
                    </tr>"""

if old_sls_thead in content:
    content = content.replace(old_sls_thead, new_sls_thead)
if old_petugas_thead in content:
    content = content.replace(old_petugas_thead, new_petugas_thead)

with open('index.html', 'w') as f:
    f.write(content)

with open('rekon.js', 'r') as f:
    rcontent = f.read()

rcontent = re.sub(r"let rekonSortConfig = \{.*?^\};" , 
    "let rekonSortConfig = {\n    sls: { key: 'diff', dir: 'desc' },\n    petugas: { key: 'diff', dir: 'desc' }\n};",
    rcontent, flags=re.MULTILINE | re.DOTALL)

sls_old = """        let totMuatan = 0, totSql = 0;

        filtered.forEach(d => {
            totMuatan += d.total_muatan || 0;
            totSql += d.total_sqllab || 0;
            const diff = d.diff_muatan_vs_sqllab || 0;
            const diffColor = diff !== 0 ? '#b91c1c' : 'inherit';
            
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${d.sls_id}</td>
                <td>${d.nmkab} - ${d.nmkec} - ${d.nmdesa} - ${d.nmsls}</td>
                <td style="text-align: right;">${d.total_muatan.toLocaleString('id-ID')}</td>
                <td style="text-align: right;">${d.total_sqllab.toLocaleString('id-ID')}</td>
                <td style="text-align: right; color: ${diffColor}; font-weight: bold;">${diff.toLocaleString('id-ID')}</td>
            `;
            tbody.appendChild(tr);
        });

        // Update Summary Cards
        document.getElementById('rekon-summary').innerHTML = `
            <div class="summary-card"><div class="label">Total SLS Filtered</div><div class="value">${filtered.length}</div></div>
            <div class="summary-card"><div class="label">Total Muatan (UTP+SBR)</div><div class="value">${totMuatan.toLocaleString('id-ID')}</div></div>
            <div class="summary-card"><div class="label">Total Target SQL Lab</div><div class="value">${totSql.toLocaleString('id-ID')}</div></div>
            <div class="summary-card"><div class="label">Total Selisih (Muatan - SQL Lab)</div><div class="value" style="color: ${totMuatan - totSql !== 0 ? '#b91c1c' : 'inherit'}">${(totMuatan - totSql).toLocaleString('id-ID')}</div></div>
        `;"""

sls_new = """        let totTarget = 0, totRealisasi = 0;

        filtered.forEach(d => {
            totTarget += d.target_awal || 0;
            totRealisasi += d.realisasi || 0;
            const diff = d.diff || 0;
            const diffColor = diff !== 0 ? '#b91c1c' : 'inherit';
            
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${d.sls_id}</td>
                <td>${d.nmkab} - ${d.nmkec} - ${d.nmdesa} - ${d.nmsls}</td>
                <td style="text-align: right;">${d.target_awal.toLocaleString('id-ID')}</td>
                <td style="text-align: right;">${d.realisasi.toLocaleString('id-ID')}</td>
                <td style="text-align: right; color: ${diffColor}; font-weight: bold;">${diff.toLocaleString('id-ID')}</td>
            `;
            tbody.appendChild(tr);
        });

        // Update Summary Cards
        document.getElementById('rekon-summary').innerHTML = `
            <div class="summary-card"><div class="label">Total SLS Filtered</div><div class="value">${filtered.length}</div></div>
            <div class="summary-card"><div class="label">Total Target Awal (UTP+SBR)</div><div class="value">${totTarget.toLocaleString('id-ID')}</div></div>
            <div class="summary-card"><div class="label">Total Realisasi (UTP+SBR)</div><div class="value">${totRealisasi.toLocaleString('id-ID')}</div></div>
            <div class="summary-card"><div class="label">Total Selisih (Realisasi - Target Awal)</div><div class="value" style="color: ${totRealisasi - totTarget !== 0 ? '#b91c1c' : 'inherit'}">${(totRealisasi - totTarget).toLocaleString('id-ID')}</div></div>
        `;"""

petugas_old = """        let totMuatan = 0, totSql = 0;

        filtered.forEach(d => {
            totMuatan += d.total_muatan_assigned || 0;
            totSql += d.total_sqllab || 0;

            const diff = d.diff_muatan_vs_sqllab || 0;
            const diffColor = diff !== 0 ? '#b91c1c' : 'inherit';
            
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${d.email}</td>
                <td style="text-align: right;">${d.total_muatan_assigned.toLocaleString('id-ID')}</td>
                <td style="text-align: right;">${d.total_sqllab.toLocaleString('id-ID')}</td>
                <td style="text-align: right; color: ${diffColor}; font-weight: bold;">${diff.toLocaleString('id-ID')}</td>
            `;
            tbody.appendChild(tr);
        });

        // Update Summary Cards
        document.getElementById('rekon-summary').innerHTML = `
            <div class="summary-card"><div class="label">Total Petugas</div><div class="value">${filtered.length}</div></div>
            <div class="summary-card"><div class="label">Total Beban Muatan</div><div class="value">${totMuatan.toLocaleString('id-ID')}</div></div>
            <div class="summary-card"><div class="label">Total Target SQL Lab</div><div class="value">${totSql.toLocaleString('id-ID')}</div></div>
            <div class="summary-card"><div class="label">Selisih Muatan vs SQL Lab</div><div class="value" style="color: ${totMuatan - totSql !== 0 ? '#b91c1c' : 'inherit'}">${(totMuatan - totSql).toLocaleString('id-ID')}</div></div>
        `;"""

petugas_new = """        let totTarget = 0, totRealisasi = 0;

        filtered.forEach(d => {
            totTarget += d.target_awal || 0;
            totRealisasi += d.realisasi || 0;

            const diff = d.diff || 0;
            const diffColor = diff !== 0 ? '#b91c1c' : 'inherit';
            
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${d.email}</td>
                <td style="text-align: right;">${d.target_awal.toLocaleString('id-ID')}</td>
                <td style="text-align: right;">${d.realisasi.toLocaleString('id-ID')}</td>
                <td style="text-align: right; color: ${diffColor}; font-weight: bold;">${diff.toLocaleString('id-ID')}</td>
            `;
            tbody.appendChild(tr);
        });

        // Update Summary Cards
        document.getElementById('rekon-summary').innerHTML = `
            <div class="summary-card"><div class="label">Total Petugas</div><div class="value">${filtered.length}</div></div>
            <div class="summary-card"><div class="label">Total Target Awal (UTP+SBR)</div><div class="value">${totTarget.toLocaleString('id-ID')}</div></div>
            <div class="summary-card"><div class="label">Total Realisasi (UTP+SBR)</div><div class="value">${totRealisasi.toLocaleString('id-ID')}</div></div>
            <div class="summary-card"><div class="label">Selisih Realisasi vs Target Awal</div><div class="value" style="color: ${totRealisasi - totTarget !== 0 ? '#b91c1c' : 'inherit'}">${(totRealisasi - totTarget).toLocaleString('id-ID')}</div></div>
        `;"""

if sls_old in rcontent:
    rcontent = rcontent.replace(sls_old, sls_new)
if petugas_old in rcontent:
    rcontent = rcontent.replace(petugas_old, petugas_new)

with open('rekon.js', 'w') as f:
    f.write(rcontent)

