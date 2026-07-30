import re

with open('rekon.js', 'r') as f:
    content = f.read()

# Update Sort Config
content = re.sub(r"let rekonSortConfig = \{.*?^\};" , 
    "let rekonSortConfig = {\n    sls: { key: 'diff_muatan_vs_sqllab', dir: 'desc' },\n    petugas: { key: 'diff_muatan_vs_sqllab', dir: 'desc' }\n};",
    content, flags=re.MULTILINE | re.DOTALL)

# Update renderRekon SLS part
sls_part_old = """        let totMuatan = 0, totFasih = 0;

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
        `;"""

sls_part_new = """        let totMuatan = 0, totSql = 0;

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

# Update renderRekon Petugas part
petugas_part_old = """        let totMuatan = 0, totFasih = 0, totSql = 0;

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
        `;"""

petugas_part_new = """        let totMuatan = 0, totSql = 0;

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

content = content.replace(sls_part_old, sls_part_new)
content = content.replace(petugas_part_old, petugas_part_new)

with open('rekon.js', 'w') as f:
    f.write(content)

