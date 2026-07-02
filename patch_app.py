import re

with open('app.js', 'r') as f:
    content = f.read()

# 1. Replace loadGranularAssignmentsData
new_load = """
    async function loadGranularAssignmentsData(kabVal = null, surveyTypeFilter = null) {
        if (!kabVal) {
            kabVal = document.getElementById('assign-sls-kab-filter')?.value || 'all';
        }
        if (!surveyTypeFilter) {
            const surveyFilterEl = document.getElementById('assign-sls-survey-filter');
            surveyTypeFilter = surveyFilterEl ? surveyFilterEl.value : (localStorage.getItem('active_assign_subtab') === 'se2026' ? 'se_umum' : 'se_ub');
        }

        const tbody = document.getElementById('assign-sls-table-body');
        if (surveyTypeFilter === 'se_umum' && kabVal === 'all') {
            if (tbody) {
                tbody.innerHTML = `<tr><td colspan="12" style="text-align: center; padding: 3rem; color: var(--text-secondary);">Silakan pilih Kabupaten/Kota terlebih dahulu untuk memuat rincian data assignment.</td></tr>`;
            }
            if (window.renderPetugasSummaryTable) window.renderPetugasSummaryTable([]);
            
            // Populating KPI cards with overall province data
            try {
                const ipasDataObj = window.IPAS_DATA || { se_umum: [], se_ub: [] };
                const surveyData = ipasDataObj[surveyTypeFilter] || [];
                let prelist = 0, draft = 0, openVal = 0, submitted = 0, rejected = 0;
                surveyData.forEach(item => {
                    prelist += item.total_prelist || 0;
                    draft += item.total_draft || 0;
                    openVal += item.total_open || 0;
                    submitted += item.total_submitted || 0;
                    rejected += item.total_rejected || 0;
                });
                const selesaiAll = submitted;
                const belumAll = draft + openVal + rejected;
                const totalAll = prelist;
                const pctSelesaiAll = totalAll > 0 ? ((selesaiAll / totalAll) * 100).toFixed(1) : 0;
                const pctBelumAll = totalAll > 0 ? ((belumAll / totalAll) * 100).toFixed(1) : 0;

                const totalEl = document.getElementById('petugas-stat-total');
                const selesaiEl = document.getElementById('petugas-stat-selesai');
                const belumEl = document.getElementById('petugas-stat-belum');
                if (totalEl) totalEl.textContent = totalAll.toLocaleString('id-ID');
                if (selesaiEl) selesaiEl.innerHTML = `${selesaiAll.toLocaleString('id-ID')} <span style="font-size: 0.9rem; opacity: 0.8; font-weight: 500;">(${pctSelesaiAll}%)</span>`;
                if (belumEl) belumEl.innerHTML = `${belumAll.toLocaleString('id-ID')} <span style="font-size: 0.9rem; opacity: 0.8; font-weight: 500;">(${pctBelumAll}%)</span>`;
            } catch (e) {}
            return;
        }

        // Fetch Petugas Summary from MySQL
        const cleanKabVal = kabVal.replace(/^\[\\d+\]\\s*/, '').trim().toUpperCase();
        try {
            const url = `https://dds-api.bpssulteng.id/api.php?action=get_petugas_summary&survey=${surveyTypeFilter}&kab=${kabVal === 'all' ? '' : cleanKabVal}`;
            const res = await fetch(url);
            const data = await res.json();
            window.PETUGAS_SUMMARY_MYSQL = data; 
            if (window.renderPetugasSummaryTable) {
                window.renderPetugasSummaryTable(null, true);
            }
        } catch (e) {
            console.error("Failed to fetch petugas summary:", e);
        }

        window.updateGranularStatusFilterOptions();
        window.renderGranularAssignmentsTable(true);
    }
"""

content = re.sub(
    r'async function loadGranularAssignmentsData.*?// --- REKAP BELUM DITUGASKAN PER KECAMATAN ---',
    lambda m: new_load + '\n    // --- REKAP BELUM DITUGASKAN PER KECAMATAN ---',
    content,
    flags=re.DOTALL
)

# 2. Replace updateGranularStatusFilterOptions
new_status_opt = """
    window.updateGranularStatusFilterOptions = function () {
        const statusSelect = document.getElementById('assign-sls-status-filter');
        if (!statusSelect) return;
        const currentSelectedStatus = statusSelect.value || 'all';
        
        let optionsHTML = `<option value="all">Semua Status</option>`;
        ['OPEN', 'DRAFT', 'SUBMITTED', 'REJECTED', 'APPROVED'].forEach(s => {
            optionsHTML += `<option value="${s}">${s}</option>`;
        });
        statusSelect.innerHTML = optionsHTML;
        statusSelect.value = currentSelectedStatus;
    };
"""

