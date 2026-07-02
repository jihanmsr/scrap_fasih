import re

with open('app.js', 'r') as f:
    content = f.read()

new_renderSeDashboard = """
    window.renderSeDashboard = async function (surveyType) {
        const ipasDataObj = window.IPAS_DATA || { se_umum: [], se_ub: [] };
        
        // --- MySQL FETCH DASHBOARD KPI ---
        try {
            const url = `https://dds-api.bpssulteng.id/api.php?action=get_dashboard_summary&survey=${surveyType}&kab=all`;
            const res = await fetch(url);
            const data = await res.json();
            
            let totalPrelist = 0;
            let totalSelesai = 0;
            
            data.forEach(row => {
                totalPrelist += parseInt(row.total_target) || 0;
                totalSelesai += parseInt(row.selesai) || 0;
            });
            
            const pct = totalPrelist > 0 ? ((totalSelesai / totalPrelist) * 100).toFixed(2) : '0.00';
            
            const prelistEl = document.getElementById(`${surveyType}-stat-total-prelist`);
            const prelistWrapEl = document.getElementById(`${surveyType}-stat-total-prelist-wrapper`);
            if (prelistWrapEl) {
                // If it has popover wrapper, just update the value
                const spanEl = prelistWrapEl.querySelector('span:first-child');
                if (spanEl) spanEl.textContent = totalPrelist.toLocaleString('id-ID');
                else prelistWrapEl.innerHTML = `<span style="font-weight: 800;">${totalPrelist.toLocaleString('id-ID')}</span>`;
            } else if (prelistEl) {
                prelistEl.textContent = totalPrelist.toLocaleString('id-ID');
            }
            
            const submittedEl = document.getElementById(`${surveyType}-stat-submitted`);
            if (submittedEl) {
                submittedEl.textContent = totalSelesai.toLocaleString('id-ID');
            }
            
            const pctEl = document.getElementById(`${surveyType}-stat-percentage`);
            if (pctEl) {
                pctEl.textContent = `(${pct}%)`;
                pctEl.style.color = pct >= 50 ? 'var(--color-delivered)' : (pct > 0 ? '#f59e0b' : 'var(--text-secondary)');
            }
        } catch (e) {
            console.error("Failed to load KPI from MySQL", e);
        }

        // --- CONTINUE OLD BEHAVIOR FOR DAILY STATS ---
        const surveyData = ipasDataObj[surveyType] || [];
"""

content = re.sub(
    r'window\.renderSeDashboard = function \(surveyType\) \{.*?const surveyData = ipasDataObj\[surveyType\] \|\| \[\];',
    lambda m: new_renderSeDashboard.strip(),
    content,
    flags=re.DOTALL
)

# Also disable the lines where it overwrites the KPI elements
content = re.sub(
    r'const prelistWrapperEl = document\.getElementById.*?const newTodayEl',
    lambda m: '/* ' + m.group(0).replace('/*', '').replace('*/', '') + ' */\n        const newTodayEl',
    content,
    flags=re.DOTALL
)

with open('app.js', 'w') as f:
    f.write(content)
