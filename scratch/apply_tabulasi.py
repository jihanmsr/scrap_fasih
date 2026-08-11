import re

def update_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # match the function exactly
    pattern = r'(\s*)function renderTabulasi\(\)\s*\{.*?(?=// ========== END ANOMALI FEATURE ==========)'
    
    # The new function
    new_func = r"""function renderTabulasi() {
        const container = document.getElementById('tabulasi-container');
        if (!container || anomaliDataCache.length === 0) return;

        const data = anomaliDataCache;

        // Build hierarchical pivot: kab -> kec -> desa -> sls
        const pivot = {};
        
        function getStats() {
            return { melebihi: 0, sama: 0, sangat: 0, dominan: 0, total: 0, biaya: 0, belum: 0, diproses: 0, selesai: 0 };
        }
        function addStats(p, row) {
            p.total++;
            p.biaya += row.biaya_produksi || 0;
            if ((row.jenis_anomali || '').includes('Melebihi')) p.melebihi++;
            else if ((row.jenis_anomali || '').includes('Sama')) p.sama++;
            else if ((row.jenis_anomali || '').includes('Sangat')) p.sangat++;
            else p.dominan++;
            
            if (row.status_anomali == 3) p.selesai++;
            else if (row.status_anomali == 2) p.diproses++;
            else p.belum++;
        }

        const totals = getStats();

        data.forEach(row => {
            const kab = row.kab_code || 'Lainnya';
            const kec = row.kec_code || 'Lainnya';
            const desa = row.desa_code || 'Lainnya';
            const sls = row.sls_code || 'Lainnya';

            if (!pivot[kab]) pivot[kab] = { stats: getStats(), children: {} };
            if (!pivot[kab].children[kec]) pivot[kab].children[kec] = { stats: getStats(), children: {} };
            if (!pivot[kab].children[kec].children[desa]) pivot[kab].children[kec].children[desa] = { stats: getStats(), children: {} };
            if (!pivot[kab].children[kec].children[desa].children[sls]) pivot[kab].children[kec].children[desa].children[sls] = { stats: getStats() };

            addStats(pivot[kab].stats, row);
            addStats(pivot[kab].children[kec].stats, row);
            addStats(pivot[kab].children[kec].children[desa].stats, row);
            addStats(pivot[kab].children[kec].children[desa].children[sls].stats, row);
            addStats(totals, row);
        });

        const thStyle = 'padding: 0.55rem 0.75rem; font-size: 0.75rem; font-weight: 700; text-align: center; white-space: nowrap; letter-spacing: 0.04em; text-transform: uppercase; background: var(--card-bg); color: var(--text-secondary); border-bottom: 2px solid var(--card-border);';
        const thLeftStyle = thStyle.replace('text-align: center', 'text-align: left');
        const tdStyle = (align = 'center') => `padding: 0.5rem 0.75rem; font-size: 0.82rem; text-align: ${align}; border-bottom: 1px solid var(--card-border); vertical-align: middle;`;
        const badge = (n, color, bg) => n > 0 ? `<span style="display:inline-block;padding:0.15rem 0.55rem;background:${bg};color:${color};border-radius:99px;font-weight:700;font-size:0.78rem;">${n}</span>` : `<span style="color:var(--text-secondary);font-size:0.78rem;">-</span>`;

        function renderRow(label, p, paddingLeft, type, parentKab, parentKec, parentDesa) {
            const pct = p.total > 0 ? Math.round((p.selesai / p.total) * 100) : 0;
            const pctColor = pct >= 80 ? '#22c55e' : pct >= 40 ? '#f59e0b' : '#ef4444';
            const barW = pct;
            
            let idAttr = '';
            let classAttr = '';
            let btn = '';
            let rowStyle = '';
            
            if (type === 'kab') {
                classAttr = 'row-kab';
                btn = `<button class="btn-expand" onclick="window.toggleTabulasiRow(this, 'kab', '${label}', '', '', '')" style="background:none;border:none;cursor:pointer;font-size:0.7rem;margin-right:0.3rem;">▶</button>`;
                rowStyle = 'background: rgba(99, 102, 241, 0.05); font-weight: 700;';
            } else if (type === 'kec') {
                classAttr = 'row-kec';
                idAttr = `data-parent-kab="${parentKab}"`;
                btn = `<button class="btn-expand" onclick="window.toggleTabulasiRow(this, 'kec', '${parentKab}', '${label}', '', '')" style="background:none;border:none;cursor:pointer;font-size:0.7rem;margin-right:0.3rem;">▶</button>`;
                rowStyle = 'display: none; background: rgba(99, 102, 241, 0.02); font-weight: 600;';
            } else if (type === 'desa') {
                classAttr = 'row-desa';
                idAttr = `data-parent-kec="${parentKab}-${parentKec}"`;
                btn = `<button class="btn-expand" onclick="window.toggleTabulasiRow(this, 'desa', '${parentKab}', '${parentKec}', '${label}', '')" style="background:none;border:none;cursor:pointer;font-size:0.7rem;margin-right:0.3rem;">▶</button>`;
                rowStyle = 'display: none; background: #fff; font-weight: 500;';
            } else {
                classAttr = 'row-sls';
                idAttr = `data-parent-desa="${parentKab}-${parentKec}-${parentDesa}"`;
                rowStyle = 'display: none; background: #fafafa; font-size: 0.78rem;';
            }

            return `<tr class="${classAttr}" ${idAttr} style="${rowStyle}" onmouseenter="this.style.background='var(--hover-bg)'" onmouseleave="this.style.background=''">
                <td style="${tdStyle('left')} padding-left: ${paddingLeft}rem;">
                    ${btn}${label}
                </td>
                <td style="${tdStyle()}">${badge(p.melebihi, '#ef4444', 'rgba(239,68,68,0.1)')}</td>
                <td style="${tdStyle()}">${badge(p.sama, '#ef4444', 'rgba(239,68,68,0.1)')}</td>
                <td style="${tdStyle()}">${badge(p.sangat, '#f97316', 'rgba(249,115,22,0.1)')}</td>
                <td style="${tdStyle()}">${badge(p.dominan, '#f59e0b', 'rgba(245,158,11,0.1)')}</td>
                <td style="${tdStyle()} font-weight: 700;">${p.total}</td>
                <td style="${tdStyle('right')} font-size: 0.78rem; color: var(--text-secondary);">${window.fmtRp ? window.fmtRp(p.biaya) : p.biaya}</td>
                <td style="${tdStyle()}">
                    ${badge(p.belum, '#ef4444', 'rgba(239,68,68,0.1)')}
                    ${p.diproses > 0 ? badge(p.diproses, '#f59e0b', 'rgba(245,158,11,0.1)') : ''}
                    ${p.selesai > 0 ? badge(p.selesai, '#22c55e', 'rgba(34,197,94,0.1)') : ''}
                </td>
                <td style="${tdStyle()} min-width: 100px;">
                    <div style="display:flex;align-items:center;gap:0.4rem;">
                        <div style="flex:1;height:6px;background:var(--card-border);border-radius:99px;overflow:hidden;">
                            <div style="height:100%;width:${barW}%;background:${pctColor};border-radius:99px;transition:width 0.5s;"></div>
                        </div>
                        <span style="font-size:0.75rem;font-weight:700;color:${pctColor};min-width:32px;">${pct}%</span>
                    </div>
                </td>
            </tr>`;
        }

        let rows = '';
        Object.keys(pivot).sort().forEach(kab => {
            rows += renderRow(kab, pivot[kab].stats, 0.75, 'kab', kab, '', '');
            Object.keys(pivot[kab].children).sort().forEach(kec => {
                rows += renderRow(kec, pivot[kab].children[kec].stats, 2, 'kec', kab, kec, '');
                Object.keys(pivot[kab].children[kec].children).sort().forEach(desa => {
                    rows += renderRow(desa, pivot[kab].children[kec].children[desa].stats, 3.5, 'desa', kab, kec, desa);
                    Object.keys(pivot[kab].children[kec].children[desa].children).sort().forEach(sls => {
                        rows += renderRow(sls, pivot[kab].children[kec].children[desa].children[sls].stats, 5, 'sls', kab, kec, desa);
                    });
                });
            });
        });

        // Totals row
        const totalPct = totals.total > 0 ? Math.round((totals.selesai / totals.total) * 100) : 0;
        const totalPctColor = totalPct >= 80 ? '#22c55e' : totalPct >= 40 ? '#f59e0b' : '#ef4444';
        const totalsRow = `<tr style="background: rgba(249,115,22,0.04); border-top: 2px solid var(--card-border);">
            <td style="${tdStyle('left')} font-weight: 800; color: var(--primary);">TOTAL SULAWESI TENGAH</td>
            <td style="${tdStyle()} font-weight: 700;">${totals.melebihi}</td>
            <td style="${tdStyle()} font-weight: 700;">${totals.sama}</td>
            <td style="${tdStyle()} font-weight: 700;">${totals.sangat}</td>
            <td style="${tdStyle()} font-weight: 700;">${totals.dominan}</td>
            <td style="${tdStyle()} font-weight: 800; font-size: 0.9rem;">${totals.total}</td>
            <td style="${tdStyle('right')} font-weight: 700; font-size: 0.78rem;">${window.fmtRp ? window.fmtRp(totals.biaya) : totals.biaya}</td>
            <td style="${tdStyle()}">
                ${badge(totals.belum, '#ef4444', 'rgba(239,68,68,0.1)')}
                ${totals.diproses > 0 ? badge(totals.diproses, '#f59e0b', 'rgba(245,158,11,0.1)') : ''}
                ${totals.selesai > 0 ? badge(totals.selesai, '#22c55e', 'rgba(34,197,94,0.1)') : ''}
            </td>
            <td style="${tdStyle()}">
                <div style="display:flex;align-items:center;gap:0.4rem;">
                    <div style="flex:1;height:6px;background:var(--card-border);border-radius:99px;overflow:hidden;">
                        <div style="height:100%;width:${totalPct}%;background:${totalPctColor};border-radius:99px;"></div>
                    </div>
                    <span style="font-size:0.75rem;font-weight:800;color:${totalPctColor};min-width:32px;">${totalPct}%</span>
                </div>
            </td>
        </tr>`;

        container.innerHTML = `
            <table style="width:100%;border-collapse:collapse;font-family:'Plus Jakarta Sans',sans-serif;min-width:700px;">
                <thead>
                    <tr>
                        <th style="${thLeftStyle} min-width:250px;">Wilayah</th>
                        <th style="${thStyle} color:#ef4444;">⛔ Melebihi</th>
                        <th style="${thStyle} color:#ef4444;">⚠️ Sama</th>
                        <th style="${thStyle} color:#f97316;">🔴 Sangat Dom.</th>
                        <th style="${thStyle} color:#f59e0b;">🟡 Dominan</th>
                        <th style="${thStyle}">Total</th>
                        <th style="${thStyle} text-align:right; min-width:120px;">Total Biaya Prod.</th>
                        <th style="${thStyle} min-width:150px;">Status TL</th>
                        <th style="${thStyle} min-width:110px;">% Selesai</th>
                    </tr>
                </thead>
                <tbody>${rows}</tbody>
                <tfoot>${totalsRow}</tfoot>
            </table>
            <div style="margin-top:0.6rem;font-size:0.73rem;color:var(--text-secondary);">
                * Klik icon ▶ untuk melihat rincian per kecamatan, desa, hingga SLS.
            </div>`;
    }

    window.toggleTabulasiRow = function(btn, type, id1, id2, id3, id4) {
        const table = btn.closest('table');
        const isExpanded = btn.textContent.includes('▼');
        btn.textContent = isExpanded ? '▶' : '▼';
        
        let targetClass = '';
        let targetAttr = '';
        let targetValue = '';
        if (type === 'kab') {
            targetClass = 'row-kec';
            targetAttr = 'data-parent-kab';
            targetValue = id1;
        } else if (type === 'kec') {
            targetClass = 'row-desa';
            targetAttr = 'data-parent-kec';
            targetValue = id1 + '-' + id2;
        } else if (type === 'desa') {
            targetClass = 'row-sls';
            targetAttr = 'data-parent-desa';
            targetValue = id1 + '-' + id2 + '-' + id3;
        }
        
        const children = table.querySelectorAll(`tr.${targetClass}[${targetAttr}="${targetValue}"]`);
        children.forEach(tr => {
            if (isExpanded) {
                tr.style.display = 'none';
                const childBtn = tr.querySelector('.btn-expand');
                if (childBtn && childBtn.textContent.includes('▼')) {
                    childBtn.click();
                }
            } else {
                tr.style.display = 'table-row';
            }
        });
    };
    
    """
    
    new_content = re.sub(pattern, r'\g<1>' + new_func, content, flags=re.DOTALL)
    
    if content != new_content:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {filename}")
    else:
        print(f"Failed to match in {filename}")

update_file('app.js')
update_file('app_v2.js')