content = re.sub(
    r'window\.updateGranularStatusFilterOptions = function \(\) \{.*?};(?=\n\n\s*async function loadGranular)',
    lambda m: new_status_opt.strip(),
    content,
    flags=re.DOTALL
)

# 3. Replace renderGranularAssignmentsTable
new_render_table = """
    window.renderGranularAssignmentsTable = async function (resetPage = true) {
        const tbody = document.getElementById('assign-sls-table-body');
        if (!tbody) return;

        if (resetPage) window.granularCurrentPage = 1;

        const kabVal = document.getElementById('assign-sls-kab-filter')?.value || 'all';
        const cleanKabVal = kabVal.replace(/^\[\\d+\]\\s*/, '').trim().toUpperCase();
        const kecVal = document.getElementById('assign-sls-kec-filter')?.value || 'all';
        const desaVal = document.getElementById('assign-sls-desa-filter')?.value || 'all';
        const slsVal = document.getElementById('assign-sls-sls-filter')?.value || 'all';
        const statusVal = document.getElementById('assign-sls-status-filter')?.value || 'all';
        const searchVal = document.getElementById('assign-sls-search-input')?.value.trim() || '';

        const surveyFilterEl = document.getElementById('assign-sls-survey-filter');
        const surveyTypeFilter = surveyFilterEl ? surveyFilterEl.value : (localStorage.getItem('active_assign_subtab') === 'se2026' ? 'se_umum' : 'se_ub');

        if (surveyTypeFilter === 'se_umum' && kabVal === 'all') return;

        tbody.innerHTML = `<tr><td colspan="12" style="text-align: center; padding: 3rem; color: var(--text-secondary);">Memuat data dari MySQL Server...</td></tr>`;

        try {
            const params = new URLSearchParams({
                action: 'get_granular',
                survey: surveyTypeFilter,
                kab: cleanKabVal === 'ALL' ? '' : cleanKabVal,
                kec: kecVal === 'all' ? '' : kecVal,
                desa: desaVal === 'all' ? '' : desaVal,
                sls: slsVal === 'all' ? '' : slsVal,
                status: statusVal === 'all' ? '' : statusVal,
                search: searchVal,
                page: window.granularCurrentPage,
                limit: window.granularPageLimit
            });
            const url = `https://dds-api.bpssulteng.id/api.php?${params.toString()}`;
            const res = await fetch(url);
            const resp = await res.json();
            
            const paginated = resp.data || [];
            const totalItems = parseInt(resp.total) || 0;
            const totalPages = Math.ceil(totalItems / window.granularPageLimit);
            const startIndex = (window.granularCurrentPage - 1) * window.granularPageLimit;

            if (paginated.length === 0) {
                tbody.innerHTML = `<tr><td colspan="12" style="text-align: center; padding: 3rem; color: var(--text-secondary);">Tidak ada data assignment yang cocok dengan kriteria filter.</td></tr>`;
                const pagInfo = document.getElementById('assign-sls-pagination-info');
                if (pagInfo) pagInfo.innerText = 'Menampilkan 0 - 0 dari 0 Target';
                const pagBtns = document.getElementById('assign-sls-pagination-buttons');
                if (pagBtns) pagBtns.innerHTML = '';
                return;
            }

            let html = '';
            paginated.forEach((r, idx) => {
                const no = startIndex + idx + 1;
                const statusColor = getStatusColor(r.status);
                const petugasName = r.petugas_fullname || r.petugas_username || '-';
                
                html += `
                    <tr style="border-bottom: 1px solid var(--card-border); transition: background 0.2s ease;">
                        <td style="padding: 0.8rem 1rem; color: var(--text-secondary); text-align: center;">${no}</td>
                        <td style="padding: 0.8rem 1rem;">${r.kab_name || '-'}</td>
                        <td style="padding: 0.8rem 1rem;">${r.kec_name || '-'}</td>
                        <td style="padding: 0.8rem 1rem;">${r.desa_name || '-'}</td>
                        <td style="padding: 0.8rem 1rem; font-family: monospace;">${r.sls_code || '-'}</td>
                        <td style="padding: 0.8rem 1rem;">
                            <div style="display:flex; align-items:center; gap:0.5rem;">
                                <div style="width: 28px; height: 28px; border-radius: 99px; background: var(--primary); color: white; display: flex; align-items: center; justify-content: center; font-size: 0.75rem; font-weight: bold; flex-shrink:0;">
                                    ${petugasName !== '-' ? petugasName.substring(0, 2).toUpperCase() : '?'}
                                </div>
                                <span style="font-weight: 600;">${petugasName}</span>
                            </div>
                        </td>
                        <td style="padding: 0.8rem 1rem; color: var(--text-secondary);">${r.petugas_username || '-'}</td>
                        <td style="padding: 0.8rem 1rem; font-family: monospace; font-size: 0.8rem;">${r.target_id || '-'}</td>
                        <td style="padding: 0.8rem 1rem; font-weight: 600;">${r.target_name || '-'}</td>
                        <td style="padding: 0.8rem 1rem; text-align: center;">
                            <span style="background: ${statusColor}15; color: ${statusColor}; padding: 0.25rem 0.75rem; border-radius: 99px; font-size: 0.75rem; font-weight: 700;">
                                ${r.status || 'UNKNOWN'}
                            </span>
                        </td>
                        <td style="padding: 0.8rem 1rem; text-align: center;">${r.updated_at || '-'}</td>
                    </tr>
                `;
            });
            tbody.innerHTML = html;

            const pagInfo = document.getElementById('assign-sls-pagination-info');
            if (pagInfo) {
                const endIdx = Math.min(startIndex + window.granularPageLimit, totalItems);
                pagInfo.innerText = `Menampilkan ${startIndex + 1} - ${endIdx} dari ${totalItems.toLocaleString('id-ID')} Target`;
            }

            const pagBtns = document.getElementById('assign-sls-pagination-buttons');
            if (pagBtns) {
                let btns = '';
                if (window.granularCurrentPage > 1) {
                    btns += `<button onclick="window.granularCurrentPage--; window.renderGranularAssignmentsTable(false)" style="padding: 0.4rem 0.8rem; background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 0.3rem; cursor: pointer; color: var(--text-primary); font-weight:600;">&laquo; Prev</button>`;
                }
                btns += `<span style="padding: 0.4rem 0.8rem; font-weight: 600;">Halaman ${window.granularCurrentPage} dari ${totalPages.toLocaleString('id-ID')}</span>`;
                if (window.granularCurrentPage < totalPages) {
                    btns += `<button onclick="window.granularCurrentPage++; window.renderGranularAssignmentsTable(false)" style="padding: 0.4rem 0.8rem; background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 0.3rem; cursor: pointer; color: var(--primary); font-weight:600;">Next &raquo;</button>`;
                }
                pagBtns.innerHTML = btns;
            }
        } catch (e) {
            console.error("Failed to load granular table:", e);
            tbody.innerHTML = `<tr><td colspan="12" style="text-align: center; padding: 3rem; color: #ef4444;">Gagal memuat data dari server. Periksa koneksi atau console.</td></tr>`;
        }
    };
"""

