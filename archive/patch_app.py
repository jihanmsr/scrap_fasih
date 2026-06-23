with open('app.js', 'r', encoding='utf-8') as f:
    js = f.read()

target = '''    window.renderGranularAssignmentsTable = function(resetPage = true) {'''

replacement = '''    window.petugasSortField = window.petugasSortField || 'total';
    window.petugasSortOrder = window.petugasSortOrder || -1;

    window.sortPetugasSummary = function(field) {
        if (window.petugasSortField === field) {
            window.petugasSortOrder *= -1; // toggle
        } else {
            window.petugasSortField = field;
            window.petugasSortOrder = field === 'name' ? 1 : -1;
        }
        if (window.lastBaseFiltered && window.renderPetugasSummaryTable) {
            window.renderPetugasSummaryTable(window.lastBaseFiltered);
        }
    };

    window.renderPetugasSummaryTable = function(data) {
        let totalAll = 0;
        let selesaiAll = 0;
        let belumAll = 0;
        let petugasMap = {};

        data.forEach(r => {
            const petName = (r.petugas_username !== '-' && r.petugas_username) ? r.petugas_username : ((r.petugas_fullname !== '-' && r.petugas_fullname) ? r.petugas_fullname : 'Belum Ada Petugas');
            
            if (!petugasMap[petName]) {
                petugasMap[petName] = { name: petName, total: 0, selesai: 0, belum: 0 };
            }
            
            petugasMap[petName].total += 1;
            totalAll += 1;
            
            if (r.status === 'OPEN' || r.status === 'DRAFT') {
                petugasMap[petName].belum += 1;
                belumAll += 1;
            } else {
                petugasMap[petName].selesai += 1;
                selesaiAll += 1;
            }
        });

        const pctSelesaiAll = totalAll > 0 ? ((selesaiAll / totalAll) * 100).toFixed(1) : 0;
        const pctBelumAll = totalAll > 0 ? ((belumAll / totalAll) * 100).toFixed(1) : 0;

        document.getElementById('petugas-stat-total').textContent = totalAll.toLocaleString('id-ID');
        document.getElementById('petugas-stat-selesai').innerHTML = `${selesaiAll.toLocaleString('id-ID')} <span style="font-size: 0.9rem; opacity: 0.8; font-weight: 500;">(${pctSelesaiAll}%)</span>`;
        document.getElementById('petugas-stat-belum').innerHTML = `${belumAll.toLocaleString('id-ID')} <span style="font-size: 0.9rem; opacity: 0.8; font-weight: 500;">(${pctBelumAll}%)</span>`;

        let arr = Object.values(petugasMap);
        
        // Search filter
        const searchInput = document.getElementById('petugas-summary-search-input');
        if (searchInput && searchInput.value.trim()) {
            const term = searchInput.value.toLowerCase().trim();
            arr = arr.filter(p => p.name.toLowerCase().includes(term));
        }

        // Apply Sort
        arr.sort((a, b) => {
            let valA, valB;
            switch(window.petugasSortField) {
                case 'name': valA = a.name; valB = b.name; break;
                case 'belum': valA = a.belum; valB = b.belum; break;
                case 'selesai': valA = a.selesai; valB = b.selesai; break;
                case 'pct': valA = (a.total>0?a.selesai/a.total:0); valB = (b.total>0?b.selesai/b.total:0); break;
                case 'total':
                default:
                    valA = a.total; valB = b.total; break;
            }
            if (typeof valA === 'string') {
                return valA.localeCompare(valB) * window.petugasSortOrder;
            }
            return (valA - valB) * window.petugasSortOrder;
        });

        const tbody = document.getElementById('petugas-summary-table-body');
        if (!tbody) return;

        if (arr.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 2rem; color: var(--text-secondary);">Silakan muat data atau pilih wilayah terlebih dahulu...</td></tr>';
            return;
        }

        let html = '';
        arr.forEach((p, i) => {
            const pct = p.total > 0 ? ((p.selesai / p.total) * 100).toFixed(1) : 0;
            const isComplete = pct === "100.0";
            
            let badgeHtml = '';
            if (isComplete) {
                badgeHtml = `<div style="background: rgba(34, 197, 94, 0.1); color: var(--color-delivered); border: 1px solid rgba(34, 197, 94, 0.2); padding: 0.25rem 0.5rem; border-radius: 0.5rem; display: inline-flex; align-items: center; gap: 0.25rem; font-size: 0.75rem; font-weight: 700;">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
                    Tuntas
                </div>`;
            } else {
                badgeHtml = `<div style="display: flex; align-items: center; gap: 0.5rem; width: 100%;">
                    <div style="flex-grow: 1; height: 6px; background: rgba(0,0,0,0.05); border-radius: 3px; overflow: hidden;">
                        <div style="height: 100%; width: ${pct}%; background: var(--primary); border-radius: 3px;"></div>
                    </div>
                    <span style="font-weight: 700; color: var(--text-primary); min-width: 35px; text-align: right;">${pct}%</span>
                </div>`;
            }

            html += `
                <tr style="border-bottom: 1px solid var(--border-light); transition: all 0.2s;">
                    <td style="text-align: center; font-weight: 600; color: var(--text-secondary);">${i + 1}</td>
                    <td style="font-weight: 600; color: var(--text-primary);">
                        <div style="display: flex; align-items: center; gap: 0.5rem;">
                            <div style="width: 24px; height: 24px; border-radius: 50%; background: rgba(249, 115, 22, 0.1); color: var(--primary); display: flex; align-items: center; justify-content: center; font-size: 0.65rem; font-weight: 700;">
                                ${p.name.substring(0, 2).toUpperCase()}
                            </div>
                            ${p.name}
                        </div>
                    </td>
                    <td style="text-align: center; font-weight: 700; color: var(--text-primary); font-family: 'Outfit', sans-serif;">${p.total.toLocaleString('id-ID')}</td>
                    <td style="text-align: center; font-weight: 600; color: var(--color-bounced);">${p.belum.toLocaleString('id-ID')}</td>
                    <td style="text-align: center; font-weight: 600; color: var(--color-delivered);">${p.selesai.toLocaleString('id-ID')}</td>
                    <td style="text-align: center;">${badgeHtml}</td>
                </tr>
            `;
        });
        tbody.innerHTML = html;
        
        // Update sort icons
        const headers = document.querySelectorAll('#petugas-summary-table-body').length > 0 ? document.getElementById('petugas-summary-table-body').parentElement.querySelectorAll('th') : [];
        headers.forEach(th => {
            const iconSpan = th.querySelector('.sort-icon');
            if (iconSpan) {
                iconSpan.innerHTML = ''; // Clear all
                if (th.getAttribute('onclick') && th.getAttribute('onclick').includes(window.petugasSortField)) {
                    iconSpan.innerHTML = window.petugasSortOrder === 1 ? ' ↑' : ' ↓';
                }
            }
        });
    };

    window.renderGranularAssignmentsTable = function(resetPage = true) {'''

if target in js:
    js = js.replace(target, replacement)
    with open('app.js', 'w', encoding='utf-8') as f:
        f.write(js)
    print('app.js successfully patched with renderPetugasSummaryTable')
else:
    print('Target not found in app.js')
