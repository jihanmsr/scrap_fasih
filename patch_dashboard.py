import re

with open('app.js', 'r') as f:
    content = f.read()

# Modify renderDashboardStats
new_render_dashboard = """
async function renderDashboardStats() {
    const surveyType = activeSubtab === 'se2026' ? 'se_umum' : 'se_ub';
    const selKab = document.getElementById('filter-kabupaten');
    const kabVal = selKab ? selKab.value : 'all';
    
    // FETCH DASHBOARD SUMMARY DARI MYSQL!
    const cleanKabVal = kabVal.replace(/^\[\\d+\]\\s*/, '').trim().toUpperCase();
    
    document.getElementById('stat-total-target').innerHTML = '<span style="font-size: 0.9rem; color: var(--text-secondary);">Memuat...</span>';
    document.getElementById('stat-total-selesai').innerHTML = '<span style="font-size: 0.9rem; color: var(--text-secondary);">Memuat...</span>';
    
    try {
        const url = `https://dds-api.bpssulteng.id/api.php?action=get_dashboard_summary&survey=${surveyType}&kab=${kabVal === 'all' ? '' : cleanKabVal}`;
        const res = await fetch(url);
        const data = await res.json();
        
        let totalTarget = 0;
        let totalSelesai = 0;
        let totalBelum = 0;
        
        const chartLabels = [];
        const chartSelesai = [];
        const chartTarget = [];
        
        let rincianHTML = '';
        
        data.forEach((row, idx) => {
            const tgt = parseInt(row.total_target) || 0;
            const sel = parseInt(row.selesai) || 0;
            const blm = parseInt(row.belum_selesai) || 0;
            
            totalTarget += tgt;
            totalSelesai += sel;
            totalBelum += blm;
            
            const pct = tgt > 0 ? ((sel / tgt) * 100).toFixed(1) : 0;
            const name = row.name || '-';
            
            chartLabels.push(name.length > 15 ? name.substring(0, 15) + '...' : name);
            chartSelesai.push(sel);
            chartTarget.push(tgt);
            
            rincianHTML += `
            <tr style="border-bottom: 1px solid var(--card-border); transition: background 0.2s ease;">
                <td style="padding: 0.8rem 1rem; color: var(--text-secondary); text-align: center;">${idx + 1}</td>
                <td style="padding: 0.8rem 1rem; font-weight: 700; color: var(--text-primary); cursor: pointer;" onclick="if('${kabVal}' === 'all') { const sel = document.getElementById('filter-kabupaten'); if(sel) { for(let i=0; i<sel.options.length; i++) { if(sel.options[i].text.includes('${name}')) { sel.selectedIndex = i; sel.dispatchEvent(new Event('change')); break; } } } }">${name}</td>
                <td style="padding: 0.8rem 1rem; text-align: right; font-weight: 700;">${tgt.toLocaleString('id-ID')}</td>
                <td style="padding: 0.8rem 1rem; text-align: right; font-weight: 700; color: #ef4444;">${blm.toLocaleString('id-ID')}</td>
                <td style="padding: 0.8rem 1rem; text-align: right; font-weight: 700; color: #22c55e;">${sel.toLocaleString('id-ID')}</td>
                <td style="padding: 0.8rem 1rem;">
                    <div style="display: flex; align-items: center; gap: 0.5rem; justify-content: flex-end;">
                        <div style="width: 60px; height: 6px; background: var(--card-border); border-radius: 99px; overflow: hidden; flex-shrink: 0;">
                            <div style="height: 100%; width: ${pct}%; background: ${pct >= 100 ? '#22c55e' : 'var(--primary)'}; border-radius: 99px;"></div>
                        </div>
                        <span style="font-size: 0.8rem; font-weight: 700; color: ${pct >= 100 ? '#22c55e' : 'var(--text-primary)'}; min-width: 40px; text-align: right;">${pct}%</span>
                    </div>
                </td>
            </tr>`;
        });
        
        // Update KPI Cards
        document.getElementById('stat-total-target').innerHTML = `${totalTarget.toLocaleString('id-ID')}`;
        
        const pctTotalSelesai = totalTarget > 0 ? ((totalSelesai / totalTarget) * 100).toFixed(2) : '0.00';
        document.getElementById('stat-total-selesai').innerHTML = `${totalSelesai.toLocaleString('id-ID')} <span style="font-size: 1rem; opacity: 0.8; font-weight: 500;">(${pctTotalSelesai}%)</span>`;
        
        // Update Chart
        if (window.capaianChart) {
            window.capaianChart.data.labels = chartLabels;
            window.capaianChart.data.datasets[0].data = chartSelesai;
            window.capaianChart.data.datasets[1].data = chartTarget;
            window.capaianChart.update();
        }
        
        // Update Table
        const tbody = document.getElementById('rincian-kab-tbody');
        if (tbody) {
            if (data.length === 0) {
                tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; padding: 2rem; color: var(--text-secondary);">Tidak ada data.</td></tr>`;
            } else {
                tbody.innerHTML = rincianHTML;
            }
        }
        
        // Update Title of Table
        const tblTitle = document.getElementById('rincian-kab-title');
        if (tblTitle) {
            tblTitle.innerText = kabVal === 'all' ? 'Rincian per Kabupaten/Kota' : 'Rincian per Kecamatan';
        }
        
    } catch (e) {
        console.error("Gagal load dashboard mysql:", e);
    }
}
"""

content = re.sub(
    r'function renderDashboardStats\(\) \{.*?\n\s*// --- UPDATE SE UMUM & SE UB COUNTS ---',
    lambda m: new_render_dashboard + '\n    // --- UPDATE SE UMUM & SE UB COUNTS ---',
    content,
    flags=re.DOTALL
)

with open('app.js', 'w') as f:
    f.write(content)
