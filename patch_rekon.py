import re

with open('rekon.js', 'r') as f:
    content = f.read()

# 1. SLS render logic
sls_logic = """
        let m_utp_tot = 0, r_utp_tot = 0;
        let m_sbr_tot = 0, r_sbr_tot = 0;
        let m_kel_tot = 0, r_kel_tot = 0;

        filtered.forEach(d => {
            const m_utp = d.jml_utp_subsektor || 0;
            const m_sbr = d.Total_usaha_SBR || 0;
            const m_kel = d.keluarga || 0;
            
            const r_utp = d.total_utp || 0;
            const r_sbr = d.total_sbr || 0;
            const r_kel = 0; // Not available in data
            
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
            <div class="summary-card"><div class="label">Total UTP (Rls/Muatan)</div><div class="value">${r_utp_tot.toLocaleString('id-ID')} / ${m_utp_tot.toLocaleString('id-ID')}</div></div>
            <div class="summary-card"><div class="label">Total SBR (Rls/Muatan)</div><div class="value">${r_sbr_tot.toLocaleString('id-ID')} / ${m_sbr_tot.toLocaleString('id-ID')}</div></div>
            <div class="summary-card"><div class="label">Total Keluarga (Rls/Muatan)</div><div class="value">${r_kel_tot.toLocaleString('id-ID')} / ${m_kel_tot.toLocaleString('id-ID')}</div></div>
        `;"""
content = re.sub(r'        let totTarget = 0, totRealisasi = 0;\s*filtered.forEach\(d => \{.*?</script>', sls_logic + '\n\n    } else {', content, flags=re.DOTALL)
# Wait, the regex ending might be bad. Let's do it safely.