content = re.sub(
    r'window\.renderGranularAssignmentsTable = function \(resetPage = true\) \{.*?};(?=\n\n\s*// --- REKAPITULASI CAPAIAN PER PETUGAS ---)',
    lambda m: new_render_table.strip(),
    content,
    flags=re.DOTALL
)

# 4. Modify Dropdowns handleGranularFilterChange
new_handle_filter = """
    window.handleGranularFilterChange = async function (changedLevel) {
        // Reset sub filters
        const kabSelect = document.getElementById('assign-sls-kab-filter');
        const kecSelect = document.getElementById('assign-sls-kec-filter');
        const desaSelect = document.getElementById('assign-sls-desa-filter');
        const slsSelect = document.getElementById('assign-sls-sls-filter');
        const searchInput = document.getElementById('assign-sls-search-input');
        const surveyFilterEl = document.getElementById('assign-sls-survey-filter');
        
        const surveyTypeFilter = surveyFilterEl ? surveyFilterEl.value : (localStorage.getItem('active_assign_subtab') === 'se2026' ? 'se_umum' : 'se_ub');

        if (changedLevel === 'search') {
            window.renderGranularAssignmentsTable(true);
            return;
        }

        const kabVal = kabSelect ? kabSelect.value : 'all';
        const cleanKabVal = kabVal.replace(/^\[\\d+\]\\s*/, '').trim().toUpperCase();

        if (changedLevel === 'kab') {
            if (kabVal === 'all') {
                if (kecSelect) { kecSelect.innerHTML = '<option value="all">Semua Kecamatan</option>'; kecSelect.disabled = true; }
                if (desaSelect) { desaSelect.innerHTML = '<option value="all">Semua Desa</option>'; desaSelect.disabled = true; }
                if (slsSelect) { slsSelect.innerHTML = '<option value="all">Semua SLS</option>'; slsSelect.disabled = true; }
                if (searchInput) { searchInput.value = ''; searchInput.disabled = true; }
                window.loadGranularAssignmentsData(kabVal, surveyTypeFilter);
                return;
            }

            if (kecSelect) {
                kecSelect.innerHTML = '<option value="all">Memuat...</option>';
                const res = await fetch(`https://dds-api.bpssulteng.id/api.php?action=get_granular_options&type=kec&survey=${surveyTypeFilter}&kab=${cleanKabVal}`);
                const data = await res.json();
                let opts = '<option value="all">Semua Kecamatan</option>';
                data.forEach(k => opts += `<option value="${k}">${k}</option>`);
                kecSelect.innerHTML = opts;
                kecSelect.disabled = false;
            }
            if (desaSelect) { desaSelect.innerHTML = '<option value="all">Semua Desa</option>'; desaSelect.disabled = true; }
            if (slsSelect) { slsSelect.innerHTML = '<option value="all">Semua SLS</option>'; slsSelect.disabled = true; }
            if (searchInput) searchInput.disabled = false;
            window.loadGranularAssignmentsData(kabVal, surveyTypeFilter);
            return;
        }

        const kecVal = kecSelect ? kecSelect.value : 'all';
        if (changedLevel === 'kec') {
            if (kecVal === 'all') {
                if (desaSelect) { desaSelect.innerHTML = '<option value="all">Semua Desa</option>'; desaSelect.disabled = true; }
                if (slsSelect) { slsSelect.innerHTML = '<option value="all">Semua SLS</option>'; slsSelect.disabled = true; }
                window.renderGranularAssignmentsTable(true);
                return;
            }

            if (desaSelect) {
                desaSelect.innerHTML = '<option value="all">Memuat...</option>';
                const res = await fetch(`https://dds-api.bpssulteng.id/api.php?action=get_granular_options&type=desa&survey=${surveyTypeFilter}&kab=${cleanKabVal}&kec=${kecVal}`);
                const data = await res.json();
                let opts = '<option value="all">Semua Desa</option>';
                data.forEach(d => opts += `<option value="${d}">${d}</option>`);
                desaSelect.innerHTML = opts;
                desaSelect.disabled = false;
            }
            if (slsSelect) { slsSelect.innerHTML = '<option value="all">Semua SLS</option>'; slsSelect.disabled = true; }
            window.renderGranularAssignmentsTable(true);
            return;
        }

        const desaVal = desaSelect ? desaSelect.value : 'all';
        if (changedLevel === 'desa') {
            if (desaVal === 'all') {
                if (slsSelect) { slsSelect.innerHTML = '<option value="all">Semua SLS</option>'; slsSelect.disabled = true; }
                window.renderGranularAssignmentsTable(true);
                return;
            }

            if (slsSelect) {
                slsSelect.innerHTML = '<option value="all">Memuat...</option>';
                const res = await fetch(`https://dds-api.bpssulteng.id/api.php?action=get_granular_options&type=sls&survey=${surveyTypeFilter}&kab=${cleanKabVal}&kec=${kecVal}&desa=${desaVal}`);
                const data = await res.json();
                let opts = '<option value="all">Semua SLS</option>';
                data.forEach(s => opts += `<option value="${s.sls_code}">${s.sls_code} - ${s.sls_name || ''}</option>`);
                slsSelect.innerHTML = opts;
                slsSelect.disabled = false;
            }
            window.renderGranularAssignmentsTable(true);
            return;
        }

        if (changedLevel === 'sls' || changedLevel === 'status') {
            window.renderGranularAssignmentsTable(true);
        }
    };
"""

content = re.sub(
    r'window\.handleGranularFilterChange = function \(changedLevel\) \{.*?};(?=\n\n\s*// --- TAB NAVIGATION)',
    lambda m: new_handle_filter.strip(),
    content,
    flags=re.DOTALL
)

# 5. Modify renderPetugasSummaryTable
new_petugas_summary = """
    window.renderPetugasSummaryTable = function (baseFiltered, isMySQL = false) {
        const tbody = document.getElementById('assign-sls-petugas-summary-tbody');
        if (!tbody) return;

        if (isMySQL) {
            const data = window.PETUGAS_SUMMARY_MYSQL || [];
            if (data.length === 0) {
                tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; padding: 2rem; color: var(--text-secondary);">Silakan muat data atau pilih wilayah terlebih dahulu...</td></tr>`;
                return;
            }

            let html = '';
            let totalAll = 0, selesaiAll = 0, belumAll = 0;

            const searchVal = document.getElementById('assign-sls-petugas-search')?.value.toLowerCase().trim() || '';

            let filteredData = data;
            if (searchVal) {
                filteredData = data.filter(r => (r.petugas_fullname || '').toLowerCase().includes(searchVal));
            }

            filteredData.forEach((row, idx) => {
                const total = parseInt(row.total_target) || 0;
                const selesai = parseInt(row.selesai) || 0;
                const belum = parseInt(row.belum_selesai) || 0;
                const pct = total > 0 ? ((selesai / total) * 100).toFixed(1) : 0;
                
                totalAll += total; selesaiAll += selesai; belumAll += belum;

                const nameDisplay = row.petugas_fullname || '-';

                html += `
                <tr style="border-bottom: 1px solid var(--card-border); transition: background 0.2s ease;">
                    <td style="padding: 0.8rem; text-align: center; color: var(--text-secondary); font-size: 0.85rem;">${idx + 1}</td>
                    <td style="padding: 0.8rem; font-weight: 600; color: var(--text-primary);">
                        <div style="display:flex; align-items:center; gap:0.5rem;">
                            <div style="width: 28px; height: 28px; border-radius: 99px; background: var(--primary); color: white; display: flex; align-items: center; justify-content: center; font-size: 0.75rem; font-weight: bold; flex-shrink:0;">
                                ${nameDisplay !== '-' ? nameDisplay.substring(0, 2).toUpperCase() : '?'}
                            </div>
                            <span style="font-size: 0.9rem;">${nameDisplay}</span>
                        </div>
                    </td>
                    <td style="padding: 0.8rem; text-align: right; font-weight: 700;">${total.toLocaleString('id-ID')}</td>
                    <td style="padding: 0.8rem; text-align: right; font-weight: 700; color: #ef4444;">${belum.toLocaleString('id-ID')}</td>
                    <td style="padding: 0.8rem; text-align: right; font-weight: 700; color: #22c55e;">${selesai.toLocaleString('id-ID')}</td>
                    <td style="padding: 0.8rem;">
                        <div style="display: flex; align-items: center; gap: 0.5rem; justify-content: flex-end;">
                            <div style="width: 60px; height: 6px; background: var(--card-border); border-radius: 99px; overflow: hidden; flex-shrink: 0;">
                                <div style="height: 100%; width: ${pct}%; background: ${pct >= 100 ? '#22c55e' : 'var(--primary)'}; border-radius: 99px;"></div>
                            </div>
                            <span style="font-size: 0.8rem; font-weight: 700; color: ${pct >= 100 ? '#22c55e' : 'var(--text-primary)'}; min-width: 40px; text-align: right;">${pct}%</span>
                        </div>
                    </td>
                </tr>
                `;
            });
            tbody.innerHTML = html;

            const totalEl = document.getElementById('petugas-stat-total');
            const selesaiEl = document.getElementById('petugas-stat-selesai');
            const belumEl = document.getElementById('petugas-stat-belum');
            
            const pctSelesaiAll = totalAll > 0 ? ((selesaiAll / totalAll) * 100).toFixed(1) : 0;
            const pctBelumAll = totalAll > 0 ? ((belumAll / totalAll) * 100).toFixed(1) : 0;

            if (totalEl) totalEl.textContent = totalAll.toLocaleString('id-ID');
            if (selesaiEl) selesaiEl.innerHTML = `${selesaiAll.toLocaleString('id-ID')} <span style="font-size: 0.9rem; opacity: 0.8; font-weight: 500;">(${pctSelesaiAll}%)</span>`;
            if (belumEl) belumEl.innerHTML = `${belumAll.toLocaleString('id-ID')} <span style="font-size: 0.9rem; opacity: 0.8; font-weight: 500;">(${pctBelumAll}%)</span>`;

            return;
        }
        
        // Old logic fallback
        if (!baseFiltered) baseFiltered = window.lastBaseFiltered || [];
    };
"""

content = re.sub(
    r'window\.renderPetugasSummaryTable = function \(baseFiltered\) \{.*?(?=\n\n\s*// --- REKAP BELUM DITUGASKAN PER KECAMATAN ---)',
    lambda m: new_petugas_summary.strip(),
    content,
    flags=re.DOTALL
)

with open('app.js', 'w') as f:
    f.write(content)
