document.addEventListener('DOMContentLoaded', () => {
    // Pagination defaults
    window.petugasSummaryCurrentPage = window.petugasSummaryCurrentPage || 1;
    window.petugasSummaryPerPage = window.petugasSummaryPerPage || 25;
    
    window.changePetugasSummaryPerPage = function() {
        const select = document.getElementById('petugas-summary-per-page');
        if (select) {
            window.petugasSummaryPerPage = parseInt(select.value) || 25;
            window.petugasSummaryCurrentPage = 1;
            if (window.renderPetugasSummaryTable) window.renderPetugasSummaryTable(window.lastBaseFiltered);
        }
    };

    window.changePetugasSummaryPage = function(page) {
        window.petugasSummaryCurrentPage = page;
        if (window.renderPetugasSummaryTable) window.renderPetugasSummaryTable(window.lastBaseFiltered);
    };

    // Sanitize localStorage active_assign_subtab to avoid loading UB data by default
    const initialSubtab = localStorage.getItem('active_assign_subtab');
    if (initialSubtab === 'ub' || initialSubtab === 'se_ub') {
        localStorage.setItem('active_assign_subtab', 'se2026');
    }

    // Initialize user map from static file to avoid API failure during VPN
    window.userMap = window.STATIC_USER_MAP || {};

    // Helper to get CSS theme colors resolved for Chart.js
    function getThemeColor(varName, fallback) {
        const val = getComputedStyle(document.documentElement).getPropertyValue(varName).trim();
        return val || fallback;
    }

    const rawData = window.EMAIL_DATA || [];

    // Helper to highlight matching search query text
    function highlightText(text, query) {
        if (!query) return text;
        const escapedQuery = query.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&');
        const regex = new RegExp(`(${escapedQuery})`, 'gi');
        return text.replace(regex, '<mark class="highlight">$1</mark>');
    }

    // Helper to calculate percentage and round down (floor) to prevent false 100.00%
    function floorPct(val, total) {
        if (!total || total <= 0) return '0.00';
        if (val >= total) return '100.00';
        const pct = (val / total) * 100;
        if (pct < 0.01 && pct > 0) {
            return pct.toFixed(4);
        }
        const floored = Math.floor(pct * 100) / 100;
        if (floored >= 100 && val < total) {
            return '99.99';
        }
        return floored.toFixed(2);
    }

    function getFormattedDateLabels() {
        let t = new Date();
        if (window.IPAS_DATA && window.IPAS_DATA.updated_at) {
            t = new Date(window.IPAS_DATA.updated_at);
        }
        const y = new Date(t); y.setDate(y.getDate() - 1);
        const h2 = new Date(t); h2.setDate(h2.getDate() - 2);
        const fmt = d => String(d.getDate()).padStart(2, '0') + '/' + String(d.getMonth() + 1).padStart(2, '0');
        return {
            today: "Hari Ini (" + fmt(t) + ")",
            yesterday: "Kemarin (" + fmt(y) + ")",
            h2: "H-2 (" + fmt(h2) + ")"
        };
    }
    window.getFormattedDateLabels = getFormattedDateLabels;

    // UI elements
    const searchInput = document.getElementById('search-input');
    const sortSelect = document.getElementById('sort-select');
    const surveyFilterSelect = document.getElementById('survey-filter-select');
    const kabkotFilterSelect = document.getElementById('kabkot-filter-select');
    const pills = document.querySelectorAll('.pill');
    const companyListContainer = document.getElementById('company-list');
    const paginationContainer = document.getElementById('pagination');
    const viewModeToggleBtn = document.getElementById('toggle-view-mode');
    const companyTableWrapper = document.getElementById('company-table-wrapper');
    const companyTableBody = document.getElementById('company-table-body');
    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    const htmlElement = document.documentElement;

    // View mode state
    let viewMode = localStorage.getItem('viewMode') || 'card';

    function updateViewMode() {
        const isTable = viewMode === 'table';
        if (companyTableWrapper) companyTableWrapper.style.display = isTable ? 'block' : 'none';
        if (companyListContainer) companyListContainer.style.display = isTable ? 'none' : 'flex';
        if (viewModeToggleBtn) {
            viewModeToggleBtn.textContent = isTable ? 'Mode Kartu' : 'Mode Tabel';
        }
    }

    if (viewModeToggleBtn) {
        viewModeToggleBtn.addEventListener('click', () => {
            viewMode = viewMode === 'card' ? 'table' : 'card';
            localStorage.setItem('viewMode', viewMode);
            updateViewMode();
            renderList();
        });
    }

    updateViewMode();

    // Stats & Badge count elements
    const statTotalEl = document.getElementById('stat-total-companies');
    const statBouncedEl = document.getElementById('stat-bounced');
    const statPermanentEl = document.getElementById('stat-permanent');
    const statClickedEl = document.getElementById('stat-clicked');
    const statOpenedEl = document.getElementById('stat-opened');

    const countAll = document.getElementById('count-all');
    const countBounced = document.getElementById('count-bounced');
    const countPermanent = document.getElementById('count-permanent_fail');
    const countClicked = document.getElementById('count-clicked');
    const countOpened = document.getElementById('count-opened');
    const countDelivered = document.getElementById('count-delivered');
    const countQueued = document.getElementById('count-queued');
    const countNolog = document.getElementById('count-nolog');

    // Pagination configuration
    const ITEMS_PER_PAGE = 20;
    let currentPage = 1;

    let activeFilter = 'all';
    let activeSurveyFilter = 'all';
    let activeKabkotFilter = 'all';
    let searchQuery = '';
    let activeSort = 'name-asc';

    const kabkotMapping = {
        "7201": "Banggai",
        "7202": "Poso",
        "7203": "Donggala",
        "7204": "Toli-Toli",
        "7205": "Buol",
        "7206": "Morowali",
        "7207": "Banggai Kepulauan",
        "7208": "Parigi Moutong",
        "7209": "Tojo Una-Una",
        "7210": "Sigi",
        "7211": "Banggai Laut",
        "7212": "Morowali Utara",
        "7271": "Palu"
    };

    // Theme Switcher Setup
    const savedTheme = localStorage.getItem('theme') || 'light';
    htmlElement.setAttribute('data-theme', savedTheme);

    themeToggleBtn.addEventListener('click', () => {
        const currentTheme = htmlElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        htmlElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);

        // Re-render charts to update colors for the new theme
        setTimeout(() => {
            const activeTab = localStorage.getItem('active_tab') || 'se_umum';
            if (activeTab === 'se_umum') renderSeDashboard('se_umum');
            else if (activeTab === 'se_ub') renderSeDashboard('se_ub');
            else if (activeTab === 'assign') {
                renderAssignChart();
            }
        }, 50);
    });

    let supabaseClient;
    if (typeof window.supabase !== 'undefined' && window.SUPABASE_URL && window.SUPABASE_KEY) {
        supabaseClient = window.supabase.createClient(window.SUPABASE_URL, window.SUPABASE_KEY);
        window.supabaseClient = supabaseClient; // expose globally for download functions
        console.log("Initialized real Supabase client.");
    } else {
        console.log("Initializing mock Supabase client proxying to MySQL API.");
        supabaseClient = {
            from: function(tableName) {
                return {
                    select: function(cols) {
                        let req = { tableName, eqCol: null, eqVal: null, isSingle: false, orderCol: null };
                        let executor = {
                            eq: function(col, val) { req.eqCol = col; req.eqVal = val; return executor; },
                            single: function() { req.isSingle = true; return executor; },
                            order: function(col, opts) { req.orderCol = col; return executor; },
                            then: function(resolve, reject) {
                                let action = 'get_' + tableName.replace('_data','');
                                if (tableName === 'dashboard_store') action = 'get_store';
                                fetch(`https://dds-api.bpssulteng.id/api.php?action=${action}`)
                                    .then(res => res.json())
                                    .then(data => {
                                        if (req.eqCol && req.eqVal) {
                                            data = data.filter(d => d[req.eqCol] === req.eqVal);
                                        }
                                        if (req.isSingle) {
                                            if (data.length > 0) {
                                                if (tableName === 'dashboard_store' && typeof data[0].value === 'string') {
                                                    try { data[0].value = JSON.parse(data[0].value); } catch(e){}
                                                }
                                                resolve({ data: data[0], error: null });
                                            } else resolve({ data: null, error: { message: "No rows found" } });
                                        } else {
                                            resolve({ data: data, error: null });
                                        }
                                    }).catch(err => resolve({ data: null, error: err }));
                            }
                        };
                        return executor;
                    },
                    update: function(payload) {
                        return {
                            eq: async function(col, val) {
                                try {
                                    const response = await fetch(`https://dds-api.bpssulteng.id/api.php?action=update_${tableName.replace('_data','')}`, {
                                        method: 'POST',
                                        headers: {'Content-Type': 'application/json'},
                                        body: JSON.stringify({...payload, id: val})
                                    });
                                    const data = await response.json();
                                    return { data: data, error: null };
                                } catch(e) { return { data: null, error: e }; }
                            }
                        };
                    }
                };
            }
        };

        // Add rpc method for mock client
        supabaseClient.rpc = async function(fnName, params) {
            if (fnName === 'check_login') {
                try {
                    const response = await fetch(`https://dds-api.bpssulteng.id/api.php?action=check_login`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(params)
                    });
                    if (response.ok) {
                        const data = await response.json();
                        return { data: data, error: null };
                    } else {
                        return { data: null, error: { message: "Invalid credentials" } };
                    }
                } catch(e) {
                    return { data: null, error: e };
                }
            }
            return { data: null, error: { message: "Not implemented" } };
        };
    }

    let companies = [];
    let sourceData = [];
    let se_umumData = window.IPAS_DATA ? window.IPAS_DATA.se_umum : [];
    let se_ubData = window.IPAS_DATA ? window.IPAS_DATA.se_ub : [];

    // Group logs by company code
    function processGroupedData(dataArray) {
        const grouped = {};

        // Fallback map: jika database Supabase belum memiliki kolom survey_status,
        // kita ambil dari data.js lokal yang memiliki status lengkap hasil scraping.
        const localData = window.EMAIL_DATA || [];
        const localStatusMap = {};
        localData.forEach(r => {
            if (r.code && r.survey_status) {
                localStatusMap[r.code] = r.survey_status;
            }
        });

        dataArray.forEach(record => {
            const code = record.code;
            if (!grouped[code]) {
                grouped[code] = {
                    code: code,
                    company_name: record.company_name,
                    global_status: record.global_status,
                    survey_status: record.survey_status || localStatusMap[code] || "-",
                    email: record.email,
                    history: []
                };
            } else if (record.survey_status && record.survey_status !== "-") {
                grouped[code].survey_status = record.survey_status;
            }

            if (record.status !== '-' && record.timestamp !== '-') {
                grouped[code].history.push({
                    status: record.status,
                    timestamp: record.timestamp,
                    order: record.order
                });
            }
        });

        // Sort history and determine final status
        Object.values(grouped).forEach(comp => {
            comp.history.sort((a, b) => a.order - b.order);
            // Gunakan global_status yang sudah dihitung oleh database/scraper jika valid
            if (!comp.global_status || comp.global_status === '-') {
                if (comp.history.length > 0) {
                    comp.global_status = comp.history[comp.history.length - 1].status;
                }
            }
        });

        // Menyeimbangkan jumlah total perusahaan agar sesuai dengan total target Sensus Ekonomi UB
        const currentLen = Object.keys(grouped).length;
        const targetTotalUB = (window.IPAS_DATA && window.IPAS_DATA.se_ub_prov_total) || 1302;
        if (currentLen < targetTotalUB) {
            const diff = targetTotalUB - currentLen;
            for (let i = 0; i < diff; i++) {
                const dummyCode = `dummy-no-log-${i}`;
                grouped[dummyCode] = {
                    code: dummyCode,
                    company_name: `Target Usaha Besar (Tanpa Log Email - #${i + 1})`,
                    global_status: "-",
                    survey_status: "-",
                    email: "-",
                    history: []
                };
            }
        }

        return Object.values(grouped);
    }

    // Survey Status Badge Styling
    function getSurveyStatusStyle(status) {
        const s = status.toUpperCase().trim();
        if (s === 'DRAFT') return { bg: 'rgba(245, 158, 11, 0.1)', color: '#f59e0b', border: 'rgba(245, 158, 11, 0.3)' };
        if (s === 'OPEN') return { bg: 'rgba(59, 130, 246, 0.1)', color: '#3b82f6', border: 'rgba(59, 130, 246, 0.3)' };
        if (s.includes('SUBMITTED') || s === 'APPROVED') return { bg: 'rgba(16, 185, 129, 0.1)', color: '#10b981', border: 'rgba(16, 185, 129, 0.3)' };
        if (s === 'REJECTED') return { bg: 'rgba(239, 68, 68, 0.1)', color: '#ef4444', border: 'rgba(239, 68, 68, 0.3)' };
        return { bg: 'rgba(107, 114, 128, 0.1)', color: 'var(--text-secondary)', border: 'rgba(107, 114, 128, 0.3)' };
    }

    // Status Badge Colors & Styling
    function getStatusStyle(status) {
        const s = status.toLowerCase().trim();
        if (s === 'bounced' || s === 'permanent_fail' || s === 'permanent_failure') return { bg: 'rgba(239, 68, 68, 0.1)', color: 'var(--color-bounced)', border: 'rgba(239, 68, 68, 0.3)' };
        if (s === 'clicked') return { bg: 'rgba(139, 92, 246, 0.1)', color: 'var(--color-clicked)', border: 'rgba(139, 92, 246, 0.3)' };
        if (s === 'opened') return { bg: 'rgba(59, 130, 246, 0.1)', color: 'var(--color-opened)', border: 'rgba(59, 130, 246, 0.3)' };
        if (s === 'delivered') return { bg: 'rgba(16, 185, 129, 0.1)', color: 'var(--color-delivered)', border: 'rgba(16, 185, 129, 0.3)' };
        if (s === '-') return { bg: 'rgba(107, 114, 128, 0.1)', color: 'var(--color-nolog)', border: 'rgba(107, 114, 128, 0.3)' };
        return { bg: 'rgba(107, 114, 128, 0.1)', color: 'var(--color-queued)', border: 'rgba(107, 114, 128, 0.3)' };
    }

    // Calculate and display Stats & Filter Pill Count Badges
    function updateFiltersAndStats() {
        statTotalEl.textContent = companies.length;
        countAll.textContent = companies.length;

        const bounced = companies.filter(c => c.global_status.toLowerCase() === 'bounced').length;
        const permanentFails = companies.filter(c => {
            const st = c.global_status.toLowerCase();
            return st === 'permanent_fail' || st === 'permanent_failure';
        }).length;
        const clicked = companies.filter(c => c.global_status.toLowerCase() === 'clicked').length;
        const opened = companies.filter(c => c.global_status.toLowerCase() === 'opened').length;
        const delivered = companies.filter(c => c.global_status.toLowerCase() === 'delivered').length;
        const queued = companies.filter(c => c.global_status.toLowerCase() === 'queued').length;
        const nolog = companies.filter(c => c.global_status.trim() === '-').length;
        statBouncedEl.textContent = bounced;
        if (statPermanentEl) statPermanentEl.textContent = permanentFails;
        statClickedEl.textContent = clicked;
        statOpenedEl.textContent = opened;

        countBounced.textContent = bounced;
        if (countPermanent) countPermanent.textContent = permanentFails;
        countClicked.textContent = clicked;
        countOpened.textContent = opened;
        countDelivered.textContent = delivered;
        countQueued.textContent = queued;
        countNolog.textContent = nolog;
    }

    // Render Pagination Buttons
    function renderPagination(totalItems) {
        paginationContainer.innerHTML = '';
        const totalPages = Math.ceil(totalItems / ITEMS_PER_PAGE);

        if (totalPages <= 1) return; // No pagination needed if only 1 page

        // Previous Button
        const prevBtn = document.createElement('button');
        prevBtn.className = 'page-btn';
        prevBtn.innerHTML = '&laquo;';
        prevBtn.disabled = currentPage === 1;
        prevBtn.addEventListener('click', () => {
            if (currentPage > 1) {
                currentPage--;
                renderList();
                window.scrollTo({ top: document.querySelector('.filter-panel').offsetTop - 20, behavior: 'smooth' });
            }
        });
        paginationContainer.appendChild(prevBtn);

        // Page numbers
        let startPage = Math.max(1, currentPage - 2);
        let endPage = Math.min(totalPages, currentPage + 2);

        if (startPage > 1) {
            const firstBtn = document.createElement('button');
            firstBtn.className = 'page-btn';
            firstBtn.textContent = '1';
            firstBtn.addEventListener('click', () => {
                currentPage = 1;
                renderList();
            });
            paginationContainer.appendChild(firstBtn);

            if (startPage > 2) {
                const dots = document.createElement('span');
                dots.className = 'page-btn';
                dots.textContent = '...';
                dots.style.cursor = 'default';
                dots.style.border = 'none';
                dots.style.background = 'none';
                paginationContainer.appendChild(dots);
            }
        }

        for (let i = startPage; i <= endPage; i++) {
            const pageBtn = document.createElement('button');
            pageBtn.className = `page-btn ${i === currentPage ? 'active' : ''}`;
            pageBtn.textContent = i;
            pageBtn.addEventListener('click', () => {
                currentPage = i;
                renderList();
                window.scrollTo({ top: document.querySelector('.filter-panel').offsetTop - 20, behavior: 'smooth' });
            });
            paginationContainer.appendChild(pageBtn);
        }

        if (endPage < totalPages) {
            if (endPage < totalPages - 1) {
                const dots = document.createElement('span');
                dots.className = 'page-btn';
                dots.textContent = '...';
                dots.style.cursor = 'default';
                dots.style.border = 'none';
                dots.style.background = 'none';
                paginationContainer.appendChild(dots);
            }

            const lastBtn = document.createElement('button');
            lastBtn.className = 'page-btn';
            lastBtn.textContent = totalPages;
            lastBtn.addEventListener('click', () => {
                currentPage = totalPages;
                renderList();
            });
            paginationContainer.appendChild(lastBtn);
        }

        // Next Button
        const nextBtn = document.createElement('button');
        nextBtn.className = 'page-btn';
        nextBtn.innerHTML = '&raquo;';
        nextBtn.disabled = currentPage === totalPages;
        nextBtn.addEventListener('click', () => {
            if (currentPage < totalPages) {
                currentPage++;
                renderList();
                window.scrollTo({ top: document.querySelector('.filter-panel').offsetTop - 20, behavior: 'smooth' });
            }
        });
        paginationContainer.appendChild(nextBtn);
    }

    // Render Company List
    function renderList() {
        companyListContainer.innerHTML = '';

        // Filter
        let filtered = companies.filter(comp => {
            const matchesSearch =
                comp.company_name.toLowerCase().includes(searchQuery) ||
                comp.code.toLowerCase().includes(searchQuery) ||
                comp.email.toLowerCase().includes(searchQuery);

            const matchesFilter =
                activeFilter === 'all' ||
                comp.global_status.toLowerCase() === activeFilter ||
                (activeFilter === 'permanent_fail' && (comp.global_status.toLowerCase() === 'permanent_fail' || comp.global_status.toLowerCase() === 'permanent_failure'));

            const matchesSurveyFilter =
                activeSurveyFilter === 'all' ||
                comp.survey_status.toUpperCase() === activeSurveyFilter.toUpperCase();

            const prefix = comp.code ? comp.code.substring(0, 4) : '';
            const matchesKabkotFilter =
                activeKabkotFilter === 'all' ||
                (activeKabkotFilter === 'other' ? !kabkotMapping[prefix] : prefix === activeKabkotFilter);

            return matchesSearch && matchesFilter && matchesSurveyFilter && matchesKabkotFilter;
        });

        // Sort
        filtered.sort((a, b) => {
            if (activeSort === 'name-asc') {
                return a.company_name.localeCompare(b.company_name);
            } else if (activeSort === 'name-desc') {
                return b.company_name.localeCompare(a.company_name);
            } else if (activeSort === 'status-severity') {
                const severity = { 'bounced': 0, 'permanent_fail': 0, 'permanent_failure': 0, 'queued': 1, 'delivered': 2, 'opened': 3, 'clicked': 4 };
                const sevA = severity[a.global_status.toLowerCase()] ?? 5;
                const sevB = severity[b.global_status.toLowerCase()] ?? 5;
                return sevA - sevB;
            } else if (activeSort === 'survey-status-asc') {
                const severity = { 'draft': 1, 'open': 2, 'submitted': 3, 'approved': 4 };
                const sevA = severity[a.survey_status.toLowerCase()] ?? 5;
                const sevB = severity[b.survey_status.toLowerCase()] ?? 5;
                if (sevA !== sevB) return sevA - sevB;
                return a.company_name.localeCompare(b.company_name);
            } else if (activeSort === 'survey-status-desc') {
                const severity = { 'draft': 1, 'open': 2, 'submitted': 3, 'approved': 4 };
                const sevA = severity[a.survey_status.toLowerCase()] ?? 5;
                const sevB = severity[b.survey_status.toLowerCase()] ?? 5;
                if (sevA !== sevB) return sevB - sevA;
                return a.company_name.localeCompare(b.company_name);
            }
            return 0;
        });

        // Update pagination buttons based on total items
        renderPagination(filtered.length);

        // Slice data for current page
        const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
        const endIndex = startIndex + ITEMS_PER_PAGE;
        const pageItems = filtered.slice(startIndex, endIndex);

        if (filtered.length === 0) {
            if (viewMode === 'table' && companyTableBody) {
                companyTableBody.innerHTML = `
                    <tr>
                        <td colspan="8" style="text-align: center; padding: 2.5rem 1rem; color: var(--text-secondary);">
                            Tidak ada data perusahaan yang cocok. Coba ubah kata kunci atau filter status.
                        </td>
                    </tr>
                `;
            }
            companyListContainer.innerHTML = `
                <div class="empty-state">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <h3>Tidak ada data ditemukan</h3>
                    <p>Coba gunakan kata kunci pencarian lain atau pilih filter status berbeda.</p>
                </div>
            `;
            paginationContainer.innerHTML = '';
            return;
        }

        if (viewMode === 'table') {
            if (companyTableWrapper) companyTableWrapper.style.display = 'block';
            if (companyListContainer) companyListContainer.style.display = 'none';
            if (companyTableBody) {
                const tableRows = pageItems.map(comp => {
                    const statusStyle = getStatusStyle(comp.global_status);
                    const surveyStyle = getSurveyStatusStyle(comp.survey_status);
                    let rawKab = comp.kab_name || '';
                    if (rawKab && rawKab !== '-') {
                        rawKab = rawKab.replace(/^\[\d+\]\s*/, '').trim();
                        rawKab = rawKab.split(' ').map(w => w.charAt(0).toUpperCase() + w.substring(1).toLowerCase()).join(' ');
                    } else {
                        rawKab = '';
                    }
                    const kabkotName = rawKab || ((comp.code && typeof comp.code === 'string') ? (kabkotMapping[comp.code.substring(0, 4)] || 'Lainnya') : 'Lainnya');
                    const lastLog = comp.history.length ? comp.history[comp.history.length - 1] : { status: '-', timestamp: '-' };
                    let employeeName = '';
                    if (window.userMap && window.userMap[(comp.email || '').split('@')[0]]) {
                        employeeName = `<br><span style="font-size:0.75rem;color:var(--text-secondary);">${window.userMap[(comp.email || '').split('@')[0]]}</span>`;
                    }

                    return `
                        <tr>
                            <td>${highlightText(comp.code, searchQuery)}</td>
                            <td style="font-weight: 700;">${highlightText(comp.company_name, searchQuery)}</td>
                            <td>${highlightText(comp.email, searchQuery)}${employeeName}</td>
                            <td><span class="company-status-badge" style="--badge-bg: ${statusStyle.bg}; --badge-color: ${statusStyle.color}; --badge-border: ${statusStyle.border};">${comp.global_status}</span></td>
                            <td><span class="survey-status-badge" style="background-color: ${surveyStyle.bg}; color: ${surveyStyle.color}; border: 1px solid ${surveyStyle.border};">${comp.survey_status}</span></td>
                            <td>${kabkotName === 'Lainnya' ? '-' : kabkotName}</td>
                            <td>${lastLog.timestamp}</td>
                            <td>${lastLog.status}</td>
                        </tr>
                    `;
                }).join('');
                companyTableBody.innerHTML = tableRows;
            }
        } else {
            if (companyTableWrapper) companyTableWrapper.style.display = 'none';
            if (companyListContainer) companyListContainer.style.display = 'flex';
            pageItems.forEach(comp => {
                const card = document.createElement('div');
                card.className = 'company-card';

                const statusStyle = getStatusStyle(comp.global_status);
                let historyHTML = '';
                if (comp.history.length > 0) {
                    historyHTML = `
                        <div class="timeline-section">
                            <div class="timeline-title">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                                Riwayat Log Pengiriman
                            </div>
                            <div class="timeline-list">
                                ${comp.history.map(item => {
                        const stepStyle = getStatusStyle(item.status);
                        return `
                                        <div class="timeline-item" style="--node-color: ${stepStyle.color}">
                                            <div class="timeline-left">
                                                <span class="timeline-badge" style="--badge-bg: ${stepStyle.bg}; --badge-color: ${stepStyle.color}">${item.status}</span>
                                                <span class="timeline-email">${comp.email}</span>
                                            </div>
                                            <div class="timeline-time">${item.timestamp}</div>
                                        </div>
                                    `;
                    }).join('')}
                            </div>
                        </div>
                    `;
                } else {
                    historyHTML = `
                        <div class="timeline-section" style="color: var(--text-muted); font-size: 0.85rem; font-style: italic;">
                            Tidak ada data log email yang tercatat.
                        </div>
                    `;
                }

                let rawKab = comp.kab_name || '';
                if (rawKab && rawKab !== '-') {
                    rawKab = rawKab.replace(/^\[\d+\]\s*/, '').trim();
                    rawKab = rawKab.split(' ').map(w => w.charAt(0).toUpperCase() + w.substring(1).toLowerCase()).join(' ');
                } else {
                    rawKab = '';
                }
                const kabkotName = rawKab || ((comp.code && typeof comp.code === 'string') ? (kabkotMapping[comp.code.substring(0, 4)] || 'Lainnya') : 'Lainnya');

                const surveyStyle = getSurveyStatusStyle(comp.survey_status);
                card.innerHTML = `
                    <div class="company-header">
                        <div class="company-info">
                            <div class="company-name-row">
                                <div class="company-name">${highlightText(comp.company_name, searchQuery)}</div>
                            </div>
                            <div class="company-meta">
                                <span class="code-badge">${highlightText(comp.code, searchQuery)}</span>
                                ${(kabkotName && kabkotName !== 'Lainnya') ? `
                                <span class="code-badge" style="background-color: rgba(99, 102, 241, 0.08); color: var(--primary); border: 1px solid rgba(99, 102, 241, 0.15); font-weight: 700;">
                                    ${kabkotName}
                                </span>` : ''}
                                <span class="code-badge" style="background-color: ${surveyStyle.bg}; color: ${surveyStyle.color}; border: 1px solid ${surveyStyle.border}; font-weight: 700; text-transform: uppercase;">
                                    ${comp.survey_status}
                                </span>
                                <span class="company-email-text">${highlightText(comp.email, searchQuery)}</span>
                            </div>
                        </div>
                        <div class="right-badges">
                            <span class="company-status-badge" style="--badge-bg: ${statusStyle.bg}; --badge-color: ${statusStyle.color}; --badge-border: ${statusStyle.border}">
                                ${comp.global_status}
                            </span>
                            <div class="toggle-icon">
                                <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7"></path>
                                </svg>
                            </div>
                        </div>
                    </div>
                    <div class="details-wrapper">
                        ${historyHTML}
                    </div>
                `;

                card.addEventListener('click', (e) => {
                    if (e.target.closest('a') || e.target.closest('button')) return;

                    const isExpanded = card.classList.contains('expanded');
                    const details = card.querySelector('.details-wrapper');

                    document.querySelectorAll('.company-card.expanded').forEach(c => {
                        if (c !== card) {
                            c.classList.remove('expanded');
                            const otherDetails = c.querySelector('.details-wrapper');
                            otherDetails.style.overflow = 'hidden';
                            otherDetails.style.maxHeight = null;
                        }
                    });

                    card.classList.toggle('expanded');

                    if (!isExpanded) {
                        details.style.maxHeight = details.scrollHeight + "px";
                        details.addEventListener('transitionend', function handler() {
                            if (card.classList.contains('expanded')) {
                                details.style.maxHeight = 'none';
                                details.style.overflow = 'visible';
                            }
                            details.removeEventListener('transitionend', handler);
                        });
                    } else {
                        details.style.overflow = 'hidden';
                        details.style.maxHeight = details.scrollHeight + "px";
                        details.offsetHeight;
                        details.style.maxHeight = null;
                    }
                });

                companyListContainer.appendChild(card);
            });
        }
    }

    // Listeners
    searchInput.addEventListener('input', (e) => {
        searchQuery = e.target.value.toLowerCase().trim();
        currentPage = 1; // Reset to first page
        renderList();
    });

    sortSelect.addEventListener('change', (e) => {
        activeSort = e.target.value;
        currentPage = 1; // Reset to first page
        renderList();
    });

    surveyFilterSelect.addEventListener('change', (e) => {
        activeSurveyFilter = e.target.value;
        currentPage = 1; // Reset to first page
        renderList();
    });

    if (kabkotFilterSelect) {
        kabkotFilterSelect.addEventListener('change', (e) => {
            activeKabkotFilter = e.target.value;
            currentPage = 1; // Reset to first page
            renderList();
        });
    }

    pills.forEach(pill => {
        pill.addEventListener('click', () => {
            pills.forEach(p => p.classList.remove('active'));
            pill.classList.add('active');
            activeFilter = pill.getAttribute('data-filter');
            currentPage = 1; // Reset to first page
            renderList();
        });
    });

    // SE Umum & UB Search Input Listeners
    const seUmumSearchInput = document.getElementById('se_umum-search-input');
    if (seUmumSearchInput) {
        seUmumSearchInput.addEventListener('input', () => {
            renderSeDashboard('se_umum');
        });
    }
    const seUbSearchInput = document.getElementById('se_ub-search-input');
    if (seUbSearchInput) {
        seUbSearchInput.addEventListener('input', () => {
            renderSeDashboard('se_ub');
        });
    }

    // SLS Search & Filter Listeners
    const slsSearchInput = document.getElementById('sls-search-input');
    if (slsSearchInput) {
        slsSearchInput.addEventListener('input', () => {
            renderSlsTable();
        });
    }

    const assignSlsSearchInput = document.getElementById('assign-sls-search-input');
    if (assignSlsSearchInput) {
        assignSlsSearchInput.addEventListener('input', () => {
            if (typeof window.updateGranularStatusFilterOptions === 'function') {
                window.updateGranularStatusFilterOptions();
            }
            window.renderGranularAssignmentsTable(true);
        });
    }

    const petugasSearchInput = document.getElementById('petugas-search-input');
    if (petugasSearchInput) {
        petugasSearchInput.addEventListener('input', () => {
            window.petugasCurrentPage = 1;
            renderPetugasTable();
        });
    }
    const syncSearchInput = document.getElementById('sync-search-input');
    if (syncSearchInput) {
        syncSearchInput.addEventListener('input', () => {
            window.syncCurrentPage = 1;
            renderSyncTable();
        });
    }
    const diffSearchInput = document.getElementById('diff-search-input');
    if (diffSearchInput) {
        diffSearchInput.addEventListener('input', () => {
            window.diffCurrentPage = 1;
            renderDiffTable();
        });
    }
    const slsAssignmentFilter = document.getElementById('sls-assignment-filter');
    if (slsAssignmentFilter) {
        slsAssignmentFilter.addEventListener('change', () => {
            renderSlsTable();
        });
    }

    // Sensus Ekonomi Table Sorting State
    window.seSorts = {
        se_umum: { column: 'kabupaten', order: 'asc' },
        se_ub: { column: 'kabupaten', order: 'asc' }
    };

    // Table Header Sort Click Handler
    window.sortSeTable = function (surveyType, column) {
        const current = window.seSorts[surveyType];
        if (current.column === column) {
            current.order = current.order === 'asc' ? 'desc' : 'asc';
        } else {
            current.column = column;
            current.order = 'desc';
            if (column === 'kabupaten') {
                current.order = 'asc';
            }
        }
        window.renderSeDashboard(surveyType);
    };

    // Petugas Table Sorting State
    window.petugasSorts = {
        se_umum: { column: 'progres', order: 'desc' },
        se_ub: { column: 'progres', order: 'desc' }
    };

    // Petugas Table Header Sort Click Handler
    window.sortPetugasTable = function (surveyType, column) {
        const current = window.petugasSorts[surveyType];
        if (current.column === column) {
            current.order = current.order === 'asc' ? 'desc' : 'asc';
        } else {
            current.column = column;
            current.order = 'desc';
            if (column === 'petugas' || column === 'role' || column === 'kabupaten') {
                current.order = 'asc';
            }
        }
        window.renderSeDashboard(surveyType);
    };

    window.expandAllKabs = function (surveyType) {
        const ipasDataObj = window.IPAS_DATA || { se_umum: [], se_ub: [] };
        const surveyData = ipasDataObj[surveyType] || [];
        if (!window.expandedSeKabs) window.expandedSeKabs = { se_umum: {}, se_ub: {} };
        if (!window.expandedSeKabs[surveyType]) window.expandedSeKabs[surveyType] = {};
        surveyData.forEach(item => {
            window.expandedSeKabs[surveyType][item.kabupaten] = true;
        });
        window.renderSeDashboard(surveyType);
    };

    window.collapseAllKabs = function (surveyType) {
        if (!window.expandedSeKabs) window.expandedSeKabs = { se_umum: {}, se_ub: {} };
        window.expandedSeKabs[surveyType] = {};
        window.renderSeDashboard(surveyType);
    };

    // Dynamic Table Headers Renderer
    window.renderSeTableHeaders = function (surveyType) {
        const table = document.querySelector(`#tab-content-${surveyType} .ipas-table`);
        if (!table) return;
        const thead = table.querySelector('thead');
        if (!thead) return;

        const getIcon = (col) => {
            const sort = window.seSorts[surveyType];
            if (sort.column === col) {
                return sort.order === 'asc' ? ' ▲' : ' ▼';
            }
            return ' ⇅';
        };

        thead.innerHTML = `
            <tr>
                <th rowspan="2" class="sortable" onclick="sortSeTable('${surveyType}', 'kabupaten')" style="font-family: 'Outfit', sans-serif; vertical-align: middle;">
                    Kabupaten/Kota${getIcon('kabupaten')}
                </th>
                <th rowspan="2" class="sortable" onclick="sortSeTable('${surveyType}', 'total_prelist')" style="font-family: 'Outfit', sans-serif; text-align: right; vertical-align: middle; color: var(--text-secondary);">
                    Total Target${getIcon('total_prelist')}
                </th>
                <th rowspan="2" class="sortable" onclick="sortSeTable('${surveyType}', 'total_draft')" style="font-family: 'Outfit', sans-serif; text-align: right; color: #f59e0b; vertical-align: middle;">
                    Draft${getIcon('total_draft')}
                </th>
                <th rowspan="2" class="sortable" onclick="sortSeTable('${surveyType}', 'total_open')" style="font-family: 'Outfit', sans-serif; text-align: right; color: #3b82f6; vertical-align: middle;">
                    Open${getIcon('total_open')}
                </th>
                <th colspan="5" style="font-family: 'Outfit', sans-serif; text-align: center; color: var(--color-delivered); border-bottom: 1px solid var(--card-border);">
                    Submitted (Selesai)
                </th>
                <th rowspan="2" class="sortable" onclick="sortSeTable('${surveyType}', 'persentase')" style="font-family: 'Outfit', sans-serif; text-align: center; vertical-align: middle;">
                    % Capaian${getIcon('persentase')}
                </th>
                <th rowspan="2" class="sortable" onclick="sortSeTable('${surveyType}', 'delta_persen')" style="font-family: 'Outfit', sans-serif; text-align: center; vertical-align: middle;">
                    Delta (%)${getIcon('delta_persen')}
                </th>
                <th rowspan="2" class="sortable" onclick="sortSeTable('${surveyType}', 'new_usaha_overall')" style="font-family: 'Outfit', sans-serif; text-align: center; vertical-align: middle;">
                    Tambahan (Non-Target)${getIcon('new_usaha_overall')}
                </th>
            </tr>
            <tr>
                <th class="sortable" onclick="sortSeTable('${surveyType}', 'total_submitted')" style="font-family: 'Outfit', sans-serif; text-align: right; color: var(--color-delivered); font-size: 0.8rem; padding: 0.4rem 0.75rem;">
                    Total${getIcon('total_submitted')}
                </th>
                <th style="font-family: 'Outfit', sans-serif; text-align: right; color: var(--color-opened); font-size: 0.8rem; padding: 0.4rem 0.75rem;">
                    Pencacah
                </th>
                <th style="font-family: 'Outfit', sans-serif; text-align: right; color: #d97706; font-size: 0.8rem; padding: 0.4rem 0.75rem;">
                    Respondent
                </th>
                <th style="font-family: 'Outfit', sans-serif; text-align: right; color: #047857; font-size: 0.8rem; padding: 0.4rem 0.75rem;">
                    Approved
                </th>
                <th style="font-family: 'Outfit', sans-serif; text-align: right; color: #dc2626; font-size: 0.8rem; padding: 0.4rem 0.75rem;">
                    Rejected
                </th>
            </tr>
        `;
    };

    window.toggleDailyPopover = function (event, element) {
        event.stopPropagation();
        const popover = element.nextElementSibling;
        if (!popover) return;
        const isActive = popover.classList.contains('active');

        // Close all other active popovers
        document.querySelectorAll('.daily-popover.active').forEach(p => {
            if (p !== popover) p.classList.remove('active');
        });

        if (isActive) {
            popover.classList.remove('active');
        } else {
            popover.classList.add('active');

            // Adjust position if offscreen
            const rect = popover.getBoundingClientRect();
            if (rect.left < 0) {
                popover.style.left = '0';
                popover.style.right = 'auto';
            } else if (rect.right > window.innerWidth) {
                popover.style.right = '0';
                popover.style.left = 'auto';
            }
        }
    };

    // Close popovers on body click
    document.addEventListener('click', () => {
        document.querySelectorAll('.daily-popover.active').forEach(p => {
            p.classList.remove('active');
        });
    });

    // Sensus Ekonomi Dashboard Render Engine (Umum or UB)
    function getSlsStatusCounts(slsCode, slsTotal, surveyType) {
        const slsStatusMap = window.IPAS_DATA ? (window.IPAS_DATA[surveyType + '_sls_status'] || {}) : {};
        const slsData = slsStatusMap[slsCode] || { target: {}, nontarget: {} };

        const targetCounts = slsData.target || {};
        const nontargetCounts = slsData.nontarget || {};

        let activeTargetSum = 0;
        const statuses = new Set([...Object.keys(targetCounts), ...Object.keys(nontargetCounts)]);

        for (const count of Object.values(targetCounts)) {
            activeTargetSum += count;
        }

        const openTargets = Math.max(0, slsTotal - activeTargetSum);

        const combined = {};
        if (openTargets > 0) {
            combined["OPEN"] = openTargets;
        }

        statuses.forEach(status => {
            const tCount = targetCounts[status] || 0;
            const ntCount = nontargetCounts[status] || 0;
            const total = tCount + ntCount;
            if (total > 0) {
                combined[status] = total;
            }
        });

        return combined;
    }

    const statusStyles = {
        'OPEN': 'background: rgba(100, 116, 139, 0.1); color: #475569; border: 1px solid rgba(100, 116, 139, 0.2);',
        'DRAFT': 'background: rgba(245, 158, 11, 0.12); color: #d97706; border: 1px solid rgba(245, 158, 11, 0.25);',
        'SUBMITTED BY PENCACAH': 'background: rgba(16, 185, 129, 0.12); color: #059669; border: 1px solid rgba(16, 185, 129, 0.25);',
        'SUBMITTED RESPONDENT': 'background: rgba(16, 185, 129, 0.12); color: #059669; border: 1px solid rgba(16, 185, 129, 0.25);',
        'SUBMITTED': 'background: rgba(16, 185, 129, 0.12); color: #059669; border: 1px solid rgba(16, 185, 129, 0.25);',
        'APPROVED BY PENGAWAS': 'background: rgba(4, 120, 87, 0.15); color: #047857; border: 1px solid rgba(4, 120, 87, 0.3); font-weight: 700;',
        'APPROVED': 'background: rgba(4, 120, 87, 0.15); color: #047857; border: 1px solid rgba(4, 120, 87, 0.3); font-weight: 700;',
        'REJECTED BY PENGAWAS': 'background: rgba(239, 68, 68, 0.12); color: #dc2626; border: 1px solid rgba(239, 68, 68, 0.25);',
        'REJECTED': 'background: rgba(239, 68, 68, 0.12); color: #dc2626; border: 1px solid rgba(239, 68, 68, 0.25);',
        'REVOKED BY PENGAWAS': 'background: rgba(153, 27, 27, 0.15); color: #991b1b; border: 1px solid rgba(153, 27, 27, 0.3);'
    };

    function getStatusBadgeStyle(status) {
        const key = status.toUpperCase();
        if (statusStyles[key]) return statusStyles[key];
        if (key.includes('REVOKED')) return statusStyles['REVOKED BY PENGAWAS'];
        if (key.includes('REJECTED')) return statusStyles['REJECTED'];
        if (key.includes('APPROVED')) return statusStyles['APPROVED'];
        if (key.includes('SUBMITTED')) return statusStyles['SUBMITTED'];
        return 'background: rgba(156, 163, 175, 0.1); color: #4b5563; border: 1px solid rgba(156, 163, 175, 0.2);';
    }

    // Sensus Ekonomi Dashboard Render Engine (Umum or UB)
    window.renderSeDashboard = async function (surveyType) {
        const ipasDataObj = window.IPAS_DATA || { se_umum: [], se_ub: [] };
        
        // --- MySQL FETCH DASHBOARD KPI ---
        let mysqlPrelist = 0;
        let mysqlSelesai = 0;
        let kpiLoadedFromMysql = false;

        try {
            const url = `https://dds-api.bpssulteng.id/api.php?action=get_dashboard_summary&survey=${surveyType}&kab=all`;
            const res = await fetch(url);
            const text = await res.text();
            if (text.includes("DNS Sinkhole")) {
                throw new Error("DNS Sinkhole block detected");
            }
            const data = JSON.parse(text);
            
            data.forEach(row => {
                mysqlPrelist += parseInt(row.total_target) || 0;
                mysqlSelesai += parseInt(row.selesai) || 0;
            });
            kpiLoadedFromMysql = true;
        } catch (e) {
            console.warn("Failed to load KPI from MySQL (falling back to Supabase/IPAS_DATA):", e.message);
        }

        // --- CONTINUE OLD BEHAVIOR FOR DAILY STATS ---
        const surveyData = ipasDataObj[surveyType] || [];

        // Build a lookup map of (kab_name, date, survey_type) -> count and breakdown from window.DAILY_SUBMISSION_STATS
        const statsMap = {};
        const statsBreakdownMap = {};
        if (window.DAILY_SUMMARY && Array.isArray(window.DAILY_SUMMARY)) {
            window.DAILY_SUMMARY.forEach(r => {
                if (r.tanggal && r.kabupaten) {
                    const key = `${r.kabupaten.toUpperCase()}_${r.tanggal}_${surveyType}`;
                    // We only have combined stats from granular_data, so we'll apply them to se_umum
                    // If you want accurate split later, the DB needs survey_type column.
                    if (surveyType === 'se_umum') {
                        statsMap[key] = (statsMap[key] || 0) + (r.total_submitted || 0);
                        
                        if (!statsBreakdownMap[key]) statsBreakdownMap[key] = {};
                        statsBreakdownMap[key]["APPROVED BY Pengawas"] = (statsBreakdownMap[key]["APPROVED BY Pengawas"] || 0) + (r.total_approved || 0);
                        statsBreakdownMap[key]["REJECTED BY Pengawas"] = (statsBreakdownMap[key]["REJECTED BY Pengawas"] || 0) + (r.total_rejected || 0);
                        statsBreakdownMap[key]["SUBMITTED BY Pencacah"] = (statsBreakdownMap[key]["SUBMITTED BY Pencacah"] || 0) + (r.total_submitted || 0);
                    }
                }
            });
        } else if (window.DAILY_SUBMISSION_STATS && Array.isArray(window.DAILY_SUBMISSION_STATS)) {
            window.DAILY_SUBMISSION_STATS.forEach(r => {
                if (r.date && r.kab_name && r.survey_type) {
                    const cleanKab = r.kab_name.replace(/\[\d+\]\s*/, '').trim().toUpperCase();
                    const key = `${cleanKab}_${r.date}_${r.survey_type}`;
                    statsMap[key] = (statsMap[key] || 0) + (r.count || 0);
                    
                    if (r.status) {
                        if (!statsBreakdownMap[key]) statsBreakdownMap[key] = {};
                        statsBreakdownMap[key][r.status] = (statsBreakdownMap[key][r.status] || 0) + (r.count || 0);
                    }
                }
            });
        }

        // Helper to compute WITA date strings relative to updated_at without timezone jumps
        const getWitaDateStr = (offsetDays = 0) => {
            let baseDateStr = '';
            if (ipasDataObj && ipasDataObj.updated_at) {
                baseDateStr = ipasDataObj.updated_at.substring(0, 10);
            }
            
            let d;
            if (baseDateStr && /^\d{4}-\d{2}-\d{2}$/.test(baseDateStr)) {
                const parts = baseDateStr.split('-');
                d = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]), 12, 0, 0);
            } else {
                const now = new Date();
                const utc = now.getTime() + (now.getTimezoneOffset() * 60000);
                d = new Date(utc + (3600000 * 8));
            }
            
            if (offsetDays !== 0) d.setDate(d.getDate() + offsetDays);
            return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
        };

        const todayDateStr = getWitaDateStr(0);
        const yesterdayDateStr = getWitaDateStr(-1);
        const twoDaysDateStr = getWitaDateStr(-2);

        // Use breakdown data from generate_ipas_report.py as-is (no inflation from DAILY_SUBMISSION_STATS)
        // Daily counts are derived from the sum of the breakdown so they always match — no "Belum Terkategori"
        const scaleBreakdown = (breakdown, targetCount) => {
            if (!breakdown || typeof breakdown !== 'object') {
                if (targetCount > 0) {
                    return { "SUBMITTED BY Pencacah": targetCount };
                }
                return {};
            }
            const sum = Object.values(breakdown).reduce((a, b) => a + b, 0);
            if (sum === 0 || targetCount === 0) {
                if (targetCount > 0) {
                    return { "SUBMITTED BY Pencacah": targetCount };
                }
                return {};
            }
            if (sum === targetCount) return breakdown;

            const scale = targetCount / sum;
            const newBreakdown = {};
            let newSum = 0;
            const entries = Object.entries(breakdown);
            entries.forEach(([status, val]) => {
                const scaled = Math.round(val * scale);
                newBreakdown[status] = scaled;
                newSum += scaled;
            });

            const diff = targetCount - newSum;
            if (diff !== 0 && entries.length > 0) {
                let maxStatus = null;
                let maxVal = -1;
                for (const [status, val] of Object.entries(newBreakdown)) {
                    if (val > maxVal) {
                        maxVal = val;
                        maxStatus = status;
                    }
                }
                if (maxStatus) {
                    newBreakdown[maxStatus] = Math.max(0, newBreakdown[maxStatus] + diff);
                }
            }
            return newBreakdown;
        };
        const scaleKecamatans = (kecamatanList, targetCount, dayKey, parentItem) => {
            if (!kecamatanList || kecamatanList.length === 0) return;
            const completedKey = `${dayKey}_completed`;
            const breakdownKey = `${dayKey}_completed_breakdown`;

            const sumKec = kecamatanList.reduce((acc, k) => acc + (k[completedKey] || 0), 0);
            
            // If the raw BPS data had no kecamatan-level daily stats (sumKec === 0),
            // or if the total count is 0
            if (sumKec === 0 || targetCount === 0) {
                if (targetCount > 0) {
                    const totalSubmittedKec = kecamatanList.reduce((acc, k) => acc + (k.total_submitted || 0), 0);
                    const parentBreakdownKey = `${dayKey}_completed_breakdown`;
                    const parentBreakdown = parentItem ? parentItem[parentBreakdownKey] : null;

                    if (totalSubmittedKec === 0) {
                        // Even fallback if no kecamatan has completed targets yet
                        const base = Math.floor(targetCount / kecamatanList.length);
                        let remainder = targetCount % kecamatanList.length;
                        kecamatanList.forEach(k => {
                            k[completedKey] = base + (remainder > 0 ? 1 : 0);
                            if (remainder > 0) remainder--;
                            
                            if (parentBreakdown && typeof parentBreakdown === 'object') {
                                k[breakdownKey] = {};
                                Object.entries(parentBreakdown).forEach(([status, val]) => {
                                    k[breakdownKey][status] = Math.round(val / kecamatanList.length);
                                });
                            } else {
                                k[breakdownKey] = { "SUBMITTED BY Pencacah": k[completedKey] };
                            }
                        });
                    } else {
                        // Proportional distribution fallback!
                        let distributedSum = 0;
                        kecamatanList.forEach(k => {
                            const share = (k.total_submitted || 0) / totalSubmittedKec;
                            k[completedKey] = Math.round(targetCount * share);
                            distributedSum += k[completedKey];
                            
                            // Scale status breakdown from parent
                            if (parentBreakdown && typeof parentBreakdown === 'object') {
                                k[breakdownKey] = {};
                                Object.entries(parentBreakdown).forEach(([status, val]) => {
                                    k[breakdownKey][status] = Math.round(val * share);
                                });
                            } else {
                                k[breakdownKey] = { "SUBMITTED BY Pencacah": k[completedKey] };
                            }
                        });
                        
                        // Adjust remainder to match exactly
                        const diff = targetCount - distributedSum;
                        if (diff !== 0) {
                            let maxKec = null;
                            let maxVal = -1;
                            kecamatanList.forEach(k => {
                                if ((k.total_submitted || 0) > maxVal) {
                                    maxVal = k.total_submitted || 0;
                                    maxKec = k;
                                }
                            });
                            if (maxKec) {
                                maxKec[completedKey] = Math.max(0, maxKec[completedKey] + diff);
                                // Recalculate breakdown for the remainder adjustment
                                const share = (maxKec.total_submitted || 0) / totalSubmittedKec;
                                if (parentBreakdown && typeof parentBreakdown === 'object') {
                                    maxKec[breakdownKey] = {};
                                    let bdSum = 0;
                                    Object.entries(parentBreakdown).forEach(([status, val]) => {
                                        maxKec[breakdownKey][status] = Math.round(val * share);
                                        bdSum += maxKec[breakdownKey][status];
                                    });
                                    // Adjust breakdown sum to match maxKec[completedKey]
                                    const bdDiff = maxKec[completedKey] - bdSum;
                                    const bdKeys = Object.keys(maxKec[breakdownKey]);
                                    if (bdDiff !== 0 && bdKeys.length > 0) {
                                        maxKec[breakdownKey][bdKeys[0]] = Math.max(0, maxKec[breakdownKey][bdKeys[0]] + bdDiff);
                                    }
                                } else {
                                    maxKec[breakdownKey] = { "SUBMITTED BY Pencacah": maxKec[completedKey] };
                                }
                            }
                        }
                    }
                } else {
                    kecamatanList.forEach(k => {
                        k[completedKey] = 0;
                        k[breakdownKey] = {};
                    });
                }
                return;
            }

            // Normal path when BPS raw data has kecamatan-level daily stats
            if (sumKec === targetCount) return;

            const scale = targetCount / sumKec;
            let newSum = 0;
            kecamatanList.forEach(k => {
                k[completedKey] = Math.round((k[completedKey] || 0) * scale);
                newSum += k[completedKey];
            });

            const diff = targetCount - newSum;
            if (diff !== 0) {
                let maxKec = null;
                let maxVal = -1;
                kecamatanList.forEach(k => {
                    if (k[completedKey] > maxVal) {
                        maxVal = k[completedKey];
                        maxKec = k;
                    }
                });
                if (maxKec) {
                    maxKec[completedKey] = Math.max(0, maxKec[completedKey] + diff);
                }
            }

            kecamatanList.forEach(k => {
                k[breakdownKey] = scaleBreakdown(k[breakdownKey] || {}, k[completedKey]);
            });
        };

        surveyData.forEach(item => {
            // Clean up any leftover "Belum Terkategori" from old data
            if (item.today_completed_breakdown) delete item.today_completed_breakdown["Belum Terkategori"];
            if (item.yesterday_completed_breakdown) delete item.yesterday_completed_breakdown["Belum Terkategori"];
            if (item.two_days_ago_completed_breakdown) delete item.two_days_ago_completed_breakdown["Belum Terkategori"];

            // Update with uncapped real-time counts from DAILY_SUBMISSION_STATS if larger
            const cleanKab = item.kabupaten.replace(/\[\d+\]\s*/, '').trim().toUpperCase();
            const rawToday = statsMap[`${cleanKab}_${todayDateStr}_${surveyType}`] || 0;
            const rawYesterday = statsMap[`${cleanKab}_${yesterdayDateStr}_${surveyType}`] || 0;
            const rawTwoDays = statsMap[`${cleanKab}_${twoDaysDateStr}_${surveyType}`] || 0;

            item.today_completed = Math.max(item.today_completed || 0, rawToday);
            item.yesterday_completed = Math.max(item.yesterday_completed || 0, rawYesterday);
            item.two_days_ago_completed = Math.max(item.two_days_ago_completed || 0, rawTwoDays);

            // Scale breakdowns to match the uncapped count or load directly from sync cache
            const keyToday = `${cleanKab}_${todayDateStr}_${surveyType}`;
            const keyYesterday = `${cleanKab}_${yesterdayDateStr}_${surveyType}`;
            const keyTwoDays = `${cleanKab}_${twoDaysDateStr}_${surveyType}`;

            if (statsBreakdownMap[keyToday]) {
                item.today_completed_breakdown = statsBreakdownMap[keyToday];
            } else {
                item.today_completed_breakdown = scaleBreakdown(item.today_completed_breakdown, item.today_completed);
            }

            if (statsBreakdownMap[keyYesterday]) {
                item.yesterday_completed_breakdown = statsBreakdownMap[keyYesterday];
            } else {
                item.yesterday_completed_breakdown = scaleBreakdown(item.yesterday_completed_breakdown, item.yesterday_completed);
            }

            if (statsBreakdownMap[keyTwoDays]) {
                item.two_days_ago_completed_breakdown = statsBreakdownMap[keyTwoDays];
            } else {
                item.two_days_ago_completed_breakdown = scaleBreakdown(item.two_days_ago_completed_breakdown, item.two_days_ago_completed);
            }

            // Distribute and scale the uncapped count down to Kecamatans
            scaleKecamatans(item.kecamatan_list, item.today_completed, 'today', item);
            scaleKecamatans(item.kecamatan_list, item.yesterday_completed, 'yesterday', item);
            scaleKecamatans(item.kecamatan_list, item.two_days_ago_completed, 'two_days_ago', item);
        });

        // Calculate Summary
        let prelist = 0, draft = 0, openVal = 0, submitted = 0, rejected = 0, approved = 0, today = 0, yesterday = 0, twoDaysAgo = 0, newToday = 0, newRumahToday = 0;
        let submittedPencacah = 0, submittedRespondent = 0;
        const todayBreakdown = {};
        const yesterdayBreakdown = {};
        const twoDaysAgoBreakdown = {};

        const statusColors = {
            "DRAFT": "#f59e0b",
            "OPEN": "#3b82f6",
            "SUBMITTED BY Pencacah": "#10b981",
            "SUBMITTED RESPONDENT": "#d97706",
            "APPROVED BY Pengawas": "#047857",
            "REJECTED BY Pengawas": "#dc2626",
            "EDITED BY Admin Kabupaten": "#6366f1",
            "REVOKED BY Pengawas": "#a855f7",
            "COMPLETED BY Admin Kabupaten": "#14b8a6",
            "REJECTED BY Admin Kabupaten": "#ef4444",
            "EDITED BY Pengawas": "#ec4899"
        };
        const statusSums = {};
        Object.keys(statusColors).forEach(st => statusSums[st] = 0);

        surveyData.forEach(item => {
            prelist += item.total_prelist || 0;
            draft += item.total_draft || 0;
            openVal += item.total_open || 0;
            submitted += item.total_submitted || 0;
            rejected += item.total_rejected || 0;
            approved += item.total_approved || 0;
            submittedPencacah += item.total_submitted_pencacah || 0;
            submittedRespondent += item.total_submitted_respondent || 0;
            today += item.today_completed || 0;
            yesterday += item.yesterday_completed || 0;
            twoDaysAgo += item.two_days_ago_completed || 0;
            newToday += item.new_usaha_today || 0;
            newRumahToday += item.new_rumah_today || 0;
            item.sisa_usaha = Math.max(0, (item.total_prelist || 0) - (item.total_submitted || 0));

            // Sum BPS status breakdown
            if (item.breakdown) {
                for (const [st, val] of Object.entries(item.breakdown)) {
                    statusSums[st] = (statusSums[st] || 0) + val;
                }
            }

            // Sum breakdowns for province
            if (item.today_completed_breakdown) {
                for (const [st, val] of Object.entries(item.today_completed_breakdown)) {
                    todayBreakdown[st] = (todayBreakdown[st] || 0) + val;
                }
            }
            if (item.yesterday_completed_breakdown) {
                for (const [st, val] of Object.entries(item.yesterday_completed_breakdown)) {
                    yesterdayBreakdown[st] = (yesterdayBreakdown[st] || 0) + val;
                }
            }
            if (item.two_days_ago_completed_breakdown) {
                for (const [st, val] of Object.entries(item.two_days_ago_completed_breakdown)) {
                    twoDaysAgoBreakdown[st] = (twoDaysAgoBreakdown[st] || 0) + val;
                }
            }
        });

        // Override prelist with PROVINSI_TOTAL if available
        const provTotalKey = surveyType + "_prov_total";
        if (ipasDataObj[provTotalKey]) {
            prelist = ipasDataObj[provTotalKey];
        }

        // Override with MySQL KPI if loaded successfully and contains completed data
        if (kpiLoadedFromMysql && mysqlPrelist > 0 && mysqlSelesai > 0) {
            prelist = mysqlPrelist;
            submitted = mysqlSelesai;
        }

        const persentase = floorPct(submitted, prelist);
        const sisa = prelist - submitted;

        // Calculate Provincial Delta dynamically from item deltas
        let sumSelesaiYesterday = 0;
        let sumTargetYesterday = 0;
        surveyData.forEach(item => {
            const pctNow = item.persentase || 0;
            const itemDelta = item.delta_persen || 0;
            const pctYesterday = pctNow - itemDelta;
            sumSelesaiYesterday += (pctYesterday / 100) * (item.total_prelist || 0);
            sumTargetYesterday += (item.total_prelist || 0);
        });
        const provPctYesterday = sumTargetYesterday > 0 ? (sumSelesaiYesterday / sumTargetYesterday) * 100 : 0;
        let provDelta = parseFloat(persentase) - provPctYesterday;
        if (Math.abs(provDelta) < 0.01) provDelta = 0;

        // Format helper
        const formatNum = (num) => new Intl.NumberFormat('id-ID').format(num || 0);

        const getDailyProgressCellHTML = (count, breakdown, headerTitle, isEstimate) => {
            if (!count || count <= 0) return `<span>0</span>`;

            const estimatePrefix = isEstimate ? `<span title="Data estimasi — snapshot H-2 tidak tersedia" style="color:#f59e0b;font-weight:800;cursor:help;margin-right:2px;">~</span>` : '';
            const itemsHTML = Object.entries(breakdown || {})
                .map(([status, val]) => `
                    <div class="popover-item">
                        <span class="popover-badge">${status}</span>
                        <span class="popover-count">${formatNum(val)}</span>
                    </div>
                `).join('');

            return `
                <div class="daily-progress-wrapper">
                    <span>${estimatePrefix}${formatNum(count)}</span>
                    <span class="daily-dropdown-trigger" onclick="window.toggleDailyPopover(event, this)">▼</span>
                    <div class="daily-popover">
                        <div class="popover-header">${headerTitle}${isEstimate ? ' <span style="color:#f59e0b;font-size:0.7rem;">(estimasi)</span>' : ''}</div>
                        ${itemsHTML || '<div style="color: var(--text-secondary); font-size: 0.75rem;">Tidak ada detail status</div>'}
                    </div>
                </div>
            `;
        };

        // Update stats elements
        const prelistWrapperEl = document.getElementById(`${surveyType}-stat-total-prelist-wrapper`);
        if (prelistWrapperEl) {
            const breakdown = {
                "OPEN (Belum dikerjakan)": openVal,
                "DRAFT (Sedang dikerjakan)": draft,
                "SUBMITTED BY Pencacah": submittedPencacah,
                "SUBMITTED RESPONDENT": submittedRespondent,
                "APPROVED BY Pengawas": approved,
                "REJECTED BY Pengawas": rejected
            };
            const itemsHTML = Object.entries(breakdown)
                .map(([status, val]) => {
                    let badgeStyle = "background: rgba(100,116,139,0.1); color: #475569; border-color: rgba(100,116,139,0.2);";
                    if (status.includes("DRAFT")) badgeStyle = "background: rgba(245,158,11,0.12); color: #d97706; border-color: rgba(245,158,11,0.25);";
                    if (status.includes("OPEN")) badgeStyle = "background: rgba(59,130,246,0.1); color: #2563eb; border-color: rgba(59,130,246,0.2);";
                    if (status.includes("SUBMITTED")) badgeStyle = "background: rgba(16,185,129,0.1); color: #059669; border-color: rgba(16,185,129,0.25);";
                    if (status.includes("APPROVED")) badgeStyle = "background: rgba(4,120,87,0.15); color: #047857; border-color: rgba(4,120,87,0.3);";
                    if (status.includes("REJECTED")) badgeStyle = "background: rgba(239,68,68,0.15); color: #ef4444; border-color: rgba(239,68,68,0.3);";

                    return `
                    <div class="popover-item">
                        <span class="popover-badge" style="${badgeStyle}">${status}</span>
                        <span class="popover-count">${formatNum(val)}</span>
                    </div>
                    `;
                }).join('');

            const provNewTotalKey = surveyType + "_prov_new_total";
            const provNewRumahTotalKey = surveyType + "_prov_new_rumah_total";
            const newUsahaProv = ipasDataObj[provNewTotalKey] || 0;
            const newRumahProv = ipasDataObj[provNewRumahTotalKey] || 0;

            prelistWrapperEl.innerHTML = `
                <div class="daily-progress-wrapper" style="display: flex; align-items: baseline; gap: 0.25rem; flex-direction: row;">
                    <span id="${surveyType}-stat-total-prelist" style="font-weight: 800;">${formatNum(prelist)}</span>
                    <span class="daily-dropdown-trigger" onclick="window.toggleDailyPopover(event, this)" style="color: var(--primary); background: rgba(99,102,241,0.1); border-color: rgba(99,102,241,0.25); margin-left: 0.25rem;">▼</span>
                    <div class="daily-popover">
                        <div class="popover-header" style="color: var(--primary);">BREAKDOWN STATUS ASSIGNMENT</div>
                        ${itemsHTML}
                        <div class="popover-header" style="color: var(--primary); margin-top: 0.75rem;">TAMBAHAN NONTARGET TERDETEKSI</div>
                        <div class="popover-item" style="border-top: 1px dashed var(--card-border); margin-top: 0.25rem; padding-top: 0.25rem;">
                            <span style="font-size: 0.7rem; color: var(--primary); font-weight: 600;">Tambahan Usaha Baru</span>
                            <span class="popover-count" style="color: var(--primary);">+${formatNum(newUsahaProv)}</span>
                        </div>
                        <div class="popover-item">
                            <span style="font-size: 0.7rem; color: #ec4899; font-weight: 600;">Tambahan Rumah Baru</span>
                            <span class="popover-count" style="color: #ec4899;">+${formatNum(newRumahProv)}</span>
                        </div>
                        <div class="popover-item" style="border-top: 1px solid var(--card-border); margin-top: 0.25rem; padding-top: 0.25rem;">
                            <span style="font-size: 0.75rem; color: var(--text-secondary); font-weight: 700; font-style: italic;">⚠ Sudah termasuk dalam total resmi FASIH</span>
                        </div>
                    </div>
                </div>
            `;
        }

        const newTodayEl = document.getElementById(`${surveyType}-stat-new-today`);
        if (newTodayEl) newTodayEl.textContent = `+${formatNum(newToday)}`;

        const newRumahTodayEl = document.getElementById(`${surveyType}-stat-new-rumah-today`);
        if (newRumahTodayEl) newRumahTodayEl.textContent = `+${formatNum(newRumahToday)}`;

        const draftEl = document.getElementById(`${surveyType}-stat-draft`);
        if (draftEl) draftEl.textContent = formatNum(draft);

        const openEl = document.getElementById(`${surveyType}-stat-open`);
        if (openEl) openEl.textContent = formatNum(openVal);

        const submittedEl = document.getElementById(`${surveyType}-stat-submitted`);
        if (submittedEl) submittedEl.textContent = formatNum(submitted);

        const percentEl = document.getElementById(`${surveyType}-stat-percentage`);
        if (percentEl) percentEl.textContent = `(${persentase}%)`;

        // Populate premium BPS summary cards
        const premiumPctEl = document.getElementById(`${surveyType}-stat-premium-pct`);
        if (premiumPctEl) premiumPctEl.textContent = `${persentase} %`;

        const premiumCountEl = document.getElementById(`${surveyType}-stat-premium-count`);
        if (premiumCountEl) premiumCountEl.textContent = `${formatNum(submitted)} dari ${formatNum(prelist)} Assignment`;

        const submittedWrapperEl = document.getElementById(`${surveyType}-stat-submitted-wrapper`);
        if (submittedWrapperEl) {
            const breakdown = {
                "APPROVED BY Pengawas": approved,
                "REJECTED BY Pengawas": rejected,
                "SUBMITTED BY Pencacah": submittedPencacah,
                "SUBMITTED RESPONDENT": submittedRespondent
            };
            const itemsHTML = Object.entries(breakdown)
                .map(([status, val]) => `
                    <div class="popover-item">
                        <span class="popover-badge" style="background: rgba(16,185,129,0.1); color: #059669; border-color: rgba(16,185,129,0.25);">${status}</span>
                        <span class="popover-count">${formatNum(val)}</span>
                    </div>
                `).join('');

            submittedWrapperEl.innerHTML = `
                <div class="daily-progress-wrapper" style="display: flex; align-items: baseline; gap: 0.25rem; flex-direction: row;">
                    <span id="${surveyType}-stat-submitted" style="font-weight: 700;">${formatNum(submitted)}</span>
                    <span id="${surveyType}-stat-percentage" style="font-size: 0.85rem; font-weight: 700; color: var(--color-delivered);">(${persentase}%)</span>
                    ${provDelta !== 0 ? `<span style="font-size: 0.75rem; font-weight: 800; color: ${provDelta > 0 ? '#22c55e' : (provDelta < 0 ? '#ef4444' : 'inherit')}; margin-left: 0.2rem;">${provDelta > 0 ? '+' : ''}${provDelta.toFixed(2)}%</span>` : ''}
                    <span class="daily-dropdown-trigger" onclick="window.toggleDailyPopover(event, this)" style="color: var(--color-delivered); background: rgba(16,185,129,0.1); border-color: rgba(16,185,129,0.25); margin-left: 0.25rem;">▼</span>
                    <div class="daily-popover">
                        <div class="popover-header" style="color: var(--color-delivered);">BREAKDOWN TOTAL SELESAI</div>
                        ${itemsHTML}
                    </div>
                </div>
            `;
        }

        const rejectedEl = document.getElementById(`${surveyType}-stat-rejected`);
        if (rejectedEl) rejectedEl.textContent = formatNum(rejected);

        // Build rejected breakdown by aggregating status breakdowns across all days/all data
        const allRejectedBreakdown = {};
        surveyData.forEach(item => {
            // Collect from all breakdown objects to reconstruct rejected-type statuses
            [item.today_completed_breakdown, item.yesterday_completed_breakdown, item.two_days_ago_completed_breakdown].forEach(bd => {
                if (!bd) return;
                Object.entries(bd).forEach(([st, val]) => {
                    const stUpper = st.toUpperCase();
                    if (stUpper.includes('REJECTED') || stUpper.includes('REVOKED')) {
                        allRejectedBreakdown[st] = (allRejectedBreakdown[st] || 0) + val;
                    }
                });
            });
        });

        // Update top Rejected card (wrapper) with popover breakdown
        const rejectedWrapperEl = document.getElementById(`${surveyType}-stat-rejected-wrapper`);
        if (rejectedWrapperEl) {
            if (rejected <= 0) {
                rejectedWrapperEl.innerHTML = `<span>0</span>`;
            } else {
                const hasBreakdown = Object.keys(allRejectedBreakdown).length > 0;
                const itemsHTML = Object.entries(allRejectedBreakdown)
                    .map(([status, val]) => {
                        let labelText = status.replace('REJECTED BY ', 'Oleh ');
                        if (status.toUpperCase().includes('REVOKED')) {
                            labelText = status.replace(/REVOKED BY /i, 'Ditarik ');
                        }
                        return `
                            <div class="popover-item">
                                <span class="popover-badge" style="background: rgba(239,68,68,0.15); color: #ef4444; border-color: rgba(239,68,68,0.3);">${labelText}</span>
                                <span class="popover-count">${formatNum(val)}</span>
                            </div>
                        `;
                    }).join('');
                rejectedWrapperEl.innerHTML = `
                    <div class="daily-progress-wrapper">
                        <span style="color: #ef4444; font-weight: 800;">${formatNum(rejected)}</span>
                        ${hasBreakdown ? `<span class="daily-dropdown-trigger" onclick="window.toggleDailyPopover(event, this)" style="color: #ef4444; background: rgba(239,68,68,0.1); border-color: rgba(239,68,68,0.3);">▼</span>
                        <div class="daily-popover">
                            <div class="popover-header" style="color: #ef4444;">BREAKDOWN REJECTED</div>
                            ${itemsHTML}
                            <div class="popover-item" style="border-top: 1px dashed var(--card-border); margin-top: 0.25rem; padding-top: 0.25rem;">
                                <span style="font-size: 0.7rem; color: var(--text-secondary);">Total</span>
                                <span class="popover-count" style="color: #ef4444;">${formatNum(rejected)}</span>
                            </div>
                        </div>` : ''}
                    </div>
                `;
            }
        }

        // Calculate and set card percentages with dynamic precision for small numbers
        const formatPctVal = (v, tot) => {
            if (tot <= 0) return '0.00';
            const pct = (v / tot) * 100;
            if (pct > 0 && pct < 0.01) return pct.toFixed(4);
            return pct.toFixed(2);
        };

        const updateDailyStatCard = (count, breakdown, cardId, pctId, title, isAlwaysEmpty = false) => {
            const countEl = document.getElementById(cardId);
            const pctEl = document.getElementById(pctId);
            const cardEl = countEl?.closest('.stat-card-compact');
            if (countEl) {
                if (isAlwaysEmpty) {
                    countEl.innerHTML = `<span style="font-weight: 800; font-size: 1.6rem; color: var(--text-secondary); line-height: 1.1;">-</span>`;
                    if (pctEl) pctEl.textContent = '';
                    if (cardEl) {
                        cardEl.setAttribute('title', 'Tidak ada penarikan data pada hari ini sehingga data tidak tersedia');
                        cardEl.style.cursor = 'help';
                    }
                } else if (!count || count <= 0) {
                    countEl.innerHTML = `<span style="color: var(--text-secondary); font-size: 0.72rem; font-weight: 600; text-transform: uppercase;">Belum ada data</span>`;
                    if (pctEl) pctEl.textContent = '';
                    if (cardEl) {
                        cardEl.removeAttribute('title');
                        cardEl.style.cursor = 'default';
                    }
                } else {
                    countEl.innerHTML = getDailyProgressCellHTML(count, breakdown, title);
                    if (pctEl) {
                        const pctVal = formatPctVal(count, prelist);
                        pctEl.textContent = `(${pctVal}%)`;
                    }
                    if (cardEl) {
                        cardEl.removeAttribute('title');
                        cardEl.style.cursor = 'default';
                    }
                }
            }
        };

        // Removed: Overwriting today/yesterday/twoDaysAgo from DAILY_SUMMARY
        // IPAS_DATA already contains the live delta calculated by the python script
        updateDailyStatCard(today, todayBreakdown, `${surveyType}-stat-today`, `${surveyType}-stat-today-pct`, 'SUBMIT HARI INI', false);
        updateDailyStatCard(yesterday, yesterdayBreakdown, `${surveyType}-stat-yesterday`, `${surveyType}-stat-yesterday-pct`, 'SUBMIT KEMARIN', false);
        updateDailyStatCard(twoDaysAgo, twoDaysAgoBreakdown, `${surveyType}-stat-2days`, `${surveyType}-stat-2days-pct`, 'SUBMIT 2 HARI LALU', false);

        // Populate Regency/City Ranking List
        const rankingListEl = document.getElementById(`${surveyType}-ranking-list`);
        if (rankingListEl) {
            const sortedForRanking = [...surveyData]
                .map(item => {
                    const tot = item.total_prelist || 0;
                    const sub = item.total_submitted || 0;
                    const pct = tot > 0 ? (sub / tot) * 100 : 0;
                    return { item, pct };
                })
                .sort((a, b) => b.pct - a.pct);

            const renderRankingList = (limit) => {
                let html = sortedForRanking.slice(0, limit).map((entry, idx) => {
                    const item = entry.item;
                    const pct = entry.pct;
                    const rawName = item.kabupaten || "";
                    const cleanName = rawName.replace(/\[\d+\]\s*/, "").trim();
                    
                    let rankIcon = `${idx + 1}.`;
                    if (idx === 0) rankIcon = "🥇";
                    else if (idx === 1) rankIcon = "🥈";
                    else if (idx === 2) rankIcon = "🥉";

                    let deltaHtml = "";
                    // User requested to hide delta from ranking list
                    // if (item.delta_persen !== undefined && item.delta_persen !== 0) { ... }

                    return `
                    <div style="display: flex; align-items: center; justify-content: space-between; font-size: 0.8rem; padding: 0.25rem 0; border-bottom: 1px dashed rgba(249, 115, 22, 0.12);">
                        <div style="display: flex; align-items: center; gap: 0.45rem; max-width: 60%;">
                            <span style="font-size: 0.95rem; font-weight: 800; min-width: 22px; display: inline-block; text-align: center;">${rankIcon}</span>
                            <span style="font-weight: 750; color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${cleanName}">${cleanName}</span>
                        </div>
                        <div style="text-align: right;">
                            <span style="font-weight: 850; color: #a8542a;">${pct.toFixed(2)}%</span>${deltaHtml}
                            <div style="font-size: 0.65rem; color: var(--text-secondary); line-height: 1.1;">${formatNum(item.total_submitted)} / ${formatNum(item.total_prelist)}</div>
                        </div>
                    </div>
                    `;
                }).join('');

                if (limit < sortedForRanking.length) {
                    html += `<button onclick="window.openRankingModal('${surveyType}')" style="margin-top: 0.5rem; width: 100%; background: rgba(99, 102, 241, 0.1); color: var(--primary); border: none; padding: 0.4rem; border-radius: 4px; font-weight: 700; cursor: pointer; font-size: 0.75rem;">Lihat Selengkapnya</button>`;
                }

                rankingListEl.innerHTML = html;
            };

            window[`rankingData_${surveyType}`] = sortedForRanking;

            if (!window.openRankingModal) {
                window.openRankingModal = (sType) => {
                    const data = window[`rankingData_${sType}`] || [];
                    const modalBody = document.getElementById('ranking-modal-body');
                    if (modalBody) {
                        modalBody.innerHTML = data.map((entry, idx) => {
                            const item = entry.item;
                            const pct = entry.pct;
                            const rawName = item.kabupaten || "";
                            const cleanName = rawName.replace(/\[\d+\]\s*/, "").trim();
                            
                            let rankIcon = `${idx + 1}.`;
                            if (idx === 0) rankIcon = "🥇";
                            else if (idx === 1) rankIcon = "🥈";
                            else if (idx === 2) rankIcon = "🥉";

                            let deltaHtml = "";
                            // User requested to hide delta from ranking list
                            // if (item.delta_persen !== undefined && item.delta_persen !== 0) { ... }

                            return `
                            <div style="display: flex; align-items: center; justify-content: space-between; font-size: 0.85rem; padding: 0.35rem 0; border-bottom: 1px dashed rgba(249, 115, 22, 0.15);">
                                <div style="display: flex; align-items: center; gap: 0.5rem;">
                                    <span style="font-size: 0.9rem; font-weight: 800; min-width: 24px; text-align: center;">${rankIcon}</span>
                                    <span style="font-weight: 750; color: var(--text-primary);">${cleanName}</span>
                                </div>
                                <div style="text-align: right;">
                                    <span style="font-weight: 850; color: #a8542a; font-size: 0.95rem;">${pct.toFixed(2)}%</span>${deltaHtml}
                                    <div style="font-size: 0.7rem; color: var(--text-secondary); line-height: 1.1; margin-top: 1px;">Selesai: ${formatNum(item.total_submitted)} / ${formatNum(item.total_prelist)}</div>
                                </div>
                            </div>
                            `;
                        }).join('');
                    }
                    const modal = document.getElementById('ranking-modal');
                    if (modal) {
                        modal.style.display = 'flex';
                    }
                };
            }

            const currentLimit = 5;
            if (rankingListEl) {
                rankingListEl.style.maxHeight = '165px';
            }
            renderRankingList(currentLimit);
        }

        // Total Tambahan Usaha card (kumulatif)
        let newOverall = 0;
        let newRumahOverall = 0;
        surveyData.forEach(item => {
            newOverall += item.new_usaha_overall || 0;
            newRumahOverall += item.new_rumah_overall || 0;
        });
        if (ipasDataObj[surveyType + "_prov_new_total"]) {
            newOverall = ipasDataObj[surveyType + "_prov_new_total"];
        }
        if (ipasDataObj[surveyType + "_prov_new_rumah_total"]) {
            newRumahOverall = ipasDataObj[surveyType + "_prov_new_rumah_total"];
        }
        const newOverallMergedEl = document.getElementById(`${surveyType}-stat-new-overall-merged`);
        if (newOverallMergedEl) newOverallMergedEl.textContent = formatNum(newOverall + newRumahOverall);

        const newBreakdownSubtextEl = document.getElementById(`${surveyType}-stat-new-breakdown-subtext`);
        if (newBreakdownSubtextEl) {
            newBreakdownSubtextEl.textContent = `${formatNum(newOverall)} usaha | ${formatNum(newRumahOverall)} rumah`;
        }

        const newTodaySubtextEl = document.getElementById(`${surveyType}-stat-new-today-subtext`);
        if (newTodaySubtextEl) {
            newTodaySubtextEl.textContent = `+${formatNum(newToday + newRumahToday)} hari ini`;
        }

        // Kenaikan Persentase
        const kenaikanEl = document.getElementById(`${surveyType}-stat-kenaikan`);
        if (kenaikanEl) {
            kenaikanEl.innerHTML = `<span style="color: var(--color-delivered);">+${pctToday}% hari ini</span> <span style="color: var(--card-border);">|</span> <span style="color: #f59e0b;">+${pctYesterday}% kemarin</span>`;
        }

        const progressBar = document.getElementById(`${surveyType}-progress-bar`);
        if (progressBar) {
            progressBar.style.width = persentase + '%';
        }

        const sisaUsahaEl = document.getElementById(`${surveyType}-stat-sisa-usaha`);
        if (sisaUsahaEl) sisaUsahaEl.textContent = formatNum(sisa);

        const todayCompletedEl = document.getElementById(`${surveyType}-stat-today-completed`);
        if (todayCompletedEl) todayCompletedEl.textContent = formatNum(today);

        const vsYesterdayWrapper = document.getElementById(`${surveyType}-stat-vs-yesterday-wrapper`);
        if (vsYesterdayWrapper) {
            if (today >= yesterday) {
                vsYesterdayWrapper.innerHTML = `<span style="color: var(--color-delivered); background-color: rgba(16, 185, 129, 0.1); padding: 0.15rem 0.45rem; border-radius: 0.5rem; font-weight: 700; font-size: 0.75rem;">▲ vs ${formatNum(yesterday)} kemarin</span>`;
            } else {
                vsYesterdayWrapper.innerHTML = `<span style="color: var(--color-bounced); background-color: rgba(239, 68, 68, 0.1); padding: 0.15rem 0.45rem; border-radius: 0.5rem; font-weight: 700; font-size: 0.75rem;">▼ vs ${formatNum(yesterday)} kemarin</span>`;
            }
        }

        // Dynamically build the expanded stats grid
        const statsExpandedEl = document.getElementById(`${surveyType}-stats-expanded`);
        if (statsExpandedEl) {
            let cardsHTML = '';
            const majorStatuses = ["OPEN", "SUBMITTED BY Pencacah", "APPROVED BY Pengawas", "DRAFT", "REJECTED BY Pengawas", "SUBMITTED RESPONDENT"];
            
            Object.entries(statusColors).forEach(([st, color]) => {
                const sumVal = statusSums[st] || 0;
                if (sumVal > 0 || majorStatuses.includes(st)) {
                    const pctOfTotal = prelist > 0 ? ((sumVal / prelist) * 100).toFixed(2) : '0.00';
                    cardsHTML += `
                        <div class="stat-card-compact" style="--stat-color: ${color};">
                            <div class="stat-label" style="font-size: 0.7rem; font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${st}">${st}</div>
                            <div class="stat-value" style="font-family: monospace; font-weight: 800; font-size: 1.25rem;">${formatNum(sumVal)}</div>
                            <div class="stat-subtext" style="font-size: 0.65rem; color: var(--text-secondary); font-weight: 600;">(${pctOfTotal}%)</div>
                        </div>
                    `;
                }
            });
            
            // Tambahan (Non-Target) Card
            cardsHTML += `
                <div class="stat-card-compact" style="--stat-color: var(--primary); cursor: pointer;" onclick="openProvincialNewBusinessesModal('${surveyType}', 'all')">
                    <div class="stat-label" style="font-size: 0.7rem; font-weight: 700; white-space: nowrap;">TAMBAHAN (NON-TARGET)</div>
                    <div class="stat-value" style="font-family: monospace; font-weight: 800; font-size: 1.25rem;">${formatNum(newOverall + newRumahOverall)}</div>
                    <div class="stat-subtext" style="font-size: 0.65rem; color: var(--text-secondary); line-height: 1.2;">
                        <span>${formatNum(newOverall)} usaha | ${formatNum(newRumahOverall)} rumah</span>
                        <br/><span style="color: var(--color-delivered);">+${formatNum(newToday + newRumahToday)} hari ini</span>
                    </div>
                </div>
            `;
            
            // Sisa Target Card
            const sisaUsahaNum = Math.max(0, prelist - submitted);
            const sisaPct = prelist > 0 ? ((sisaUsahaNum / prelist) * 100).toFixed(2) : '0.00';
            cardsHTML += `
                <div class="stat-card-compact" style="--stat-color: var(--text-secondary);">
                    <div class="stat-label" style="font-size: 0.7rem; font-weight: 700; white-space: nowrap;">SISA TARGET</div>
                    <div class="stat-value" style="font-family: monospace; font-weight: 800; font-size: 1.25rem;">${formatNum(sisaUsahaNum)}</div>
                    <div class="stat-subtext" style="font-size: 0.65rem; color: var(--text-secondary); font-weight: 600;">(${sisaPct}%)</div>
                </div>
            `;
            
            statsExpandedEl.innerHTML = cardsHTML;
        }
        // Render Table with Filtering & Sorting
        if (!window.expandedSeKabs) {
            window.expandedSeKabs = { se_umum: {}, se_ub: {} };
        }
        if (!window.expandedSeKabs[surveyType]) {
            window.expandedSeKabs[surveyType] = {};
        }

        const searchVal = (document.getElementById(`${surveyType}-search-input`).value || '').toLowerCase().trim();
        const capaianFilterVal = document.getElementById(`${surveyType}-capaian-filter`)?.value || 'all';
        const kabFilterEl = document.getElementById(`${surveyType}-kab-filter`);
        const selectedKab = kabFilterEl?.value || 'all';
        const tbody = document.getElementById(`${surveyType}-table-body`);
        tbody.innerHTML = '';

        let filtered = surveyData.map(item => {
            // Check if filtered by kab
            if (selectedKab !== 'all' && item.kabupaten !== selectedKab) return null;

            const kabMatch = item.kabupaten.toLowerCase().includes(searchVal);
            const matchingKecs = (item.kecamatan_list || []).filter(kec =>
                kec.kec_name.toLowerCase().includes(searchVal)
            );

            if (kabMatch || matchingKecs.length > 0) {
                if ((!kabMatch && matchingKecs.length > 0 && searchVal !== "") || selectedKab !== 'all') {
                    window.expandedSeKabs[surveyType][item.kabupaten] = true;
                }
                return item;
            }
            return null;
        }).filter(item => item !== null);

        // Apply Capaian filter
        if (capaianFilterVal !== 'all') {
            filtered = filtered.filter(item => {
                const pct = parseFloat(item.persentase) || 0;
                if (capaianFilterVal === 'high') return pct >= 80;
                if (capaianFilterVal === 'med') return pct >= 50 && pct < 80;
                if (capaianFilterVal === 'low') return pct < 50;
                return true;
            });
        }

        // Read view level selector
        const viewLevel = document.getElementById(`${surveyType}-view-level`)?.value || 'kabupaten';

        // Always show kabupaten filter dropdown for Rincian Kabupaten and Ranking Kecamatan
        if (kabFilterEl) {
            kabFilterEl.style.display = (viewLevel === 'kecamatan' || viewLevel === 'kabupaten') ? '' : 'none';
        }

        // Render Top 3 Kecamatan if filtered by Kab
        const topKecContainer = document.getElementById(`${surveyType}-top-kecamatan-container`);
        if (topKecContainer) {
            if (viewLevel === 'kabupaten' && selectedKab !== 'all') {
                const kabData = surveyData.find(k => k.kabupaten === selectedKab);
                if (kabData) {
                    const sortedKecs = (kabData.kecamatan_list || []).filter(k => k.kec_name !== '-' && !k.kec_name.includes('[000]')).sort((a, b) => b.persentase - a.persentase);
                    const top3 = sortedKecs.slice(0, 3);
                    const kabDelta = kabData.delta_persen || 0;
                    const deltaColor = kabDelta > 0 ? '#22c55e' : (kabDelta < 0 ? '#ef4444' : 'var(--text-secondary)');
                    const deltaSign = kabDelta > 0 ? '+' : '';

                    let html = `
                        <div style="flex: 1; min-width: 200px; display: flex; flex-direction: column; justify-content: center;">
                            <div style="font-size: 0.8rem; font-weight: 700; color: var(--text-secondary); text-transform: uppercase;">Total Capaian</div>
                            <div style="font-size: 1.5rem; font-weight: 800; color: var(--text-primary); margin-top: 0.2rem;">${kabData.persentase}%</div>
                            <div style="font-size: 0.85rem; font-weight: 700; color: ${deltaColor}; margin-top: 0.2rem;">${deltaSign}${kabDelta.toFixed(2)}% vs Kemarin</div>
                        </div>
                        <div style="flex: 3; display: flex; flex-direction: column;">
                            <div style="font-size: 0.8rem; font-weight: 700; color: var(--text-secondary); text-transform: uppercase; margin-bottom: 0.5rem;">Top 3 Kecamatan Tertinggi</div>
                            <div style="display: flex; gap: 1rem;">
                    `;
                    top3.forEach((k, idx) => {
                        const medal = idx === 0 ? '🥇' : idx === 1 ? '🥈' : '🥉';
                        html += `
                            <div style="flex: 1; background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 0.5rem; padding: 0.75rem; display: flex; flex-direction: column;">
                                <div style="display: flex; align-items: center; justify-content: space-between;">
                                    <span style="font-size: 1.25rem;">${medal}</span>
                                    <span style="font-size: 1.1rem; font-weight: 800; color: var(--color-delivered);">${k.persentase}%</span>
                                </div>
                                <div style="font-size: 0.75rem; font-weight: 700; color: var(--text-primary); margin-top: 0.5rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${k.kec_name}">${k.kec_name}</div>
                                <div style="font-size: 0.65rem; color: var(--text-secondary); margin-top: 0.2rem;">Selesai: ${formatNum(k.total_submitted)} / ${formatNum(k.total_prelist)}</div>
                            </div>
                        `;
                    });
                    html += `</div></div>`;
                    topKecContainer.innerHTML = html;
                    topKecContainer.style.display = 'flex';
                }
            } else {
                topKecContainer.style.display = 'none';
            }
        }

        // Update title and toggle expand/collapse visibility
        const tableTitleEl = document.getElementById(`${surveyType}-table-title`);
        const expandCollapseEl = document.getElementById(`${surveyType}-expand-collapse-btns`);
        if (tableTitleEl) {
            const selectedKab = kabFilterEl?.value || 'all';
            if (viewLevel === 'kecamatan' && selectedKab !== 'all') {
                const kabLabel = selectedKab.replace(/\[\d+\]\s*/, '').trim();
                tableTitleEl.textContent = `Ranking Kecamatan — ${kabLabel}`;
            } else {
                const titles = { kabupaten: 'Rincian per Kabupaten/Kota', kecamatan: 'Ranking Kecamatan (Semua Kab/Kota)', petugas: 'Rincian per Petugas' };
                tableTitleEl.textContent = titles[viewLevel] || titles.kabupaten;
            }
        }
        if (expandCollapseEl) {
            expandCollapseEl.style.display = viewLevel === 'kabupaten' ? '' : 'none';
        }
        const allPetugas = window.PETUGAS_DATA || [];
        const hasRoles = allPetugas.some(p => typeof p.roleName === 'string' && p.roleName.trim() !== '' && p.roleName.trim() !== '-');
        const roleFilterEl = document.getElementById(`${surveyType}-role-filter`);
        if (roleFilterEl) {
            roleFilterEl.style.display = (viewLevel === 'petugas' && hasRoles) ? '' : 'none';
        }

        // Dispatch to specialized renderer
        if (viewLevel === 'kecamatan') {
            renderKecamatanFlatList();
            return;
        }
        if (viewLevel === 'petugas') {
            renderPetugasFlatList();
            return;
        }
        if (viewLevel === 'target') {
            document.getElementById(`${surveyType}-view-level`).value = 'kabupaten';
            document.getElementById('assign-sls-search-input').value = searchVal;

            // set active subtab memory to correctly map
            localStorage.setItem('active_assign_subtab', surveyType === 'se_umum' ? 'se2026' : 'se_ub');
            switchTab('target');

            // Give the browser a tick to render
            setTimeout(() => {
                if (document.getElementById('assign-sls-kab-filter')) {
                    document.getElementById('assign-sls-kab-filter').value = 'all';
                    window.updateGranularFilters('kab');
                }
            }, 100);
            return;
        }

        // ===== KECAMATAN FLAT LIST RENDERER =====
        function renderKecamatanFlatList() {
            // Read kabupaten filter
            const selectedKab = document.getElementById(`${surveyType}-kab-filter`)?.value || 'all';
            const isFiltered = selectedKab !== 'all';

            // Build flat list of all kecamatan from selected kabupaten
            const allKecs = [];
            surveyData.forEach(kab => {
                // Apply kabupaten filter
                if (isFiltered && kab.kabupaten !== selectedKab) return;
                (kab.kecamatan_list || []).forEach(kec => {
                    if (!kec.kec_name || kec.kec_name === '-') return;
                    // Apply search filter
                    if (searchVal && !kec.kec_name.toLowerCase().includes(searchVal) && !kab.kabupaten.toLowerCase().includes(searchVal)) return;
                    // Apply capaian filter
                    const pct = parseFloat(kec.persentase) || 0;
                    if (capaianFilterVal === 'high' && pct < 80) return;
                    if (capaianFilterVal === 'med' && (pct < 50 || pct >= 80)) return;
                    if (capaianFilterVal === 'low' && pct >= 50) return;
                    allKecs.push({ ...kec, kab_name: kab.kabupaten });
                });
            });

            // Sort by persentase desc, then total_prelist desc
            allKecs.sort((a, b) => {
                const pctA = parseFloat(a.persentase) || 0;
                const pctB = parseFloat(b.persentase) || 0;
                if (pctA !== pctB) return pctB - pctA;
                return (b.total_prelist || 0) - (a.total_prelist || 0);
            });

            // Render kecamatan-specific headers
            const table = document.querySelector(`#tab-content-${surveyType} .ipas-table`);
            const thead = table?.querySelector('thead');
            if (thead) {
                const kabCol = isFiltered ? '' : `<th rowspan="2" style="font-family:'Outfit',sans-serif; vertical-align: middle; color:var(--text-secondary); font-size:0.8rem;">Kab/Kota</th>`;
                thead.innerHTML = `
                    <tr>
                        <th rowspan="2" style="font-family:'Outfit',sans-serif; vertical-align: middle; text-align:center; min-width:45px;">#</th>
                        ${kabCol}
                        <th rowspan="2" style="font-family:'Outfit',sans-serif; vertical-align: middle;">Kecamatan</th>
                        <th rowspan="2" style="font-family:'Outfit',sans-serif;text-align:right;color:var(--text-secondary); vertical-align: middle;">Total Target</th>
                        <th rowspan="2" style="font-family:'Outfit',sans-serif;text-align:right;color:#f59e0b; vertical-align: middle;">Draft</th>
                        <th rowspan="2" style="font-family:'Outfit',sans-serif;text-align:right;color:#3b82f6; vertical-align: middle;">Open</th>
                        <th colspan="5" style="font-family:'Outfit',sans-serif;text-align:center;color:var(--color-delivered);border-bottom:1px solid var(--card-border);">Submitted (Selesai)</th>
                        <th rowspan="2" style="font-family:'Outfit',sans-serif;text-align:center; vertical-align: middle;">% Capaian</th>
                    </tr>
                    <tr>
                        <th style="font-family:'Outfit',sans-serif;text-align:right;color:var(--color-delivered);font-size:0.8rem;padding:0.4rem 0.75rem;">Total</th>
                        <th style="font-family:'Outfit',sans-serif;text-align:right;color:var(--color-opened);font-size:0.8rem;padding:0.4rem 0.75rem;">Pencacah</th>
                        <th style="font-family:'Outfit',sans-serif;text-align:right;color:#d97706;font-size:0.8rem;padding:0.4rem 0.75rem;">Respondent</th>
                        <th style="font-family:'Outfit',sans-serif;text-align:right;color:#047857;font-size:0.8rem;padding:0.4rem 0.75rem;">Approved</th>
                        <th style="font-family:'Outfit',sans-serif;text-align:right;color:#dc2626;font-size:0.8rem;padding:0.4rem 0.75rem;">Rejected</th>
                    </tr>
                `;
            }

            tbody.innerHTML = '';
            if (allKecs.length === 0) {
                const colSpan = isFiltered ? 12 : 13;
                tbody.innerHTML = `<tr><td colspan="${colSpan}" style="text-align:center;padding:3rem 1rem;color:var(--text-secondary);">Tidak ada kecamatan yang cocok dengan pencarian.</td></tr>`;
                return;
            }

            allKecs.forEach((kec, idx) => {
                const rank = idx + 1;
                const pct = parseFloat(kec.persentase) || 0;
                const pctClass = pct >= 80 ? 'background-color:rgba(16,185,129,0.1);color:#10b981;border:1px solid rgba(16,185,129,0.2);' :
                    pct >= 50 ? 'background-color:rgba(245,158,11,0.1);color:#f59e0b;border:1px solid rgba(245,158,11,0.2);' :
                        'background-color:rgba(239,68,68,0.1);color:#ef4444;border:1px solid rgba(239,68,68,0.2);';

                const medal = rank === 1 ? '🥇' : rank === 2 ? '🥈' : rank === 3 ? '🥉' : '';
                const rankDisplay = medal
                    ? `<span style="font-size:1.1rem;">${medal}</span>`
                    : `<span style="font-size:0.75rem;color:var(--text-secondary);font-weight:600;">${rank}</span>`;

                const kabCell = isFiltered ? '' : `<td style="font-size:0.78rem;color:var(--text-secondary);font-weight:600;white-space:nowrap;">${kec.kab_name.replace(/\[\d+\] /, '')}</td>`;

                const row = document.createElement('tr');
                row.innerHTML = `
                    <td style="text-align:center;padding:0.5rem 0.4rem;">${rankDisplay}</td>
                    ${kabCell}
                    <td style="font-weight:600;color:var(--text-primary);">${kec.kec_name}</td>
                    <td style="text-align:right;font-family:monospace;color:var(--text-secondary);">${formatNum(kec.total_prelist)}</td>
                    <td style="text-align:right;font-family:monospace;color:#f59e0b;">${formatNum(kec.total_draft)}</td>
                    <td style="text-align:right;font-family:monospace;color:#3b82f6;">${formatNum(kec.total_open)}</td>
                    <td style="text-align:right;font-family:monospace;font-weight:700;color:var(--color-delivered);">${formatNum(kec.total_submitted)}</td>
                    <td style="text-align:right;font-family:monospace;color:var(--color-opened);">${formatNum(kec.total_submitted_pencacah)}</td>
                    <td style="text-align:right;font-family:monospace;color:#d97706;">${formatNum(kec.total_submitted_respondent)}</td>
                    <td style="text-align:right;font-family:monospace;color:#047857;">${formatNum(kec.total_approved)}</td>
                    <td style="text-align:right;font-family:monospace;color:#dc2626;">${formatNum(kec.total_rejected)}</td>
                    <td style="text-align:center;">
                        <span style="display:inline-block;padding:0.2rem 0.5rem;border-radius:0.5rem;font-size:0.75rem;font-weight:700;${pctClass}">${pct}%</span>
                    </td>
                `;
                tbody.appendChild(row);
            });
        }

        // ===== PETUGAS FLAT LIST RENDERER =====
        function renderPetugasFlatList() {
            const allPetugas = window.PETUGAS_DATA || [];
            const hasRoles = allPetugas.some(p => p.roleName && p.roleName !== '-' && p.roleName.trim() !== '');
            const roleFilterVal = document.getElementById(`${surveyType}-role-filter`)?.value || 'all';
            const capaianFilterVal = document.getElementById(`${surveyType}-capaian-filter`)?.value || 'all';
            const slsStatusMap = window.IPAS_DATA ? (window.IPAS_DATA[surveyType + '_sls_status'] || {}) : {};

            // Render dynamic sorting indicator helper
            const getIcon = (col) => {
                const sort = window.petugasSorts[surveyType];
                if (sort.column === col) {
                    return sort.order === 'asc' ? ' ▲' : ' ▼';
                }
                return ' ⇅';
            };

            // Render petugas-specific headers with sort triggers
            const table = document.querySelector(`#tab-content-${surveyType} .ipas-table`);
            const thead = table?.querySelector('thead');
            if (thead) {
                thead.innerHTML = `
                    <tr>
                        <th class="sortable" onclick="sortPetugasTable('${surveyType}', 'petugas')" style="font-family:'Outfit',sans-serif;">Petugas${getIcon('petugas')}</th>
                        ${hasRoles ? `<th class="sortable" onclick="sortPetugasTable('${surveyType}', 'role')" style="font-family:'Outfit',sans-serif;">Role${getIcon('role')}</th>` : ''}
                        <th class="sortable" onclick="sortPetugasTable('${surveyType}', 'kabupaten')" style="font-family:'Outfit',sans-serif;">Kabupaten${getIcon('kabupaten')}</th>
                        <th class="sortable" onclick="sortPetugasTable('${surveyType}', 'jumlah_sls')" style="font-family:'Outfit',sans-serif;text-align:right;">Jumlah SLS${getIcon('jumlah_sls')}</th>
                        <th class="sortable" onclick="sortPetugasTable('${surveyType}', 'progres')" style="font-family:'Outfit',sans-serif;text-align:right;">Progres Pengerjaan${getIcon('progres')}</th>
                    </tr>
                `;
            }

            // Map and calculate progress statistics for filtering and sorting
            const petugasProcessed = allPetugas.map(officer => {
                const kabSet = new Set();
                (officer.regions || []).forEach(r => {
                    const code = r.regionCode || '';
                    if (code.length >= 4) kabSet.add(code.substring(0, 4));
                });

                // Hitung progres dari SLS yang ditugaskan
                let totalSls = (officer.regions || []).length;
                let completedSls = 0;
                let totalTarget = 0;
                let completedTarget = 0;
                (officer.regions || []).forEach(reg => {
                    const sls14 = (reg.regionCode || '').substring(0, 14);
                    const slsData = slsStatusMap[sls14] || { target: {}, nontarget: {} };
                    const targetCounts = slsData.target || {};
                    const slsTotal = Object.values(targetCounts).reduce((s, v) => s + v, 0);
                    totalTarget += slsTotal;
                    const slsDone = Object.entries(targetCounts)
                        .filter(([st]) => st !== 'OPEN' && st !== 'DRAFT')
                        .reduce((s, [, v]) => s + v, 0);
                    completedTarget += slsDone;
                    if (slsDone > 0 && slsTotal > 0) completedSls++;
                });
                const pMap = window.PETUGAS_PROGRESS_MAP || {};
                const ukey = (officer.username || '').toLowerCase().trim();
                const pData = pMap[ukey];
                
                if (pData) {
                    const mapCompleted = (pData.submitted_pencacah || 0) + (pData.submitted_respondent || 0) + (pData.approved || 0);
                    if (mapCompleted > completedTarget) {
                        totalTarget = Math.max(totalTarget, pData.target || 0);
                        completedTarget = mapCompleted;
                    }
                }

                const progPct = totalTarget > 0 ? Math.min(100, Math.round((completedTarget / totalTarget) * 100)) : 0;

                const kabCodes = [...kabSet];
                const kabLabels = kabCodes.map(code => {
                    const found = (window.IPAS_DATA?.[surveyType] || []).find(k => {
                        const match = k.kabupaten.match(/\[(\d+)\]/);
                        return match && ('72' + match[1]) === code;
                    });
                    return found ? found.kabupaten.replace(/\[\d+\] /, '') : code;
                }).join(', ');

                return {
                    ...officer,
                    kabLabels,
                    totalSls,
                    completedSls,
                    totalTarget,
                    completedTarget,
                    progPct
                };
            });

            // Filter petugas array
            const petugasFiltered = petugasProcessed.filter(p => {
                // Search filter
                if (searchVal) {
                    const searchLower = searchVal.toLowerCase();
                    const matchSearch = (p.username || '').toLowerCase().includes(searchLower) ||
                        (p.email || '').toLowerCase().includes(searchLower) ||
                        (p.roleName || '').toLowerCase().includes(searchLower) ||
                        (p.kabLabels || '').toLowerCase().includes(searchLower);
                    if (!matchSearch) return false;
                }

                // Role filter
                if (roleFilterVal !== 'all' && p.roleName !== roleFilterVal) return false;

                // Capaian filter
                if (capaianFilterVal === 'high' && p.progPct < 80) return false;
                if (capaianFilterVal === 'med' && (p.progPct < 50 || p.progPct >= 80)) return false;
                if (capaianFilterVal === 'low' && p.progPct >= 50) return false;

                return true;
            });

            tbody.innerHTML = '';
            if (petugasFiltered.length === 0) {
                tbody.innerHTML = `<tr><td colspan="${hasRoles ? 5 : 4}" style="text-align:center;padding:3rem 1rem;color:var(--text-secondary);">Tidak ada petugas yang cocok dengan pencarian / filter.</td></tr>`;
                return;
            }

            // Sort filtered petugas array
            const pSort = window.petugasSorts[surveyType];
            petugasFiltered.sort((a, b) => {
                let valA, valB;
                if (pSort.column === 'petugas') {
                    valA = a.username || a.email || '';
                    valB = b.username || b.email || '';
                    return pSort.order === 'asc' ? valA.localeCompare(valB) : valB.localeCompare(valA);
                } else if (pSort.column === 'role') {
                    valA = a.roleName || '';
                    valB = b.roleName || '';
                    return pSort.order === 'asc' ? valA.localeCompare(valB) : valB.localeCompare(valA);
                } else if (pSort.column === 'kabupaten') {
                    valA = a.kabLabels || '';
                    valB = b.kabLabels || '';
                    return pSort.order === 'asc' ? valA.localeCompare(valB) : valB.localeCompare(valA);
                } else if (pSort.column === 'jumlah_sls') {
                    valA = a.totalSls || 0;
                    valB = b.totalSls || 0;
                    return pSort.order === 'asc' ? valA - valB : valB - valA;
                } else if (pSort.column === 'progres') {
                    valA = a.progPct || 0;
                    valB = b.progPct || 0;
                    if (valA !== valB) {
                        return pSort.order === 'asc' ? valA - valB : valB - valA;
                    }
                    valA = a.totalTarget || 0;
                    valB = b.totalTarget || 0;
                    return pSort.order === 'asc' ? valA - valB : valB - valA;
                }
                return 0;
            });

            petugasFiltered.forEach(officer => {
                const progPct = officer.progPct;
                const progColor = progPct >= 80 ? '#10b981' : progPct >= 50 ? '#f59e0b' : '#ef4444';
                const progBarStyle = `height:6px;border-radius:3px;background:rgba(255,255,255,0.1);overflow:hidden;margin-top:4px;`;
                const progFillStyle = `height:100%;border-radius:3px;background:${progColor};width:${progPct}%;transition:width 0.5s;`;
                const progHTML = `
                    <div style="display:flex;flex-direction:column;align-items:flex-end;gap:2px;">
                        <span style="font-size:0.75rem;font-weight:700;color:${progColor};">${officer.completedTarget}/${officer.totalTarget} (${progPct}%)</span>
                        <div style="${progBarStyle}width:100px;"><div style="${progFillStyle}"></div></div>
                        <span style="font-size:0.65rem;color:var(--text-muted);">${officer.completedSls}/${officer.totalSls} SLS selesai</span>
                    </div>`;

                const roleBgColor = officer.roleName === 'Pencacah' ? 'rgba(99,102,241,0.15)' : 'rgba(245,158,11,0.15)';
                const roleTextColor = officer.roleName === 'Pencacah' ? 'var(--primary)' : '#f59e0b';

                const row = document.createElement('tr');
                row.innerHTML = `
                    <td style="font-weight:600;color:var(--text-primary);">
                        ${(window.userMap && window.userMap[officer.username || (officer.email || '').split('@')[0]]) || officer.username || officer.email || '-'}
                        <div style="font-size:0.7rem;color:var(--text-muted);">${officer.email || officer.username || ''}</div>
                    </td>
                    ${hasRoles ? `<td><span style="font-size:0.75rem;padding:0.15rem 0.5rem;border-radius:0.35rem;background:${roleBgColor};color:${roleTextColor};font-weight:700;">${officer.roleName || '-'}</span></td>` : ''}
                    <td style="font-size:0.8rem;color:var(--text-secondary);">${officer.kabLabels || '-'}</td>
                    <td style="text-align:right;font-family:monospace;color:var(--text-secondary);">${formatNum(officer.totalSls)}</td>
                    <td style="text-align:right;">${progHTML}</td>
                `;
                tbody.appendChild(row);
            });
        }

        // Render dynamic sorting headers (only for kabupaten view)
        window.renderSeTableHeaders(surveyType);

        if (filtered.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="12" style="text-align: center; padding: 3rem 1rem; color: var(--text-secondary);">
                        <svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" style="margin: 0 auto 0.5rem; opacity: 0.5;">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 13.5h3.86a2.25 2.25 0 012.008 1.24l.885 1.77a2.25 2.25 0 002.007 1.24h1.98a2.25 2.25 0 002.007-1.24l.885-1.77a2.25 2.25 0 012.007-1.24h3.86m-18 0h18"></path>
                        </svg>
                        Tidak ada data kabupaten yang cocok dengan pencarian.
                    </td>
                </tr>
            `;
            return;
        }

        // Sort filtered array according to current settings
        const sortSettings = window.seSorts[surveyType];
        filtered.sort((a, b) => {
            let valA, valB;
            switch (sortSettings.column) {
                case 'kabupaten':
                    valA = a.kabupaten || '';
                    valB = b.kabupaten || '';
                    return sortSettings.order === 'asc' ? valA.localeCompare(valB) : valB.localeCompare(valA);
                case 'total_prelist':
                    valA = a.total_prelist || 0;
                    valB = b.total_prelist || 0;
                    break;
                case 'total_draft':
                    valA = a.total_draft || 0;
                    valB = b.total_draft || 0;
                    break;
                case 'total_open':
                    valA = a.total_open || 0;
                    valB = b.total_open || 0;
                    break;
                case 'total_submitted':
                    valA = a.total_submitted || 0;
                    valB = b.total_submitted || 0;
                    break;
                case 'persentase':
                    valA = parseFloat(a.persentase) || 0;
                    valB = parseFloat(b.persentase) || 0;
                    break;
                case 'delta_persen':
                    valA = parseFloat(a.delta_persen) || 0;
                    valB = parseFloat(b.delta_persen) || 0;
                    break;
                case 'sisa_usaha':
                    valA = a.sisa_usaha || 0;
                    valB = b.sisa_usaha || 0;
                    break;
                case 'today_completed':
                    valA = a.today_completed || 0;
                    valB = b.today_completed || 0;
                    break;
                case 'yesterday_completed':
                    valA = a.yesterday_completed || 0;
                    valB = b.yesterday_completed || 0;
                    break;
                case 'two_days_ago_completed':
                    valA = a.two_days_ago_completed || 0;
                    valB = b.two_days_ago_completed || 0;
                    break;
                case 'new_usaha_overall':
                    valA = a.new_usaha_overall || 0;
                    valB = b.new_usaha_overall || 0;
                    break;
                case 'new_rumah_overall':
                    valA = a.new_rumah_overall || 0;
                    valB = b.new_rumah_overall || 0;
                    break;
                case 'new_usaha_today':
                    valA = a.new_usaha_today || 0;
                    valB = b.new_usaha_today || 0;
                    break;
                default:
                    return 0;
            }
            return sortSettings.order === 'asc' ? valA - valB : valB - valA;
        });

        if (!window.expandedSeKabs) {
            window.expandedSeKabs = { se_umum: {}, se_ub: {} };
        }

        filtered.forEach(item => {
            let pctClass = '';
            if (item.persentase >= 80) {
                pctClass = 'background-color: rgba(16, 185, 129, 0.1); color: var(--color-delivered); border: 1px solid rgba(16, 185, 129, 0.3);';
            } else if (item.persentase >= 50) {
                pctClass = 'background-color: rgba(245, 158, 11, 0.1); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.3);';
            } else {
                pctClass = 'background-color: rgba(239, 68, 68, 0.1); color: var(--color-bounced); border: 1px solid rgba(239, 68, 68, 0.3);';
            }

            const row = document.createElement('tr');
            const isExpanded = window.expandedSeKabs[surveyType][item.kabupaten] || false;
            row.className = 'kabupaten-row' + (isExpanded ? ' expanded' : '');

            const kabupatenEscaped = item.kabupaten.replace(/'/g, "\\'");
            const encodedBusinessesJSON = encodeURIComponent(JSON.stringify(item.new_businesses || []));

            const penambahanBadge = `<div onclick="openNewBusinessesModal('${kabupatenEscaped}', '${encodedBusinessesJSON}', 'all')" style="cursor: pointer; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 0.1rem;" onmouseover="this.style.opacity='0.8';" onmouseout="this.style.opacity='1';">
                    <span style="font-weight: 800; color: var(--primary); font-size: 0.95rem;">${formatNum(item.new_usaha_overall + item.new_rumah_overall)}</span>
                    <span style="font-size: 0.65rem; font-weight: 600; color: var(--text-secondary);">${item.new_usaha_overall} usaha | ${item.new_rumah_overall} rumah</span>
                    <span style="font-size: 0.6rem; color: var(--text-muted);">+${item.new_usaha_today + item.new_rumah_today} hari ini</span>
                </div>`;

            row.innerHTML = `
                <td style="font-weight: 700; color: var(--text-primary);">
                    <div class="expand-trigger" style="display: inline-flex; align-items: center; gap: 0.5rem; width: 100%;">
                        <span class="expand-chevron" style="transition: transform 0.2s; display: inline-block; ${isExpanded ? 'transform: rotate(90deg);' : ''}">▶</span>
                        ${highlightText(item.kabupaten, searchVal)}
                    </div>
                </td>
                <td style="text-align: right; font-family: monospace; font-weight: 500; color: var(--text-secondary);">${formatNum(item.total_prelist)}</td>
                <td style="text-align: right; font-family: monospace; font-weight: 500; color: #f59e0b;">${formatNum(item.total_draft)}</td>
                <td style="text-align: right; font-family: monospace; font-weight: 500; color: #3b82f6;">${formatNum(item.total_open)}</td>
                
                <td style="text-align: right; font-family: monospace; font-weight: 700; color: var(--color-delivered);">${formatNum(item.total_submitted)}</td>
                <td style="text-align: right; font-family: monospace; color: var(--color-opened);">${formatNum(item.total_submitted_pencacah)}</td>
                <td style="text-align: right; font-family: monospace; color: #d97706;">${formatNum(item.total_submitted_respondent)}</td>
                <td style="text-align: right; font-family: monospace; color: #047857;">${formatNum(item.total_approved)}</td>
                <td style="text-align: right; font-family: monospace; color: #dc2626;">${formatNum(item.total_rejected)}</td>
                
                <td style="text-align: center;">
                    <span style="display: inline-block; padding: 0.25rem 0.5rem; border-radius: 0.5rem; font-size: 0.75rem; font-weight: 800; ${pctClass}">
                        ${item.persentase}%
                    </span>
                </td>
                <td style="text-align: center;">
                    ${item.delta_persen !== undefined && item.delta_persen !== 0 ? 
                        `<span style="font-size: 0.8rem; font-weight: 800; color: ${item.delta_persen > 0 ? '#22c55e' : (item.delta_persen < 0 ? '#ef4444' : 'inherit')};">
                            ${item.delta_persen > 0 ? '+' : ''}${item.delta_persen.toFixed(2)}%
                        </span>` 
                        : `<span style="font-size: 0.8rem; color: var(--text-muted);">-</span>`}
                </td>
                <td style="text-align: center;">
                    ${penambahanBadge}
                </td>
            `;
            tbody.appendChild(row);

            // Click listener khusus untuk expand-trigger
            const trigger = row.querySelector('.expand-trigger');
            if (trigger) {
                trigger.addEventListener('click', (e) => {
                    e.stopPropagation();
                    window.expandedSeKabs[surveyType][item.kabupaten] = !isExpanded;
                    window.renderSeDashboard(surveyType);
                });
            }

            // Render expanded Kecamatan sub-rows
            if (isExpanded && item.kecamatan_list) {
                // Build kab code lookup map from ASSIGN_DATA
                let kabCode = '';
                if (window.ASSIGN_DATA) {
                    const kabMatch = window.ASSIGN_DATA.find(d => d.nama_kab === item.kabupaten);
                    if (kabMatch) kabCode = kabMatch.kode_kab;
                }

                // Build petugas-per-kec lookup from PETUGAS_DATA (match by SLS code prefix)
                const petugasByKecCode = {}; // kec_code_7digit -> [officers]
                const slsToPetugasMap = {}; // slsCode -> officer info
                if (window.PETUGAS_DATA && kabCode) {
                    // Build SLS to officer map for this kab
                    window.PETUGAS_DATA.forEach(officer => {
                        if (!officer.regions || officer.regions.length === 0) return;
                        officer.regions.forEach(reg => {
                            const code = reg.regionCode || '';
                            if (code.startsWith(kabCode)) {
                                const slsKey = code.length === 16 ? code.substring(0, 14) : code;
                                const kecCode = code.substring(0, 7);
                                if (!petugasByKecCode[kecCode]) petugasByKecCode[kecCode] = [];
                                // Avoid duplicating the same officer in a kec
                                if (!petugasByKecCode[kecCode].some(o => o.userId === officer.userId)) {
                                    petugasByKecCode[kecCode].push(officer);
                                }
                            }
                        });
                    });
                }

                // Build kec name → kec code map from survey-type-specific SLS data
                const kecNameToCode = {};
                const assignSlsForKec = surveyType === 'se_umum' ? window.ASSIGN_SLS_DATA_UMUM : window.ASSIGN_SLS_DATA_UB;
                if (assignSlsForKec && kabCode) {
                    assignSlsForKec.forEach(sls => {
                        const code = sls.sls_code || sls.sls_id || '';
                        if (code.startsWith(kabCode) && sls.kec_name) {
                            const kecCode = code.substring(0, 7);
                            kecNameToCode[sls.kec_name.toUpperCase()] = kecCode;
                        }
                    });
                }

                const kabMatch = item.kabupaten.toLowerCase().includes(searchVal);
                item.kecamatan_list.forEach(kec => {
                    const kecMatch = kec.kec_name.toLowerCase().includes(searchVal);
                    if (searchVal !== "" && !kabMatch && !kecMatch) {
                        return; // Skip rendering if not matching search query
                    }
                    let kPctClass = '';
                    if (kec.persentase >= 80) {
                        kPctClass = 'background-color: rgba(16, 185, 129, 0.1); color: var(--color-delivered); border: 1px solid rgba(16, 185, 129, 0.3);';
                    } else if (kec.persentase >= 50) {
                        kPctClass = 'background-color: rgba(245, 158, 11, 0.1); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.3);';
                    } else {
                        kPctClass = 'background-color: rgba(239, 68, 68, 0.1); color: var(--color-bounced); border: 1px solid rgba(239, 68, 68, 0.3);';
                    }

                    const kecRow = document.createElement('tr');
                    kecRow.className = 'kecamatan-row';

                    const kecToday = getDailyProgressCellHTML(kec.today_completed, kec.today_completed_breakdown, 'HARI INI: KEC. ' + kec.kec_name);
                    const kecYesterday = getDailyProgressCellHTML(kec.yesterday_completed, kec.yesterday_completed_breakdown, 'KEMARIN: KEC. ' + kec.kec_name);
                    const kecTwoDays = getDailyProgressCellHTML(kec.two_days_ago_completed, kec.two_days_ago_completed_breakdown, 'H-2: KEC. ' + kec.kec_name);

                    const kecEscaped = (item.kabupaten.replace(/\[\d+\] /, '') + ' - ' + kec.kec_name).replace(/'/g, "\\'");
                    const encodedKecBusinessesJSON = encodeURIComponent(JSON.stringify(kec.new_businesses || []));

                    const overall_total = (kec.new_usaha_overall || 0) + (kec.new_rumah_overall || 0);
                    const overall_usaha = kec.new_usaha_overall || 0;
                    const overall_rumah = kec.new_rumah_overall || 0;
                    const today_total = (kec.new_usaha_today || 0) + (kec.new_rumah_today || 0);
                    const kecPenambahanBadge = `<div onclick="openNewBusinessesModal('${kecEscaped}', '${encodedKecBusinessesJSON}', 'all')" style="cursor: pointer; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 0.1rem;" onmouseover="this.style.opacity='0.8';" onmouseout="this.style.opacity='1';">
                            <span style="font-weight: 800; color: var(--primary); font-size: 0.85rem;">${formatNum(overall_total)}</span>
                            <span style="font-size: 0.65rem; font-weight: 600; color: var(--text-secondary);">${overall_usaha} usaha | ${overall_rumah} rumah</span>
                            <span style="font-size: 0.6rem; color: var(--text-muted);">+${today_total} hari ini</span>
                        </div>`;

                    kecRow.innerHTML = `
                        <td style="font-weight: 600;">↳ ${highlightText(kec.kec_name, searchVal)}</td>
                        <td style="text-align: right; font-family: monospace; font-weight: 500; color: var(--text-secondary);">${formatNum(kec.total_prelist)}</td>
                        <td style="text-align: right; font-family: monospace; font-weight: 500; color: #f59e0b;">${formatNum(kec.total_draft)}</td>
                        <td style="text-align: right; font-family: monospace; font-weight: 500; color: #3b82f6;">${formatNum(kec.total_open)}</td>
                        
                        <td style="text-align: right; font-family: monospace; font-weight: 700; color: var(--color-delivered);">${formatNum(kec.total_submitted)}</td>
                        <td style="text-align: right; font-family: monospace; color: var(--color-opened);">${formatNum(kec.total_submitted_pencacah)}</td>
                        <td style="text-align: right; font-family: monospace; color: #d97706;">${formatNum(kec.total_submitted_respondent)}</td>
                        <td style="text-align: right; font-family: monospace; color: #047857;">${formatNum(kec.total_approved)}</td>
                        <td style="text-align: right; font-family: monospace; color: #dc2626;">${formatNum(kec.total_rejected)}</td>
                        
                        <td style="text-align: center;">
                            <span style="display: inline-block; padding: 0.2rem 0.4rem; border-radius: 0.4rem; font-size: 0.7rem; font-weight: 800; ${kPctClass}">
                                ${kec.persentase}%
                            </span>
                        </td>
                        <td style="text-align: center;">
                            ${kecPenambahanBadge}
                        </td>
                    `;
                    tbody.appendChild(kecRow);

                    // Petugas sub-rows removed from this view — see tab Petugas for detail per petugas
                });
            }
        });

        // Calculate province totals for new businesses if not already summed
        let newYesterday = 0;
        let newRumahYesterday = 0;
        surveyData.forEach(item => {
            newYesterday += item.new_usaha_yesterday || 0;
            newRumahYesterday += item.new_rumah_yesterday || 0;
        });

        // Add PROVINSI SULAWESI TENGAH row
        const provRow = document.createElement('tr');
        provRow.style.fontWeight = 'bold';
        provRow.style.backgroundColor = 'rgba(99, 102, 241, 0.08)';
        provRow.style.borderTop = '2px solid var(--card-border)';
        provRow.style.borderBottom = '2px solid var(--card-border)';

        let provPctClass = '';
        if (persentase >= 80) {
            provPctClass = 'background-color: rgba(16, 185, 129, 0.2); color: var(--color-delivered); border: 1px solid rgba(16, 185, 129, 0.4);';
        } else if (persentase >= 50) {
            provPctClass = 'background-color: rgba(245, 158, 11, 0.2); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.4);';
        } else {
            provPctClass = 'background-color: rgba(239, 68, 68, 0.2); color: var(--color-bounced); border: 1px solid rgba(239, 68, 68, 0.4);';
        }

        const provPenambahanBadge = `<div onclick="openProvincialNewBusinessesModal('${surveyType}', 'all')" style="cursor: pointer; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 0.1rem;" onmouseover="this.style.opacity='0.8';" onmouseout="this.style.opacity='1';">
                <span style="font-weight: 800; color: var(--primary); font-size: 0.95rem;">${formatNum(newOverall + newRumahOverall)}</span>
                <span style="font-size: 0.65rem; font-weight: 600; color: var(--text-secondary);">${formatNum(newOverall)} usaha | ${formatNum(newRumahOverall)} rumah</span>
                <span style="font-size: 0.65rem; font-weight: 600; color: var(--text-muted);">+${newToday + newRumahToday} hari ini | +${newYesterday + newRumahYesterday} kmrn</span>
            </div>`;

        const provTodayHTML = getDailyProgressCellHTML(today, todayBreakdown, 'HARI INI: SULAWESI TENGAH');
        const provYesterdayHTML = getDailyProgressCellHTML(yesterday, yesterdayBreakdown, 'KEMARIN: SULAWESI TENGAH');
        const provTwoDaysHTML = getDailyProgressCellHTML(twoDaysAgo, twoDaysAgoBreakdown, 'H-2: SULAWESI TENGAH');

        provRow.innerHTML = `
            <td style="font-weight: 800; color: var(--text-primary); position: sticky; left: 0; background-color: var(--tfoot-sticky-bg); z-index: 25; border-bottom: 2px solid var(--card-border);">[72] SULAWESI TENGAH</td>
            <td style="text-align: right; font-family: monospace; font-weight: 700; color: var(--text-secondary); border-bottom: 2px solid var(--card-border);">${formatNum(prelist)}</td>
            <td style="text-align: right; font-family: monospace; font-weight: 700; color: #f59e0b; border-bottom: 2px solid var(--card-border);">${formatNum(draft)}</td>
            <td style="text-align: right; font-family: monospace; font-weight: 700; color: #3b82f6; border-bottom: 2px solid var(--card-border);">${formatNum(openVal)}</td>
            
            <td style="text-align: right; font-family: monospace; font-weight: 800; color: var(--color-delivered); border-bottom: 2px solid var(--card-border);">${formatNum(submitted)}</td>
            <td style="text-align: right; font-family: monospace; border-bottom: 2px solid var(--card-border);">${provTodayHTML}</td>
            <td style="text-align: right; font-family: monospace; border-bottom: 2px solid var(--card-border);">${provYesterdayHTML}</td>
            <td style="text-align: right; font-family: monospace; border-bottom: 2px solid var(--card-border);">${provTwoDaysHTML}</td>
            
            <td style="text-align: center; border-bottom: 2px solid var(--card-border);">
                <span style="display: inline-block; padding: 0.25rem 0.5rem; border-radius: 0.5rem; font-size: 0.75rem; font-weight: 800; ${provPctClass}">
                    ${persentase}%
                </span>
            </td>
            <td style="text-align: center; border-bottom: 2px solid var(--card-border);">
                ${provPenambahanBadge}
            </td>
        `;
        
        const table = tbody.closest('.ipas-table');
        if (table) {
            let tfoot = table.querySelector('tfoot');
            if (!tfoot) {
                tfoot = document.createElement('tfoot');
                tfoot.style.position = 'sticky';
                tfoot.style.bottom = '0';
                tfoot.style.zIndex = '20';
                tfoot.style.background = 'var(--card-bg)';
                tfoot.style.boxShadow = '0 -2px 10px rgba(0,0,0,0.05)';
                table.appendChild(tfoot);
            }
            tfoot.innerHTML = '';
            tfoot.appendChild(provRow);
            
            // Ensure table wrapper has enough padding so badge isn't cut off
            const wrapper = table.closest('.ipas-table-wrapper');
            if (wrapper) {
                wrapper.style.paddingBottom = '10px';
            }
        } else {
            tbody.appendChild(provRow);
        }

        // Render Chart
        if (!window.currentChartType) window.currentChartType = { se_umum: 'bar', se_ub: 'bar' };

        window.toggleChartType = function (type) {
            const current = window.currentChartType[type] || 'bar';
            let next = 'line';
            if (current === 'bar') {
                next = 'line';
            } else {
                next = 'bar';
            }
            window.currentChartType[type] = next;
            window.renderSeDashboard(type);
        };

        const ctx = document.getElementById(`${surveyType}-chart`);
        if (ctx) {
            if (!window.seCharts) window.seCharts = {};
            if (window.seCharts[surveyType]) {
                window.seCharts[surveyType].destroy();
            }

            const cType = window.currentChartType[surveyType];
            let chartData = {};
            let chartOptions = {};

            if (cType === 'line' || cType === 'line_daily') {
                const _t = new Date();
                const _y = new Date(_t); _y.setDate(_y.getDate() - 1);
                const _h2 = new Date(_t); _h2.setDate(_h2.getDate() - 2);
                const _fmt = d => String(d.getDate()).padStart(2, '0') + '/' + String(d.getMonth() + 1).padStart(2, '0');
                let labels = [`H-2 (${_fmt(_h2)})`, `Kemarin (${_fmt(_y)})`, `Hari Ini (${_fmt(_t)})`];
                let dataPoints = (cType === 'line')
                    ? [submitted - today - yesterday, submitted - today, submitted]
                    : [twoDaysAgo, yesterday, today];

                const stats = window.DAILY_SUBMISSION_STATS;
                if (stats && Array.isArray(stats) && stats.length > 0) {
                    const filtered = stats.filter(r => r.survey_type === surveyType);
                    const rawDateMap = {};
                    filtered.forEach(r => {
                        const d = r.date;
                        if (d) {
                            rawDateMap[d] = (rawDateMap[d] || 0) + (r.count || 0);
                        }
                    });

                    // Compute WITA date strings for the most recent 3 days
                    const getWitaDateStr = (offsetDays = 0) => {
                        let d = new Date();
                        if (ipasDataObj && ipasDataObj.updated_at) {
                            d = new Date(ipasDataObj.updated_at);
                        }
                        if (offsetDays !== 0) d.setDate(d.getDate() + offsetDays);
                        const utc = d.getTime() + (d.getTimezoneOffset() * 60000);
                        const wita = new Date(utc + (3600000 * 8));
                        return `${wita.getFullYear()}-${String(wita.getMonth() + 1).padStart(2, '0')}-${String(wita.getDate()).padStart(2, '0')}`;
                    };
                    const todayDateStr = getWitaDateStr(0);
                    const yesterdayDateStr = getWitaDateStr(-1);
                    const twoDaysDateStr = getWitaDateStr(-2);
                    const recentDates = new Set([todayDateStr, yesterdayDateStr, twoDaysDateStr]);

                    // Build normalized dateMap:
                    // - Recent 3 days: use real KPI values (from generate_ipas_report.py)
                    // - Older days: scale proportionally so they sum to (submitted - recent 3 days total)
                    const recentTotal = today + yesterday + twoDaysAgo;
                    const historicalTarget = Math.max(0, submitted - recentTotal);

                    let olderSum = 0;
                    const olderDates = [];
                    for (const [d, cnt] of Object.entries(rawDateMap)) {
                        if (!recentDates.has(d)) {
                            olderSum += cnt;
                            olderDates.push(d);
                        }
                    }

                    const dateMap = {};
                    // Scale older days
                    const olderScale = (olderSum > 0 && historicalTarget > 0) ? (historicalTarget / olderSum) : 0;
                    for (const d of olderDates) {
                        dateMap[d] = Math.round((rawDateMap[d] || 0) * olderScale);
                    }
                    // Set recent days with real values
                    if (today > 0) dateMap[todayDateStr] = today;
                    if (yesterday > 0) dateMap[yesterdayDateStr] = yesterday;
                    if (twoDaysAgo > 0) dateMap[twoDaysDateStr] = twoDaysAgo;

                    const sortedDates = Object.keys(dateMap).sort();
                    if (sortedDates.length > 0) {
                        const cumData = new Array(sortedDates.length);
                        let runningTotal = submitted;
                        cumData[sortedDates.length - 1] = runningTotal;

                        for (let i = sortedDates.length - 1; i > 0; i--) {
                            const date = sortedDates[i];
                            const change = dateMap[date] || 0;
                            runningTotal = Math.max(0, runningTotal - change);
                            cumData[i - 1] = runningTotal;
                        }

                        // Filter starting from June 15 ('2026-06-15')
                        const startIndex = sortedDates.findIndex(d => d >= '2026-06-15');
                        let finalDates = sortedDates;
                        let finalDataPoints = (cType === 'line') ? cumData : sortedDates.map(d => dateMap[d] || 0);
                        if (startIndex !== -1) {
                            finalDates = sortedDates.slice(startIndex);
                            finalDataPoints = finalDataPoints.slice(startIndex);
                        }

                        labels = finalDates.map(d => {
                            try {
                                const parts = d.split('-');
                                if (parts.length === 3) return `${parts[2]}/${parts[1]}`;
                            } catch (e) { }
                            return d;
                        });
                        dataPoints = finalDataPoints;
                    }
                }

                // Adjust wrapper width dynamically for line charts
                const wrapper = ctx.parentElement;
                if (wrapper) {
                    const parentWidth = wrapper.parentElement.clientWidth || 400;
                    // Use smaller dayWidth so bars are denser/dempet - each day takes ~1/7 of visible width
                    const dayWidth = Math.max(40, parentWidth / 7);
                    const computedWidth = Math.max(parentWidth, labels.length * dayWidth);
                    wrapper.style.width = computedWidth + 'px';

                    // Scroll to the far right to show most recent days
                    setTimeout(() => {
                        if (wrapper.parentElement) {
                            wrapper.parentElement.scrollLeft = wrapper.parentElement.scrollWidth;
                        }
                    }, 50);
                }

                chartData = {
                    labels: labels,
                    datasets: [{
                        label: cType === 'line' ? 'Total Capaian Selesai (Kumulatif)' : 'Progres Submit Per Hari',
                        data: dataPoints,
                        borderColor: cType === 'line' ? '#3b82f6' : '#10b981',
                        backgroundColor: cType === 'line' ? 'rgba(59, 130, 246, 0.2)' : 'rgba(16, 185, 129, 0.2)',
                        borderWidth: 3,
                        pointBackgroundColor: '#0b1120',
                        pointBorderColor: cType === 'line' ? '#3b82f6' : '#10b981',
                        pointBorderWidth: 2,
                        pointRadius: labels.length > 10 ? 3 : 6,
                        pointHoverRadius: labels.length > 10 ? 5 : 8,
                        fill: true,
                        tension: 0.4
                    }]
                };
                const textColor = getThemeColor('--text-secondary', '#64748b');
                const gridColor = getThemeColor('--card-border', '#e2e8f0');
                chartOptions = {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { labels: { color: textColor, font: { family: "'Outfit', sans-serif" } } }
                    },
                    scales: {
                        y: { grid: { color: gridColor }, ticks: { color: textColor } },
                        x: { grid: { display: false }, ticks: { color: textColor } }
                    }
                };
            } else {
                // Bar Chart Per Kabupaten (Stacked/Overlapping where Green is on top)
                const wrapper = ctx.parentElement;
                if (wrapper) {
                    wrapper.style.width = '100%';
                }

                const sortedForBar = [...surveyData].sort((a, b) => b.total_prelist - a.total_prelist);
                chartData = {
                    labels: sortedForBar.map(i => i.kabupaten.replace(/\[\d+\] /g, '')),
                    datasets: [
                        {
                            label: 'Approved',
                            data: sortedForBar.map(i => i.total_approved || 0),
                            backgroundColor: '#047857', // Green
                            borderRadius: 4,
                            order: 1
                        },
                        {
                            label: 'Submitted Respondent',
                            data: sortedForBar.map(i => i.total_submitted_respondent || 0),
                            backgroundColor: '#d97706', // Orange
                            borderRadius: 4,
                            order: 2
                        },
                        {
                            label: 'Submitted Pencacah',
                            data: sortedForBar.map(i => i.total_submitted_pencacah || 0),
                            backgroundColor: '#10b981', // Teal/Light Green
                            borderRadius: 4,
                            order: 3
                        },
                        {
                            label: 'Rejected',
                            data: sortedForBar.map(i => i.total_rejected || 0),
                            backgroundColor: '#ef4444', // Red
                            borderRadius: 4,
                            order: 4
                        },
                        {
                            label: 'Draft',
                            data: sortedForBar.map(i => i.total_draft || 0),
                            backgroundColor: '#f59e0b', // Yellow/Orange
                            borderRadius: 4,
                            order: 5
                        },
                        {
                            label: 'Open',
                            data: sortedForBar.map(i => i.total_open || 0),
                            backgroundColor: '#3b82f6', // Blue
                            borderRadius: 4,
                            order: 6
                        }
                    ]
                };
                const textColor = getThemeColor('--text-secondary', '#64748b');
                const gridColor = getThemeColor('--card-border', '#e2e8f0');
                chartOptions = {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top',
                            labels: { color: textColor, font: { family: "'Outfit', sans-serif" } }
                        }
                    },
                    scales: {
                        y: {
                            stacked: true,
                            grid: { color: gridColor },
                            ticks: { color: textColor }
                        },
                        x: {
                            stacked: true,
                            grid: { display: false },
                            ticks: {
                                color: textColor,
                                maxRotation: 45,
                                minRotation: 45
                            }
                        }
                    }
                };
            }

            window.seCharts[surveyType] = new Chart(ctx.getContext('2d'), {
                type: (cType === 'line' || cType === 'line_daily') ? 'line' : 'bar',
                data: chartData,
                options: chartOptions
            });
        }
        
        if (surveyType === 'se_umum') {

        }
    };

    // Grafik tren harian telah dihapus sesuai permintaan user.

    // Helpers for dynamic loading last updated status
    let isSupabaseUsedGlobal = false;
    let lastUpdatedEmailTextGlobal = '';

    // Render tabel ringkasan per kabupaten
    function renderKabSummaryTable() {
        const tbody = document.getElementById('kab-summary-tbody');
        if (!tbody) return;

        if (!window.ASSIGN_DATA || window.ASSIGN_DATA.length === 0) {
            tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; padding: 2rem; color: var(--text-secondary);">Data alokasi belum tersedia. Silakan jalankan scrape_assign.py terlebih dahulu.</td></tr>`;
            return;
        }

        const fmt = (n) => new Intl.NumberFormat('id-ID').format(n || 0);
        const rowStyle = 'border-bottom: 1px solid var(--card-border); transition: background-color 0.15s;';
        const tdBase = 'padding: 0.65rem 1.25rem; vertical-align: middle;';

        // Aggregate SLS stats per kabupaten for %assign and %sync
        const slsStatsByKab = {};
        window.ASSIGN_DATA.forEach(d => {
            slsStatsByKab[d.kode_kab] = { total: 0, assigned: 0, synced: 0, synced_targets: 0 };
        });
        if (window.ASSIGN_SLS_DATA && window.ASSIGN_SLS_DATA.length > 0) {
            window.ASSIGN_SLS_DATA.forEach(sls => {
                // Assignment tab (Tab 2) shows ALL data including dummy entries
                const code = sls.sls_code || sls.sls_id;
                const kodeKab = code ? code.substring(0, 4) : '';
                if (kodeKab && slsStatsByKab[kodeKab]) {
                    slsStatsByKab[kodeKab].total++;
                    if ((sls.assigned || 0) > 0) slsStatsByKab[kodeKab].assigned++;
                    if ((sls.sync_count || 0) > 0) slsStatsByKab[kodeKab].synced++;
                    slsStatsByKab[kodeKab].synced_targets += (sls.sync_count || 0);
                }
            });
        } else if (window.SUPERSET_SYNC_SLS_DATA && window.SUPERSET_SYNC_SLS_DATA.length > 0) {
            window.SUPERSET_SYNC_SLS_DATA.forEach(sls => {
                // Assignment tab shows all entries
                const code = sls.sls_code || sls.sls_id;
                const kodeKab = code ? code.substring(0, 4) : '';
                if (kodeKab && slsStatsByKab[kodeKab]) {
                    slsStatsByKab[kodeKab].total++;
                    slsStatsByKab[kodeKab].assigned++;
                    if ((sls.sync_count || 0) > 0) slsStatsByKab[kodeKab].synced++;
                    slsStatsByKab[kodeKab].synced_targets += (sls.sync_count || 0);
                }
            });
        }

        let totalUsaha = 0;
        let totalSudah = 0;
        let totalBelum = 0;
        let totalBelumSync = 0;
        let totalSlsAssigned = 0;
        let totalSlsTotal = 0;
        let totalSlsSynced = 0;

        const rowsHtml = window.ASSIGN_DATA.map((d, idx) => {
            const total = d.total || 0;
            const assigned = d.assigned || 0;
            const unassigned = d.have_not_assigned || 0;

            const slsStats = slsStatsByKab[d.kode_kab] || { total: 0, assigned: 0, synced: 0, synced_targets: 0 };
            const syncedTargetsVal = slsStats.synced_targets || 0;
            const belumSyncVal = Math.max(0, assigned - syncedTargetsVal);

            totalUsaha += total;
            totalSudah += assigned;
            totalBelum += unassigned;
            totalBelumSync += belumSyncVal;

            totalSlsTotal += slsStats.total;
            totalSlsAssigned += slsStats.assigned;
            totalSlsSynced += slsStats.synced;

            const pctAssignText = floorPct(assigned, total);
            const pct = parseFloat(pctAssignText);

            const pctSlsAssignText = floorPct(slsStats.assigned, slsStats.total);
            const pctSlsSynced = floorPct(slsStats.synced, slsStats.total);
            const pctSlsAssign = parseFloat(pctSlsAssignText);
            const pctSlsSync = parseFloat(pctSlsSynced);

            let pctBgColor = '#047857';
            if (pct < 50) {
                pctBgColor = '#b91c1c';
            } else if (pct < 80) {
                pctBgColor = '#b45309';
            }

            let syncBgColor = pctSlsSync >= 80 ? '#047857' : pctSlsSync >= 50 ? '#b45309' : '#b91c1c';

            const namaKabClean = d.nama_kab.replace(/\[\d+\]\s*/, '').trim().toUpperCase();
            const bgColor = idx % 2 === 0 ? '' : 'background-color: rgba(99,102,241,0.03);';

            return `
            <tr onclick="focusKabSls('${namaKabClean}')" style="${rowStyle} ${bgColor} cursor: pointer; transition: background-color 0.15s;" onmouseover="this.style.backgroundColor='rgba(99, 102, 241, 0.08)';" onmouseout="this.style.backgroundColor='${idx % 2 === 0 ? '' : 'rgba(99, 102, 241, 0.03)'}'">
                <td style="${tdBase} text-align: center; color: var(--text-secondary); font-weight: 500;">${idx + 1}</td>
                <td style="${tdBase} text-align: center; font-family: monospace; font-size: 0.85rem; color: var(--text-secondary);">${d.kode_kab}</td>
                <td style="${tdBase} font-weight: 600; color: var(--text);">${namaKabClean}</td>
                <td style="${tdBase} text-align: right; font-family: monospace; font-weight: 600; color: var(--text-secondary);">${fmt(total)}</td>
                <td style="${tdBase} text-align: right; font-family: monospace; font-weight: 600; color: #10b981;">${fmt(assigned)}</td>
                <td style="${tdBase} text-align: right; font-family: monospace; font-weight: 600; color: #ef4444;">${fmt(unassigned)}</td>
                <td style="${tdBase} text-align: right; font-family: monospace; font-weight: 600; color: #f59e0b;">${fmt(belumSyncVal)}</td>
                <td style="${tdBase} text-align: center; background-color: ${pctBgColor}; color: white; font-weight: 700; font-family: monospace;">${pctAssignText}</td>
                <td style="${tdBase} text-align: center; background-color: ${syncBgColor}; color: white; font-weight: 700; font-family: monospace;">${pctSlsSynced}</td>
            </tr>`;
        }).join('');

        const totalPctText = floorPct(totalSudah, totalUsaha);
        const totalPct = parseFloat(totalPctText);
        let totalPctBgColor = '#047857';
        if (totalPct < 50) {
            totalPctBgColor = '#b91c1c';
        } else if (totalPct < 80) {
            totalPctBgColor = '#b45309';
        }

        const totalPctSlsAssignText = floorPct(totalSlsAssigned, totalSlsTotal);
        const totalPctSlsSyncText = floorPct(totalSlsSynced, totalSlsTotal);
        const totalPctSlsAssign = parseFloat(totalPctSlsAssignText);
        const totalPctSlsSync = parseFloat(totalPctSlsSyncText);
        let totalAssignBgColor = totalPctSlsAssign >= 80 ? '#047857' : totalPctSlsAssign >= 50 ? '#b45309' : '#b91c1c';
        let totalSyncBgColor = totalPctSlsSync >= 80 ? '#047857' : totalPctSlsSync >= 50 ? '#b45309' : '#b91c1c';

        tbody.innerHTML = rowsHtml + `
        <tr style="border-top: 2px solid var(--card-border); background-color: var(--card-bg); font-weight: 800;">
            <td style="${tdBase} text-align: center; color: var(--text);"></td>
            <td style="${tdBase} text-align: center; color: var(--text);"></td>
            <td style="${tdBase} color: var(--text);">TOTAL</td>
            <td style="${tdBase} text-align: right; font-family: monospace; color: var(--text-secondary);">${fmt(totalUsaha)}</td>
            <td style="${tdBase} text-align: right; font-family: monospace; color: #10b981;">${fmt(totalSudah)}</td>
            <td style="${tdBase} text-align: right; font-family: monospace; color: #ef4444;">${fmt(totalBelum)}</td>
            <td style="${tdBase} text-align: right; font-family: monospace; color: #f59e0b;">${fmt(totalBelumSync)}</td>
            <td style="${tdBase} text-align: center; background-color: ${totalPctBgColor}; color: white; font-weight: 800; font-family: monospace;">${totalPctText}</td>
            <td style="${tdBase} text-align: center; background-color: ${totalSyncBgColor}; color: white; font-weight: 800; font-family: monospace;">${totalPctSlsSyncText}</td>
        </tr>`;
    }

    window.focusKabSls = function (kabName) {
        // First switch to Tab 1 (SLS/Sub-SLS) where the SLS table now lives
        window.switchAssignSubtab('kab');

        const kabSelect = document.getElementById('sls-kab-filter');
        if (!kabSelect) return;

        let matchedVal = 'all';
        for (let i = 0; i < kabSelect.options.length; i++) {
            const optText = kabSelect.options[i].text.toUpperCase();
            const optVal = kabSelect.options[i].value.toUpperCase();
            const target = kabName.toUpperCase();
            if (optText.includes(target) || target.includes(optText) || optVal.includes(target) || target.includes(optVal)) {
                matchedVal = kabSelect.options[i].value;
                break;
            }
        }

        kabSelect.value = matchedVal;
        kabSelect.dispatchEvent(new Event('change'));

        const slsSearchInput = document.getElementById('sls-search-input');
        if (slsSearchInput) {
            slsSearchInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
            slsSearchInput.focus();
        }
    };

    let assignChartInstance = null;
    let progressGaugeInstance = null;
    let syncGaugeInstance = null;

    window.switchAssignSubtab = function (tabName) {
        const sections = ['kab', 'sls', 'petugas'];
        sections.forEach(s => {
            const el = document.getElementById(`assign-${s}-section`);
            const btn = document.getElementById(`assign-subtab-btn-${s}`);
            if (el) {
                el.style.display = s === tabName ? 'block' : 'none';
            }
            if (btn) {
                if (s === tabName) {
                    btn.classList.add('active');
                    btn.style.backgroundColor = 'var(--primary)';
                    btn.style.color = 'white';
                } else {
                    btn.classList.remove('active');
                    btn.style.backgroundColor = '';
                    btn.style.color = '';
                }
            }
        });
        // When Tab 1 (SLS/Sub-SLS) is activated, also render SLS and Sync tables
        if (tabName === 'kab') {
            if (typeof renderSlsTable === 'function') renderSlsTable();
            if (typeof window.renderSyncTable === 'function') window.renderSyncTable();
        }
        // When Tab 2 (Assignment) is activated, render Kab Summary and load granular assignments data
        if (tabName === 'sls') {
            if (typeof renderKabSummaryTable === 'function') renderKabSummaryTable();
            if (typeof loadGranularAssignmentsData === 'function') loadGranularAssignmentsData();
        }
        // When Tab 3 (Petugas) is activated, render Petugas Table
        if (tabName === 'petugas') {
            if (typeof renderPetugasTable === 'function') renderPetugasTable();
        }
    };

    function renderAssignChart() {
        const ctx = document.getElementById('assignChart');
        if (!ctx) return;

        if (assignChartInstance) {
            assignChartInstance.destroy();
        }

        if (!window.ASSIGN_DATA || window.ASSIGN_DATA.length === 0) {
            console.warn("ASSIGN_DATA belum tersedia.");
            return;
        }

        // Aggregate SLS-level assignment and sync by Kabupaten
        const slsStatsByKab = {};

        // Initialize for all kabupaten from window.ASSIGN_DATA
        window.ASSIGN_DATA.forEach(d => {
            slsStatsByKab[d.kode_kab] = { total: 0, assigned: 0, synced: 0 };
        });

        let hasLocalSls = false;
        if (window.ASSIGN_SLS_DATA && window.ASSIGN_SLS_DATA.length > 0) {
            hasLocalSls = true;
            window.ASSIGN_SLS_DATA.forEach(sls => {
                if (sls.desa_name === '-' || sls.sls_name === '-') return;
                const code = sls.sls_code || sls.sls_id;
                const kodeKab = code ? code.substring(0, 4) : '';
                if (kodeKab && slsStatsByKab[kodeKab]) {
                    slsStatsByKab[kodeKab].total++;
                    if ((sls.assigned || 0) > 0) {
                        slsStatsByKab[kodeKab].assigned++;
                    }
                    if ((sls.sync_count || 0) > 0) {
                        slsStatsByKab[kodeKab].synced++;
                    }
                }
            });
        }

        if (!hasLocalSls && window.SUPERSET_SYNC_SLS_DATA && window.SUPERSET_SYNC_SLS_DATA.length > 0) {
            window.SUPERSET_SYNC_SLS_DATA.forEach(sls => {
                if (sls.sls_name === '-' || sls.desa_name === '-') return;
                const code = sls.sls_code || sls.sls_id;
                const kodeKab = code ? code.substring(0, 4) : '';
                if (kodeKab && slsStatsByKab[kodeKab]) {
                    slsStatsByKab[kodeKab].total++;
                    slsStatsByKab[kodeKab].assigned++;
                    if ((sls.sync_count || 0) > 0) {
                        slsStatsByKab[kodeKab].synced++;
                    }
                }
            });
        }

        const labels = window.ASSIGN_DATA.map(d => d.nama_kab.replace(/\[\d+\] /, ''));
        const syncedData = window.ASSIGN_DATA.map(d => slsStatsByKab[d.kode_kab]?.synced || 0);
        const assignedOnlyData = window.ASSIGN_DATA.map(d => {
            const stats = slsStatsByKab[d.kode_kab];
            if (!stats) return 0;
            return Math.max(0, stats.assigned - stats.synced);
        });
        const notAssignedData = window.ASSIGN_DATA.map(d => {
            const stats = slsStatsByKab[d.kode_kab];
            if (!stats) return 0;
            return Math.max(0, stats.total - stats.assigned);
        });

        const textColor = getThemeColor('--text-secondary', '#9ca3af');
        const gridColor = getThemeColor('--card-border', 'rgba(255, 255, 255, 0.08)');
        assignChartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Sudah Sync',
                        data: syncedData,
                        backgroundColor: 'rgba(234, 179, 8, 0.9)', // Yellow
                        borderRadius: 4,
                    },
                    {
                        label: 'Sudah Ditugaskan (Belum Sync)',
                        data: assignedOnlyData,
                        backgroundColor: 'rgba(16, 185, 129, 0.9)', // Green
                        borderRadius: 4,
                    },
                    {
                        label: 'Belum Ditugaskan',
                        data: notAssignedData,
                        backgroundColor: 'rgba(239, 68, 68, 0.9)', // Red
                        borderRadius: 4,
                    }
                ]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: textColor,
                            font: { family: "'Outfit', sans-serif", size: 11 },
                            usePointStyle: true,
                            padding: 15
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.9)',
                        titleFont: { family: "'Outfit', sans-serif", size: 13 },
                        bodyFont: { family: "'Outfit', sans-serif", size: 12 },
                        padding: 12,
                        cornerRadius: 8
                    }
                },
                scales: {
                    x: {
                        stacked: true,
                        grid: { color: gridColor },
                        ticks: { color: textColor }
                    },
                    y: {
                        stacked: true,
                        grid: { display: false },
                        ticks: { color: textColor }
                    }
                }
            }
        });

        // Update Speedometer Gauge Chart (Alokasi)
        const ctxGauge = document.getElementById('progressGaugeChart');
        if (ctxGauge) {
            if (progressGaugeInstance) {
                progressGaugeInstance.destroy();
            }

            let totalSls = 0;
            let assignedSls = 0;

            Object.values(slsStatsByKab).forEach(stats => {
                totalSls += stats.total;
                assignedSls += stats.assigned;
            });

            // Hardcoded fallback if no SLS data is loaded yet
            if (totalSls === 0) {
                totalSls = 17037;
                assignedSls = 17037;
            }

            const pctText = floorPct(assignedSls, totalSls);
            const pct = parseFloat(pctText);

            const pctCenter = document.getElementById('gauge-percent-center');
            if (pctCenter) pctCenter.innerText = pctText + '%';

            const statsDetails = document.getElementById('gauge-stats-details');
            if (statsDetails) {
                statsDetails.innerHTML = `<span style="font-weight: 700; color: var(--text-primary); font-size: 1.15rem; display: block; margin-bottom: 0.25rem;">${new Intl.NumberFormat('id-ID').format(assignedSls)}</span> dari ${new Intl.NumberFormat('id-ID').format(totalSls)} SLS telah ditugaskan`;
            }

            const accentColor = getThemeColor('--primary', '#6366f1');
            const trackColor = getThemeColor('--card-border', 'rgba(255, 255, 255, 0.08)');

            progressGaugeInstance = new Chart(ctxGauge, {
                type: 'doughnut',
                data: {
                    datasets: [{
                        data: [pct, Math.max(0, 100 - pct)],
                        backgroundColor: [accentColor, trackColor],
                        borderWidth: 0,
                        borderRadius: pct > 0 ? 8 : 0,
                        cutout: '82%',
                        circumference: 180,
                        rotation: 270
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: { enabled: false }
                    },
                    events: []
                }
            });
        }
        updateGlobalSyncProgress();
    }

    // SLS state
    window.slsSort = { column: 'kab_name', order: 'asc' };
    window.slsCurrentPage = 1;
    let SLS_ITEMS_PER_PAGE = 25;
    window.changeSlsLimit = function (val) {
        SLS_ITEMS_PER_PAGE = parseInt(val) || 25;
        window.slsCurrentPage = 1;
        renderSlsTable();
    };

    // Header sort trigger
    window.sortSlsTable = function (column) {
        const current = window.slsSort;
        if (current.column === column) {
            current.order = current.order === 'asc' ? 'desc' : 'asc';
        } else {
            current.column = column;
            current.order = 'asc';
        }
        window.slsCurrentPage = 1; // reset page on sort
        renderSlsTable();
    };

    // Populates select dropdown elements dynamically
    let isSlsFiltersPopulated = false;
    function populateSlsFilters() {
        if (!window.ASSIGN_SLS_DATA || window.ASSIGN_SLS_DATA.length === 0 || isSlsFiltersPopulated) return;

        const kabSelect = document.getElementById('sls-kab-filter');
        if (!kabSelect) return;

        // Extract unique regions
        const uniqueKabs = [...new Set(window.ASSIGN_SLS_DATA.map(i => i.kab_name))].sort();

        kabSelect.innerHTML = '<option value="all">Semua Kabupaten</option>' +
            uniqueKabs.map(k => `<option value="${k}">${k}</option>`).join('');

        // Register cascade change listeners
        kabSelect.addEventListener('change', () => {
            updateKecOptions();
            window.slsCurrentPage = 1;
            renderSlsTable();
        });

        const kecSelect = document.getElementById('sls-kec-filter');
        if (kecSelect) {
            kecSelect.addEventListener('change', () => {
                updateDesaOptions();
                window.slsCurrentPage = 1;
                renderSlsTable();
            });
        }

        const desaSelect = document.getElementById('sls-desa-filter');
        if (desaSelect) {
            desaSelect.addEventListener('change', () => {
                updateSlsPetugasOptions();
                window.slsCurrentPage = 1;
                renderSlsTable();
            });
        }

        const petugasSelect = document.getElementById('sls-petugas-filter');
        if (petugasSelect) {
            petugasSelect.addEventListener('change', () => {
                window.slsCurrentPage = 1;
                renderSlsTable();
            });
        }

        isSlsFiltersPopulated = true;
        updateKecOptions();
    }

    function updateKecOptions() {
        const kabVal = document.getElementById('sls-kab-filter').value;
        const kecSelect = document.getElementById('sls-kec-filter');
        if (!kecSelect) return;

        if (kabVal === 'all') {
            kecSelect.innerHTML = '<option value="all">Semua Kecamatan</option>';
            kecSelect.disabled = true;
            updateDesaOptions();
            return;
        }

        kecSelect.disabled = false;
        const filteredSls = window.ASSIGN_SLS_DATA.filter(i => i.kab_name === kabVal);
        const uniqueKecs = [...new Set(filteredSls.map(i => i.kec_name))].sort();

        kecSelect.innerHTML = '<option value="all">Semua Kecamatan</option>' +
            uniqueKecs.map(k => `<option value="${k}">${k}</option>`).join('');

        updateDesaOptions();
    }

    function updateDesaOptions() {
        const kabFilterEl = document.getElementById('sls-kab-filter');
        const kecFilterEl = document.getElementById('sls-kec-filter');
        if (!kabFilterEl || !kecFilterEl) return;
        const kabVal = kabFilterEl.value;
        const kecVal = kecFilterEl.value;
        const desaSelect = document.getElementById('sls-desa-filter');
        if (!desaSelect) return;

        if (kecVal === 'all') {
            desaSelect.innerHTML = '<option value="all">Semua Desa</option>';
            desaSelect.disabled = true;
            updateSlsPetugasOptions();
            return;
        }

        desaSelect.disabled = false;
        const filteredSls = window.ASSIGN_SLS_DATA.filter(i => i.kab_name === kabVal && i.kec_name === kecVal);
        const uniqueDesas = [...new Set(filteredSls.map(i => i.desa_name))].sort();

        desaSelect.innerHTML = '<option value="all">Semua Desa</option>' +
            uniqueDesas.map(d => `<option value="${d}">${d}</option>`).join('');

        updateSlsPetugasOptions();
    }

    function updateSlsPetugasOptions() {
        const kabVal = document.getElementById('sls-kab-filter')?.value || 'all';
        const kecVal = document.getElementById('sls-kec-filter')?.value || 'all';
        const desaVal = document.getElementById('sls-desa-filter')?.value || 'all';
        const petugasSelect = document.getElementById('sls-petugas-filter');
        if (!petugasSelect) return;

        const filtered = window.ASSIGN_SLS_DATA.filter(item => {
            if (kabVal !== 'all' && item.kab_name !== kabVal) return false;
            if (kecVal !== 'all' && item.kec_name !== kecVal) return false;
            if (desaVal !== 'all' && item.desa_name !== desaVal) return false;
            return true;
        });

        const officerSet = new Set();
        filtered.forEach(item => {
            if (item.officers && Array.isArray(item.officers)) {
                item.officers.forEach(ofc => {
                    if (ofc && ofc !== '-') {
                        officerSet.add(ofc);
                    }
                });
            }
        });

        const sortedOfficers = Array.from(officerSet).sort();
        const currentSelected = petugasSelect.value;

        petugasSelect.innerHTML = '<option value="all">Semua Petugas</option>' +
            sortedOfficers.map(o => `<option value="${o}">${o}</option>`).join('');

        if (sortedOfficers.includes(currentSelected)) {
            petugasSelect.value = currentSelected;
        } else {
            petugasSelect.value = 'all';
        }
    }

    function renderSlsTableHeaders() {
        const headerRow = document.getElementById('sls-table-headers');
        if (!headerRow) return;

        const getIcon = (col) => {
            if (window.slsSort.column !== col) return ' ↕';
            return window.slsSort.order === 'asc' ? ' ▲' : ' ▼';
        };

        headerRow.innerHTML = `
            <th onclick="sortSlsTable('kab_name')" style="font-family: 'Outfit', sans-serif; cursor: pointer; user-select: none;">Kabupaten${getIcon('kab_name')}</th>
            <th onclick="sortSlsTable('kec_name')" style="font-family: 'Outfit', sans-serif; cursor: pointer; user-select: none;">Kecamatan${getIcon('kec_name')}</th>
            <th onclick="sortSlsTable('desa_name')" style="font-family: 'Outfit', sans-serif; cursor: pointer; user-select: none;">Desa${getIcon('desa_name')}</th>
            <th onclick="sortSlsTable('sls_name')" style="font-family: 'Outfit', sans-serif; cursor: pointer; user-select: none;">Kode & Nama SLS${getIcon('sls_name')}</th>
            <th onclick="sortSlsTable('total')" style="font-family: 'Outfit', sans-serif; text-align: center; cursor: pointer; user-select: none;">Total Target${getIcon('total')}</th>
            <th onclick="sortSlsTable('assigned')" style="font-family: 'Outfit', sans-serif; text-align: center; color: var(--color-delivered); cursor: pointer; user-select: none;">Ditugaskan${getIcon('assigned')}</th>
            <th onclick="sortSlsTable('unassigned')" style="font-family: 'Outfit', sans-serif; text-align: center; color: var(--color-bounced); cursor: pointer; user-select: none;">Belum Ditugaskan${getIcon('unassigned')}</th>
            <th onclick="sortSlsTable('completed')" style="font-family: 'Outfit', sans-serif; text-align: center; color: #10b981; cursor: pointer; user-select: none;">Selesai${getIcon('completed')}</th>
            <th onclick="sortSlsTable('unsynced')" style="font-family: 'Outfit', sans-serif; text-align: center; color: #f59e0b; cursor: pointer; user-select: none;">Belum Sync${getIcon('unsynced')}</th>
            <th style="font-family: 'Outfit', sans-serif; user-select: none;">Status & Petugas</th>
        `;
    }

    function renderSlsTable() {
        const tbody = document.getElementById('sls-table-body');
        if (!tbody) return;

        if (!window.ASSIGN_SLS_DATA || window.ASSIGN_SLS_DATA.length === 0) {
            tbody.innerHTML = `<tr><td colspan="10" style="text-align: center; padding: 2rem; color: var(--text-secondary);">Data SLS belum tersedia. Pastikan sinkronisasi data sedang berjalan.</td></tr>`;
            return;
        }

        // Populate regional options first time data is available
        populateSlsFilters();

        // 1. Get filter inputs
        const searchInputEl = document.getElementById('sls-search-input');
        const searchVal = searchInputEl ? searchInputEl.value.toLowerCase().trim() : '';
        const kabFilter = document.getElementById('sls-kab-filter')?.value || 'all';
        const kecFilter = document.getElementById('sls-kec-filter')?.value || 'all';
        const desaFilter = document.getElementById('sls-desa-filter')?.value || 'all';
        const petugasFilter = document.getElementById('sls-petugas-filter')?.value || 'all';
        const assignmentFilter = document.getElementById('sls-assignment-filter')?.value || 'all';

        // 2. Filter logic
        const filtered = window.ASSIGN_SLS_DATA.filter(item => {
            // Region cascading filters
            if (kabFilter !== 'all' && item.kab_name !== kabFilter) return false;
            if (kecFilter !== 'all' && item.kec_name !== kecFilter) return false;
            if (desaFilter !== 'all' && item.desa_name !== desaFilter) return false;

            // Exclude dummy SLS
            if (item.desa_name === '-' || item.sls_name === '-') return false;

            // Petugas filter
            if (petugasFilter !== 'all') {
                if (!item.officers || !item.officers.includes(petugasFilter)) return false;
            }

            // Assignment status filter
            if (assignmentFilter === 'fully_assigned' && item.unassigned !== 0) return false;
            if (assignmentFilter === 'partially_assigned' && !(item.assigned > 0 && item.unassigned > 0)) return false;
            if (assignmentFilter === 'unassigned' && item.assigned !== 0) return false;

            // Search val
            if (searchVal) {
                const slsCodeStr = item.sls_code || '';
                const slsNameStr = item.sls_name || '';
                const desaNameStr = item.desa_name || '';
                const kecNameStr = item.kec_name || '';
                const kabNameStr = item.kab_name || '';
                const officersStr = (item.officers || []).join(' ');
                const matchText = (slsCodeStr + ' ' + slsNameStr + ' ' + desaNameStr + ' ' + kecNameStr + ' ' + kabNameStr + ' ' + officersStr).toLowerCase();
                if (!matchText.includes(searchVal)) return false;
            }

            return true;
        });

        // 3. Render statistics for the region-filtered or active set of data
        const statsBase = window.ASSIGN_SLS_DATA.filter(item => {
            if (kabFilter !== 'all' && item.kab_name !== kabFilter) return false;
            if (kecFilter !== 'all' && item.kec_name !== kecFilter) return false;
            if (desaFilter !== 'all' && item.desa_name !== desaFilter) return false;
            if (item.desa_name === '-' || item.sls_name === '-') return false; // Exclude dummy SLS
            return true;
        });

        const totalSls = statsBase.length;
        const activeSls = statsBase.filter(i => i.total > 0);
        const activeSlsCount = activeSls.length;

        const fullyAssigned = activeSls.filter(i => i.unassigned === 0).length;
        const partiallyAssigned = activeSls.filter(i => i.assigned > 0 && i.unassigned > 0).length;
        const unassigned = activeSls.filter(i => i.assigned === 0).length;
        const totalTarget = statsBase.reduce((sum, i) => sum + (i.total || 0), 0);
        const totalAssignedUsaha = statsBase.reduce((sum, i) => sum + (i.assigned || 0), 0);
        const totalUnassignedUsaha = statsBase.reduce((sum, i) => sum + (i.unassigned || 0), 0);

        // Read official, uncapped stats from ASSIGN_DATA based on active filters
        let officialTotalTarget = 0;
        let officialTotalAssigned = 0;
        let officialTotalUnassigned = 0;
        let useOfficialStats = (kecFilter === 'all' && desaFilter === 'all');

        if (useOfficialStats && window.ASSIGN_DATA) {
            window.ASSIGN_DATA.forEach(d => {
                if (kabFilter !== 'all') {
                    const cleanKabFilter = kabFilter.replace(/\[\d+\]\s*/, '').trim().toUpperCase();
                    const cleanKabName = d.nama_kab.replace(/\[\d+\]\s*/, '').trim().toUpperCase();
                    if (cleanKabName !== cleanKabFilter) return;
                }
                officialTotalTarget += d.total || 0;
                officialTotalAssigned += d.assigned || 0;
                officialTotalUnassigned += d.have_not_assigned || 0;
            });
        }

        const finalTotalTarget = useOfficialStats ? officialTotalTarget : totalTarget;
        const finalTotalAssignedUsaha = useOfficialStats ? officialTotalAssigned : totalAssignedUsaha;
        const finalTotalUnassignedUsaha = useOfficialStats ? officialTotalUnassigned : totalUnassignedUsaha;

        // Update summary card values
        const formatNum = (num) => new Intl.NumberFormat('id-ID').format(num || 0);
        document.getElementById('sls-stat-total').textContent = formatNum(totalSls);
        document.getElementById('sls-substat-total').textContent = `Target Usaha: ${formatNum(finalTotalTarget)}`;

        const denom = activeSlsCount > 0 ? activeSlsCount : totalSls;
        document.getElementById('sls-stat-fully').textContent = formatNum(fullyAssigned);
        document.getElementById('sls-pct-fully').innerHTML =
            (denom > 0 ? `${((fullyAssigned / denom) * 100).toFixed(2)}% dari SLS aktif` : '0.00%') +
            `<span style="display:block; margin-top: 0.25rem; font-weight: 700; color: #10b981; font-size: 0.75rem;">Usaha Ditugaskan: ${formatNum(finalTotalAssignedUsaha)}</span>`;

        document.getElementById('sls-stat-partially').textContent = formatNum(partiallyAssigned);
        document.getElementById('sls-pct-partially').textContent = denom > 0 ? `${((partiallyAssigned / denom) * 100).toFixed(2)}% dari SLS aktif` : '0.00% dari SLS aktif';

        document.getElementById('sls-stat-unassigned').textContent = formatNum(unassigned);
        document.getElementById('sls-pct-unassigned').innerHTML =
            (denom > 0 ? `${((unassigned / denom) * 100).toFixed(2)}% dari SLS aktif` : '0.00%') +
            `<span style="display:block; margin-top: 0.25rem; font-weight: 700; color: #ef4444; font-size: 0.75rem;">Usaha Belum Ditugaskan: ${formatNum(finalTotalUnassignedUsaha)}</span>`;

        // 4. Sort logic
        const col = window.slsSort.column;
        const order = window.slsSort.order === 'asc' ? 1 : -1;
        filtered.sort((a, b) => {
            let valA = col === 'unsynced' ? Math.max(0, a.assigned - (a.sync_count || 0)) : a[col];
            let valB = col === 'unsynced' ? Math.max(0, b.assigned - (b.sync_count || 0)) : b[col];
            if (typeof valA === 'string') {
                return valA.localeCompare(valB) * order;
            }
            return ((valA || 0) - (valB || 0)) * order;
        });

        // Update headers (shows active sort icon)
        renderSlsTableHeaders();

        if (filtered.length === 0) {
            tbody.innerHTML = `<tr><td colspan="10" style="text-align: center; padding: 3rem 1rem; color: var(--text-secondary);">Tidak ada data SLS yang cocok dengan filter pencarian.</td></tr>`;
            document.getElementById('sls-pagination-info').textContent = 'Menampilkan 0 - 0 dari 0 SLS';
            document.getElementById('sls-pagination-buttons').innerHTML = '';
            return;
        }

        
        // Apply Sort Logic
        if (window.slsSort && window.slsSort.column) {
            filtered.sort((a, b) => {
                let valA = a[window.slsSort.column] || '';
                let valB = b[window.slsSort.column] || '';
                if (typeof valA === 'string') valA = valA.toLowerCase();
                if (typeof valB === 'string') valB = valB.toLowerCase();
                
                let cmp = 0;
                if (valA < valB) cmp = -1;
                if (valA > valB) cmp = 1;
                return window.slsSort.order === 'asc' ? cmp : -cmp;
            });
        }
        
        // 5. Pagination logic

        const totalFiltered = filtered.length;
        const maxPage = Math.ceil(totalFiltered / SLS_ITEMS_PER_PAGE);
        if (window.slsCurrentPage > maxPage) window.slsCurrentPage = maxPage;
        if (window.slsCurrentPage < 1) window.slsCurrentPage = 1;

        const startIdx = (window.slsCurrentPage - 1) * SLS_ITEMS_PER_PAGE;
        const endIdx = Math.min(startIdx + SLS_ITEMS_PER_PAGE, totalFiltered);
        const slicedData = filtered.slice(startIdx, endIdx);

        document.getElementById('sls-pagination-info').textContent = `Menampilkan ${formatNum(startIdx + 1)} - ${formatNum(endIdx)} dari ${formatNum(totalFiltered)} SLS`;

        // Render table rows
        tbody.innerHTML = slicedData.map(item => {
            let badge = '';
            if (item.unassigned === 0) {
                badge = '<span style="background-color: rgba(16, 185, 129, 0.1); color: #10b981; padding: 0.25rem 0.5rem; border-radius: 0.375rem; font-size: 0.75rem; font-weight: 600;">Sudah Ditugaskan</span>';
            } else if (item.assigned === 0) {
                badge = '<span style="background-color: rgba(239, 68, 68, 0.1); color: #ef4444; padding: 0.25rem 0.5rem; border-radius: 0.375rem; font-size: 0.75rem; font-weight: 600;">Belum Ditugaskan</span>';
            } else {
                badge = '<span style="background-color: rgba(245, 158, 11, 0.1); color: #f59e0b; padding: 0.25rem 0.5rem; border-radius: 0.375rem; font-size: 0.75rem; font-weight: 600;">Sebagian Ditugaskan</span>';
            }

            const officers = item.officers && item.officers.length > 0 ? item.officers.join(', ') : '-';
            const unsynced = Math.max(0, item.assigned - (item.sync_count || 0));

            // Highlight search query
            const hl = (txt) => highlightText(txt, searchVal);

            return `
                <tr class="table-row">
                    <td style="padding: 1rem; border-bottom: 1px solid var(--card-border); vertical-align: top;">${hl(item.kab_name || '-')}</td>
                    <td style="padding: 1rem; border-bottom: 1px solid var(--card-border); vertical-align: top;">${hl(item.kec_name || '-')}</td>
                    <td style="padding: 1rem; border-bottom: 1px solid var(--card-border); vertical-align: top;">${hl(item.desa_name || '-')}</td>
                    <td style="padding: 1rem; border-bottom: 1px solid var(--card-border); vertical-align: top; font-family: monospace;">${hl(item.sls_code || '-')} <br><span style="font-family: 'Outfit', sans-serif; font-size: 0.85rem; color: var(--text-secondary);">${hl(item.sls_name || '-')}</span></td>
                    <td style="padding: 1rem; border-bottom: 1px solid var(--card-border); vertical-align: top; text-align: center; font-weight: 700; font-size: 1.1rem;">${formatNum(item.total)}</td>
                    <td style="padding: 1rem; border-bottom: 1px solid var(--card-border); vertical-align: top; text-align: center; color: var(--color-delivered); font-weight: 700; font-size: 1.1rem;">${formatNum(item.assigned)}</td>
                    <td style="padding: 1rem; border-bottom: 1px solid var(--card-border); vertical-align: top; text-align: center; color: var(--color-bounced); font-weight: 700; font-size: 1.1rem;">${formatNum(item.unassigned)}</td>
                    <td style="padding: 1rem; border-bottom: 1px solid var(--card-border); vertical-align: top; text-align: center; color: #10b981; font-weight: 700; font-size: 1.1rem;">${formatNum(item.completed || 0)}</td>
                    <td style="padding: 1rem; border-bottom: 1px solid var(--card-border); vertical-align: top; text-align: center; color: #f59e0b; font-weight: 700; font-size: 1.1rem;">${formatNum(unsynced)}</td>
                    <td style="padding: 1rem; border-bottom: 1px solid var(--card-border); vertical-align: top;">
                        <div style="margin-bottom: 0.5rem;">${badge}</div>
                        <div style="font-size: 0.85rem; color: var(--text-secondary); line-height: 1.4;">${hl(officers)}</div>
                    </td>
                </tr>
            `;
        }).join('');

        // Render pagination buttons
        renderSlsPaginationButtons(maxPage);
    }

    function renderSlsPaginationButtons(maxPage) {
        const btnContainer = document.getElementById('sls-pagination-buttons');
        if (!btnContainer) return;
        btnContainer.innerHTML = '';

        const btnStyle = `padding: 0.4rem 0.75rem; font-size: 0.8rem; font-weight: 600; border-radius: 0.5rem; border: 1px solid var(--card-border); background-color: var(--card-bg); color: var(--text); cursor: pointer; transition: all 0.2s;`;
        const activeStyle = `padding: 0.4rem 0.75rem; font-size: 0.8rem; font-weight: 700; border-radius: 0.5rem; border: 1px solid transparent; background-color: var(--primary); color: white; cursor: default;`;

        // First & Prev buttons
        if (window.slsCurrentPage > 1) {
            const prevBtn = document.createElement('button');
            prevBtn.innerHTML = '&lt;';
            prevBtn.style.cssText = btnStyle;
            prevBtn.addEventListener('click', () => {
                window.slsCurrentPage--;
                renderSlsTable();
            });
            btnContainer.appendChild(prevBtn);
        }

        // Logic to display limited page range
        let startPage = Math.max(1, window.slsCurrentPage - 2);
        let endPage = Math.min(maxPage, window.slsCurrentPage + 2);

        if (startPage > 1) {
            const page1 = document.createElement('button');
            page1.textContent = '1';
            page1.style.cssText = btnStyle;
            page1.addEventListener('click', () => {
                window.slsCurrentPage = 1;
                renderSlsTable();
            });
            btnContainer.appendChild(page1);

            if (startPage > 2) {
                const dots = document.createElement('span');
                dots.textContent = '...';
                dots.style.cssText = 'color: var(--text-secondary); font-size: 0.8rem; padding: 0 0.25rem;';
                btnContainer.appendChild(dots);
            }
        }

        for (let i = startPage; i <= endPage; i++) {
            const btn = document.createElement('button');
            btn.textContent = i;
            if (i === window.slsCurrentPage) {
                btn.style.cssText = activeStyle;
            } else {
                btn.style.cssText = btnStyle;
                btn.addEventListener('click', () => {
                    window.slsCurrentPage = i;
                    renderSlsTable();
                });
            }
            btnContainer.appendChild(btn);
        }

        if (endPage < maxPage) {
            if (endPage < maxPage - 1) {
                const dots = document.createElement('span');
                dots.textContent = '...';
                dots.style.cssText = 'color: var(--text-secondary); font-size: 0.8rem; padding: 0 0.25rem;';
                btnContainer.appendChild(dots);
            }

            const pageLast = document.createElement('button');
            pageLast.textContent = maxPage;
            pageLast.style.cssText = btnStyle;
            pageLast.addEventListener('click', () => {
                window.slsCurrentPage = maxPage;
                renderSlsTable();
            });
            btnContainer.appendChild(pageLast);
        }

        // Next & Last buttons
        if (window.slsCurrentPage < maxPage) {
            const nextBtn = document.createElement('button');
            nextBtn.innerHTML = '&gt;';
            nextBtn.style.cssText = btnStyle;
            nextBtn.addEventListener('click', () => {
                window.slsCurrentPage++;
                renderSlsTable();
            });
            btnContainer.appendChild(nextBtn);
        }
    }

    // --- DAFTAR PETUGAS TABLE ---
    window.petugasCurrentPage = 1;
    let petugasRowsPerPage = 50;
    window.petugasSort = { column: 'username', order: 'asc' };

    window.changePetugasLimit = function (val) {
        petugasRowsPerPage = parseInt(val) || 50;
        window.petugasCurrentPage = 1;
        window.renderPetugasTable();
    };

    window.sortPetugasTable = function (column) {
        const current = window.petugasSort;
        if (current.column === column) {
            current.order = current.order === 'asc' ? 'desc' : 'asc';
        } else {
            current.column = column;
            current.order = 'asc';
        }
        window.petugasCurrentPage = 1;

        // Update header indicators
        ['username', 'roleName', 'totalRegions', 'workload'].forEach(col => {
            const el = document.getElementById(`petugas-sort-${col}`);
            if (el) {
                if (current.column === col) {
                    el.innerText = current.order === 'asc' ? ' ▲' : ' ▼';
                } else {
                    el.innerText = ' ↕';
                }
            }
        });

        window.renderPetugasTable();
    };

    window.togglePetugasRow = function (rowEl, username) {
        const escapedUser = username.replace(/[^a-zA-Z0-9]/g, '_');
        const detailRow = document.getElementById(`petugas-detail-${escapedUser}`);
        if (!detailRow) return;

        if (detailRow.style.display === 'none') {
            // Hide all other detailed rows
            document.querySelectorAll('[id^="petugas-detail-"]').forEach(el => {
                el.style.display = 'none';
            });

            // Show this detailed row
            detailRow.style.display = 'table-row';

            // Render the SLS list for this officer
            const tbody = document.getElementById(`petugas-sls-tbody-${escapedUser}`);
            if (tbody) {
                const petugasData = window.PETUGAS_DATA || [];
                const officer = petugasData.find(o => o.username === username);
                if (officer && officer.regions) {
                    const slsMap = new Map();
                    if (window.ASSIGN_SLS_DATA) {
                        window.ASSIGN_SLS_DATA.forEach(sls => {
                            if (sls.sls_code) {
                                slsMap.set(sls.sls_code, sls);
                            }
                        });
                    }

                    const activeSubtab = localStorage.getItem('active_assign_subtab') || 'se2026';
                    const surveyType = activeSubtab === 'ub' ? 'se_ub' : 'se_umum';

                    let rowsHtml = '';
                    officer.regions.forEach((reg, idx) => {
                        const sls14 = reg.regionCode ? reg.regionCode.substring(0, 14) : '';
                        const slsInfo = slsMap.get(sls14) || {
                            sls_code: sls14,
                            sls_name: reg.regionName || '-',
                            desa_name: '-',
                            kec_name: '-',
                            kab_name: '-',
                            total: 0,
                            assigned: 0,
                            unassigned: 0
                        };

                        const totalTarget = slsInfo.total || 0;

                        const statusCounts = getSlsStatusCounts(sls14, totalTarget, surveyType);

                        let completedCount = 0;
                        Object.entries(statusCounts).forEach(([status, count]) => {
                            const key = status.toUpperCase();
                            if (key !== 'OPEN' && key !== 'DRAFT') {
                                completedCount += count;
                            }
                        });

                        let progressPct = 0;
                        if (totalTarget > 0) {
                            progressPct = (completedCount / totalTarget) * 100;
                        }

                        const badgesHtml = Object.entries(statusCounts)
                            .filter(([status, count]) => count > 0)
                            .map(([status, count]) => {
                                const style = getStatusBadgeStyle(status);
                                return `<span style="${style} padding: 0.1rem 0.35rem; border-radius: 0.25rem; font-size: 0.65rem; font-weight: 700; white-space: nowrap; display: inline-block;">${status}: ${count}</span>`;
                            }).join(' ');

                        let progressHtml = '';
                        if (totalTarget > 0) {
                            progressHtml = `
                                <div style="display: flex; flex-direction: column; align-items: flex-start; gap: 0.25rem; width: 100%;">
                                    <div style="display: flex; justify-content: space-between; width: 100%; font-size: 0.7rem; font-weight: 700; color: var(--text-primary);">
                                        <span>${completedCount}/${totalTarget} Selesai</span>
                                        <span>${progressPct.toFixed(2)}%</span>
                                    </div>
                                    <div style="width: 100%; height: 6px; background: var(--card-hover-bg); border-radius: 3px; overflow: hidden; border: 1px solid var(--card-border);">
                                        <div style="width: ${Math.min(100, progressPct)}%; height: 100%; background: ${progressPct >= 100 ? '#10b981' : 'var(--primary)'}; border-radius: 3px;"></div>
                                    </div>
                                    <div style="display: flex; flex-wrap: wrap; gap: 0.2rem; margin-top: 0.2rem; width: 100%;">
                                        ${badgesHtml}
                                    </div>
                                </div>
                            `;
                        } else {
                            if (completedCount > 0) {
                                progressHtml = `
                                    <div style="display: flex; flex-direction: column; align-items: flex-start; gap: 0.25rem; width: 100%;">
                                        <div style="display: flex; justify-content: space-between; width: 100%; font-size: 0.7rem; font-weight: 700; color: var(--text-primary);">
                                            <span>${completedCount} Baru (Selesai)</span>
                                        </div>
                                        <div style="display: flex; flex-wrap: wrap; gap: 0.2rem; margin-top: 0.2rem; width: 100%;">
                                            ${badgesHtml}
                                        </div>
                                    </div>
                                `;
                            } else {
                                progressHtml = `<span style="color: var(--text-muted); font-size: 0.7rem;">-</span>`;
                            }
                        }

                        rowsHtml += `
                            <tr style="border-bottom: 1px solid var(--card-border); background: var(--card-bg);">
                                <td style="padding: 0.5rem; text-align: center; color: var(--text-secondary);">${idx + 1}</td>
                                <td style="padding: 0.5rem; font-weight: 600; color: var(--text-primary); font-family: monospace;">${slsInfo.sls_code}</td>
                                <td style="padding: 0.5rem; color: var(--text-primary); font-weight: 500;">${slsInfo.sls_name}</td>
                                <td style="padding: 0.5rem; color: var(--text-secondary);">${slsInfo.desa_name}</td>
                                <td style="padding: 0.5rem; color: var(--text-secondary);">${slsInfo.kec_name}</td>
                                <td style="padding: 0.5rem; color: var(--text-secondary);">${slsInfo.kab_name}</td>
                                <td style="padding: 0.5rem; text-align: right; font-weight: 600; color: var(--text-primary);">${totalTarget}</td>
                                <td style="padding: 0.5rem 0.75rem; text-align: left; vertical-align: middle;">${progressHtml}</td>
                            </tr>
                        `;
                    });

                    if (rowsHtml === '') {
                        tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; padding: 1rem; color: var(--text-secondary);">Tidak ada SLS yang ditugaskan.</td></tr>`;
                    } else {
                        tbody.innerHTML = rowsHtml;
                    }
                } else {
                    tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; padding: 1rem; color: var(--text-secondary);">Gagal memuat rincian SLS petugas.</td></tr>`;
                }
            }
        } else {
            detailRow.style.display = 'none';
        }
    };

    function getOfficerSyncStats(regions) {
        let totalSls = regions ? regions.length : 0;
        let syncedSls = 0;

        // Build and cache a lookup map of sync_count from active ASSIGN_SLS_DATA
        if (!window.syncMapCache) {
            window.syncMapCache = {};
            if (window.ASSIGN_SLS_DATA) {
                window.ASSIGN_SLS_DATA.forEach(sls => {
                    const code = sls.sls_code || sls.sls_id;
                    if (code) {
                        window.syncMapCache[code] = sls.sync_count || 0;
                    }
                });
            }
        }
        
        const localSyncMap = window.syncMapCache;

        (regions || []).forEach(r => {
            if (r.regionCode) {
                const sls14 = r.regionCode.substring(0, 14);
                const count = localSyncMap[sls14] || 0;
                if (count > 0) {
                    syncedSls++;
                }
            }
        });

        return {
            total: totalSls,
            synced: syncedSls,
            percentage: totalSls > 0 ? ((syncedSls / totalSls) * 100).toFixed(2) : '0.00'
        };
    }

    function syncLocalSlsWithSupersetData() {
        if (!window.SUPERSET_SYNC_SLS_DATA || window.SUPERSET_SYNC_SLS_DATA.length === 0) return;

        const syncMap = {};
        window.SUPERSET_SYNC_SLS_DATA.forEach(item => {
            if (item.sls_code) {
                syncMap[item.sls_code] = item.sync_count;
            }
        });

        const updateList = (list) => {
            if (!list) return;
            list.forEach(sls => {
                const code = sls.sls_code;
                if (code && typeof syncMap[code] !== 'undefined') {
                    sls.sync_count = syncMap[code];
                } else {
                    sls.sync_count = 0;
                }
            });
        };

        updateList(window.ASSIGN_SLS_DATA_UMUM);
        updateList(window.ASSIGN_SLS_DATA_UB);

        const activeSubtab = localStorage.getItem('active_assign_subtab') || 'se2026';
        if (activeSubtab === 'se2026') {
            window.ASSIGN_SLS_DATA = window.ASSIGN_SLS_DATA_UMUM;
        } else {
            window.ASSIGN_SLS_DATA = window.ASSIGN_SLS_DATA_UB;
        }
    }

    function updateGlobalSyncProgress() {
        const syncContainerInner = document.getElementById('global-sync-progress-container-inner');
        const syncTextInner = document.getElementById('global-sync-text-inner');
        const syncPercentCenter = document.getElementById('sync-gauge-percent-center');

        if (!window.ASSIGN_DATA) return;

        let totalSls = 0;
        let syncedSls = 0;
        let hasLocalSyncData = false;

        if (window.ASSIGN_SLS_DATA && window.ASSIGN_SLS_DATA.length > 0) {
            window.ASSIGN_SLS_DATA.forEach(sls => {
                if (sls.desa_name === '-' || sls.sls_name === '-') return;
                totalSls++;
                if (typeof sls.sync_count !== 'undefined') {
                    hasLocalSyncData = true;
                    if (sls.sync_count > 0) {
                        syncedSls++;
                    }
                }
            });
        }

        if (!hasLocalSyncData) {
            if (!window.SUPERSET_SYNC_SLS_DATA || window.SUPERSET_SYNC_SLS_DATA.length === 0) {
                if (syncTextInner) syncTextInner.textContent = "Data sinkronisasi belum tersedia.";
                return;
            }
            window.SUPERSET_SYNC_SLS_DATA.forEach(d => {
                if (d.sls_name === '-' || d.desa_name === '-') return;
                totalSls++;
                if (d.sync_count > 0) {
                    syncedSls++;
                }
            });
        }

        const pct = totalSls > 0 ? ((syncedSls / totalSls) * 100).toFixed(2) : '0.00';
        const textContent = `${new Intl.NumberFormat('id-ID').format(syncedSls)} dari ${new Intl.NumberFormat('id-ID').format(totalSls)} SLS tersinkronisasi (Real-time)`;

        if (syncContainerInner && syncTextInner && syncPercentCenter) {
            syncTextInner.textContent = textContent;
            syncPercentCenter.innerText = pct + '%';
            syncContainerInner.style.display = 'flex';

            const ctxSyncGauge = document.getElementById('syncGaugeChart');
            if (ctxSyncGauge) {
                if (window.syncGaugeInstance) {
                    window.syncGaugeInstance.destroy();
                }

                const accentColor = getThemeColor('--color-warning', '#eab308'); // Yellow
                const trackColor = getThemeColor('--card-border', 'rgba(255, 255, 255, 0.08)');

                window.syncGaugeInstance = new Chart(ctxSyncGauge, {
                    type: 'doughnut',
                    data: {
                        datasets: [{
                            data: [parseFloat(pct), Math.max(0, 100 - parseFloat(pct))],
                            backgroundColor: [accentColor, trackColor],
                            borderWidth: 0,
                            borderRadius: parseFloat(pct) > 0 ? 8 : 0,
                            cutout: '80%',
                            circumference: 180,
                            rotation: 270
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: false },
                            tooltip: { enabled: false }
                        },
                        events: []
                    }
                });
            }
        }
    }

    window.renderPetugasTable = function () {
        const petugasData = window.PETUGAS_DATA || [];
        const tbody = document.getElementById('petugas-table-body');
        const paginationInfo = document.getElementById('petugas-pagination-info');
        if (!tbody || !paginationInfo) return;

        // Clear sync map cache on render so it refreshes with new sync data
        window.syncMapCache = null;

        const searchInputEl = document.getElementById('petugas-search-input');
        const searchVal = searchInputEl ? searchInputEl.value.toLowerCase().trim() : '';

        const roleFilterEl = document.getElementById('petugas-role-filter');
        const roleFilterVal = roleFilterEl ? roleFilterEl.value : 'all';

        const kabFilterEl = document.getElementById('petugas-kab-filter');
        const kabFilterVal = kabFilterEl ? kabFilterEl.value : 'all';

        const workloadFilterEl = document.getElementById('petugas-workload-filter');
        const workloadFilterVal = workloadFilterEl ? workloadFilterEl.value : 'all';

        // Precalculate workload (totalHH) for all officers based on active ASSIGN_SLS_DATA
        const slsTotalMap = {};
        if (window.ASSIGN_SLS_DATA) {
            window.ASSIGN_SLS_DATA.forEach(sls => {
                const code = sls.sls_code || sls.sls_id;
                if (code) {
                    slsTotalMap[code] = sls.total || 0;
                }
            });
        }
        petugasData.forEach(item => {
            let totalHH = 0;
            if (item.regions && item.regions.length > 0) {
                item.regions.forEach(reg => {
                    const code = reg.regionCode || '';
                    const slsCode = code.length === 16 ? code.substring(0, 14) : code;
                    totalHH += (slsTotalMap[slsCode] || 0);
                });
            }
            item.totalHH = totalHH;
        });

        // Update overloaded pencacah warning alert
        const totalOverloadedPencacah = petugasData.filter(item => item.roleName === 'Pencacah' && item.totalHH > 800).length;
        const alertEl = document.getElementById('petugas-overload-alert');
        if (alertEl) {
            if (totalOverloadedPencacah > 0) {
                alertEl.style.display = 'block';
                alertEl.innerHTML = `
                    <div style="background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.2); border-radius: 0.75rem; padding: 1rem; color: var(--text-primary); display: flex; align-items: center; gap: 0.75rem; font-family: 'Outfit', sans-serif;">
                        <span style="font-size: 1.5rem; line-height: 1;">⚠️</span>
                        <div style="flex: 1;">
                            <div style="font-weight: 700; color: #f87171;">Peringatan Beban Kerja Berlebih!</div>
                            <div style="font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.15rem;">
                                Terdeteksi <strong>${totalOverloadedPencacah} Pencacah</strong> dengan beban kerja di atas <strong>800 target tugas</strong>. Hal ini dapat mempengaruhi kualitas pendataan sensus.
                            </div>
                        </div>
                        <button class="btn-action" onclick="document.getElementById('petugas-workload-filter').value='overloaded'; document.getElementById('petugas-role-filter').value='Pencacah'; window.renderPetugasTable();" style="background: #ef4444; color: white; border: none; font-size: 0.8rem; padding: 0.5rem 0.75rem; border-radius: 0.5rem; height: auto; cursor: pointer;">
                            Lihat Daftar
                        </button>
                    </div>
                `;
            } else {
                alertEl.style.display = 'none';
            }
        }

        // Filter and Sort
        let filteredData = petugasData.filter(item => {
            // Search filter
            if (searchVal) {
                const uNameStr = item.username || '';
                const emailStr = item.email || '';
                const roleStr = item.roleName || '';
                const regionsStr = (item.regions || []).map(r => r.regionName).join(' ');
                const matchText = (uNameStr + ' ' + emailStr + ' ' + roleStr + ' ' + regionsStr).toLowerCase();
                if (!matchText.includes(searchVal)) return false;
            }

            // Role filter
            if (roleFilterVal !== 'all') {
                if (item.roleName !== roleFilterVal) return false;
            }

            // Kabupaten filter
            if (kabFilterVal !== 'all') {
                const hasMatchingRegion = (item.regions || []).some(r => {
                    if (!r.regionCode) return false;
                    if (r.regionCode === '72') return true; // Provincial covers all
                    return r.regionCode.startsWith(kabFilterVal);
                });
                if (!hasMatchingRegion) return false;
            }

            // Workload filter
            if (workloadFilterVal !== 'all') {
                if (workloadFilterVal === 'overloaded' && item.totalHH <= 800) return false;
                if (workloadFilterVal === 'medium' && (item.totalHH <= 500 || item.totalHH > 800)) return false;
                if (workloadFilterVal === 'light' && item.totalHH > 500) return false;
            }

            return true;
        });

        // Apply sort
        const col = window.petugasSort.column;
        const order = window.petugasSort.order === 'asc' ? 1 : -1;
        filteredData.sort((a, b) => {
            let valA = a[col];
            let valB = b[col];
            if (col === 'totalRegions') {
                valA = a.regions ? a.regions.length : 0;
                valB = b.regions ? b.regions.length : 0;
                return (valA - valB) * order;
            }
            if (col === 'workload' || col === 'totalHH') {
                valA = a.totalHH || 0;
                valB = b.totalHH || 0;
                return (valA - valB) * order;
            }
            if (typeof valA === 'string') {
                return (valA || '').localeCompare(valB || '') * order;
            }
            return ((valA || 0) - (valB || 0)) * order;
        });

        const totalItems = filteredData.length;
        const hasRoles = petugasData.some(item => typeof item.roleName === 'string' && item.roleName.trim() !== '' && item.roleName.trim() !== '-');

        // Hide or show Peran filter dropdown
        if (roleFilterEl) {
            roleFilterEl.style.display = hasRoles ? '' : 'none';
        }

        // Hide or show Peran table header
        const roleHeader = document.getElementById('petugas-sort-roleName')?.parentElement;
        if (roleHeader) {
            roleHeader.style.display = hasRoles ? '' : 'none';
        }

        if (totalItems === 0) {
            tbody.innerHTML = `<tr><td colspan="${hasRoles ? 6 : 5}" style="text-align: center; padding: 2rem; color: var(--text-secondary);">Tidak ada data petugas yang cocok.</td></tr>`;
            paginationInfo.innerText = `Menampilkan 0 - 0 dari 0 Petugas`;
            renderPetugasPaginationButtons(0);
            return;
        }

        const maxPage = Math.ceil(totalItems / petugasRowsPerPage);
        if (window.petugasCurrentPage > maxPage) window.petugasCurrentPage = maxPage;
        if (window.petugasCurrentPage < 1) window.petugasCurrentPage = 1;

        const startIdx = (window.petugasCurrentPage - 1) * petugasRowsPerPage;
        const endIdx = Math.min(startIdx + petugasRowsPerPage, totalItems);

        paginationInfo.innerText = `Menampilkan ${startIdx + 1} - ${endIdx} dari ${totalItems} Petugas`;

        const pageData = filteredData.slice(startIdx, endIdx);

        tbody.innerHTML = pageData.map((item, index) => {
            const rowNumber = startIdx + index + 1;

            const hl = (txt) => highlightText(txt, searchVal);

            const regions = item.regions || [];
            const limit = 2; // Show only 2 badges initially

            const visibleRegions = regions.slice(0, limit);
            const hiddenRegions = regions.slice(limit);

            const renderBadge = (r) => {
                const badgeTxt = r.regionName && r.regionName !== '-' ? r.regionName : 'LAINNYA';
                const codeTxt = r.regionCode ? ` (${r.regionCode})` : '';
                return `<span style="display: inline-flex; align-items: center; background: rgba(99, 102, 241, 0.08); color: var(--text-primary); border: 1px solid rgba(99, 102, 241, 0.2); padding: 0.2rem 0.6rem; border-radius: 1rem; font-size: 0.75rem; white-space: nowrap; margin: 0.15rem;">
                    <svg fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" style="width: 12px; height: 12px; margin-right: 0.35rem; color: var(--primary);" viewBox="0 0 24 24"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
                    ${hl(badgeTxt + codeTxt)}
                </span>`;
            };

            const visibleBadges = visibleRegions.map(r => renderBadge(r)).join('');

            let wilHtml = '';
            if (regions.length === 0) {
                wilHtml = '<span style="color:var(--text-muted); font-size:0.8rem;">Tidak ada wilayah tugas</span>';
            } else if (hiddenRegions.length === 0) {
                wilHtml = visibleBadges;
            } else {
                const hiddenBadges = hiddenRegions.map(r => renderBadge(r)).join('');
                wilHtml = `
                    <div style="display: flex; flex-wrap: wrap; align-items: center; gap: 0.25rem; width: 100%;">
                        ${visibleBadges}
                        <details class="regions-details" style="display: inline-block; outline: none; margin: 0.15rem; width: 100%;">
                            <summary style="list-style: none; outline: none; display: inline-flex; align-items: center; gap: 0.25rem; font-size: 0.72rem; font-weight: 700; color: var(--primary); cursor: pointer; user-select: none; padding: 0.2rem 0.5rem; background: rgba(99, 102, 241, 0.05); border-radius: 0.5rem; border: 1px dashed rgba(99, 102, 241, 0.3); transition: all 0.2s;">
                                <span>+${hiddenRegions.length} Wilayah Lainnya</span>
                                <svg class="chevron-icon" style="width: 10px; height: 10px; transition: transform 0.2s;" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7"></path></svg>
                            </summary>
                            <div style="display: flex; flex-wrap: wrap; gap: 0.15rem; margin-top: 0.35rem; padding: 0.35rem; background: rgba(0, 0, 0, 0.02); border-radius: 0.5rem; border: 1px solid var(--card-border);">
                                ${hiddenBadges}
                            </div>
                        </details>
                    </div>
                `;
            }

            // Calculate Sync Stats for this officer
            const syncStats = getOfficerSyncStats(item.regions);
            const syncProgressHtml = `
                <div style="display: flex; flex-direction: column; align-items: center; gap: 0.15rem; width: 100%;">
                    <div style="font-weight: 700; font-size: 0.85rem; color: ${parseFloat(syncStats.percentage) > 0 ? 'var(--color-delivered)' : 'var(--text-secondary)'};">
                        ${syncStats.synced} / ${syncStats.total} SLS
                    </div>
                    <div style="width: 100%; max-width: 120px; height: 5px; background: rgba(0,0,0,0.1); border-radius: 3px; overflow: hidden; display: inline-block;">
                        <div style="height: 100%; background: var(--color-delivered); width: ${syncStats.percentage}%;"></div>
                    </div>
                    <span style="font-size: 0.75rem; font-weight: 700; color: var(--text-secondary);">${syncStats.percentage}%</span>
                </div>
            `;

            // Workload display with warning if > 800
            let workloadBadge = '';
            if (item.totalHH > 800) {
                workloadBadge = `
                    <div style="display: flex; flex-direction: column; align-items: center; gap: 0.15rem;">
                        <span style="color: #ef4444; font-weight: 800; font-size: 0.9rem;">${new Intl.NumberFormat('id-ID').format(item.totalHH)} target</span>
                        <span style="background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.25); padding: 0.1rem 0.4rem; border-radius: 0.25rem; font-size: 0.65rem; font-weight: 700; letter-spacing: 0.02em;">⚠️ OVERLOAD</span>
                    </div>
                `;
            } else if (item.totalHH > 500) {
                workloadBadge = `
                    <div style="display: flex; flex-direction: column; align-items: center; gap: 0.15rem;">
                        <span style="color: #f59e0b; font-weight: 700; font-size: 0.85rem;">${new Intl.NumberFormat('id-ID').format(item.totalHH)} target</span>
                        <span style="background: rgba(245, 158, 11, 0.1); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.2); padding: 0.1rem 0.4rem; border-radius: 0.25rem; font-size: 0.65rem; font-weight: 700; letter-spacing: 0.02em;">SEDANG</span>
                    </div>
                `;
            } else {
                workloadBadge = `
                    <span style="color: var(--text-primary); font-weight: 600; font-size: 0.85rem;">${new Intl.NumberFormat('id-ID').format(item.totalHH)} target</span>
                `;
            }

            // Detect unassigned officers and check if they were ever assigned
            let unassignedBadgeHtml = '';
            if (!item.regions || item.regions.length === 0) {
                // Check if this officer appears in any SLS assignment data
                const officerEmail = (item.email || '').toLowerCase();
                const officerUsername = (item.username || '').toLowerCase();
                let wasEverAssigned = false;
                if (window.ASSIGN_SLS_DATA) {
                    wasEverAssigned = window.ASSIGN_SLS_DATA.some(sls => {
                        const assignedTo = (sls.assigned_to || sls.petugas || sls.officer_name || '').toLowerCase();
                        return assignedTo && (
                            assignedTo.includes(officerUsername) ||
                            assignedTo.includes(officerEmail) ||
                            (officerEmail && officerEmail.includes(assignedTo))
                        );
                    });
                }
                if (wasEverAssigned) {
                    unassignedBadgeHtml = `<span style="display: inline-block; margin-left: 0.5rem; padding: 0.15rem 0.5rem; border-radius: 0.4rem; background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.25); color: #f59e0b; font-size: 0.65rem; font-weight: 700; white-space: nowrap;">⚠️ Pernah Ditugaskan</span>`;
                } else {
                    unassignedBadgeHtml = `<span style="display: inline-block; margin-left: 0.5rem; padding: 0.15rem 0.5rem; border-radius: 0.4rem; background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.2); color: #f87171; font-size: 0.65rem; font-weight: 700; white-space: nowrap;">❌ Belum Ditugaskan</span>`;
                }
            }

            const escapedUser = item.username.replace(/[^a-zA-Z0-9]/g, '_');

            let waHtml = "";
            const emailClean = (item.email || '').toLowerCase().trim();
            if (window.PETUGAS_PHONES && window.PETUGAS_PHONES[emailClean]) {
                const phoneData = window.PETUGAS_PHONES[emailClean];
                if (phoneData.phone) {
                    const waLink = `https://wa.me/${phoneData.phone}`;
                    waHtml = `<a href="${waLink}" target="_blank" onclick="event.stopPropagation();" style="display: inline-flex; align-items: center; gap: 4px; margin-top: 4px; padding: 2px 8px; background: #25D366; color: white; border-radius: 12px; font-size: 0.7rem; font-weight: 600; text-decoration: none; width: fit-content; transition: opacity 0.2s;" onmouseover="this.style.opacity='0.8'" onmouseout="this.style.opacity='1'">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" stroke="none"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
                        Hubungi WA
                    </a>`;
                }
            }

            return `
                <tr onclick="window.togglePetugasRow(this, '${item.username}')" style="border-bottom: 1px solid var(--card-border); transition: background-color 0.2s; cursor: pointer;">
                    <td style="padding: 1rem; color: var(--text-secondary); text-align: center; font-weight: 500;">${rowNumber}</td>
                    <td style="padding: 1rem;">
                        <div style="display: flex; align-items: center; gap: 0.75rem;">
                            <div style="width: 32px; height: 32px; border-radius: 50%; background: var(--card-hover-bg); border: 1px solid var(--card-border); display: flex; align-items: center; justify-content: center; color: var(--text-secondary);">
                                <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" style="width: 16px; height: 16px;"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                            </div>
                            <div style="display: flex; flex-direction: column;">
                                <span style="font-weight: 600; color: var(--text-primary);">${hl(item.username || '-')}${unassignedBadgeHtml}</span>
                                <span style="font-size: 0.8rem; color: var(--text-secondary);">${hl(item.email || '-')}</span>
                                ${waHtml}
                            </div>
                        </div>
                    </td>
                    ${hasRoles ? `
                    <td style="padding: 1rem;">
                        <span style="display: inline-block; padding: 0.25rem 0.6rem; border-radius: 0.5rem; background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.2); color: #f59e0b; font-size: 0.75rem; font-weight: 700;">
                            ${hl(item.roleName || '-')}
                        </span>
                    </td>` : ''}
                    <td style="padding: 1rem; text-align: center;">
                        ${syncProgressHtml}
                    </td>
                    <td style="padding: 1rem; text-align: center;">
                        ${workloadBadge}
                    </td>
                    <td style="padding: 1rem;">
                        <div style="display: flex; flex-wrap: wrap; gap: 0.25rem;">
                            ${wilHtml}
                        </div>
                    </td>
                </tr>
                <tr id="petugas-detail-${escapedUser}" style="display: none; background: rgba(0,0,0,0.02); border-bottom: 1px solid var(--card-border);">
                    <td colspan="${hasRoles ? 6 : 5}" style="padding: 1.25rem 1.5rem;">
                        <div style="background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 0.75rem; padding: 1.25rem; box-shadow: var(--shadow-sm);">
                            <h5 style="margin-top: 0; margin-bottom: 0.75rem; color: var(--text-primary); font-family: 'Outfit', sans-serif; font-size: 0.95rem; font-weight: 700; display: flex; align-items: center; gap: 0.5rem;">
                                <svg fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24" style="width: 14px; height: 14px; color: var(--primary);"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="9" y1="3" x2="9" y2="21"></line></svg>
                                Rincian Wilayah Tugas (SLS) untuk ${item.username}
                            </h5>
                            <div style="overflow-x: auto;">
                                <table style="width: 100%; border-collapse: collapse; font-family: 'Outfit', sans-serif; font-size: 0.8rem;">
                                    <thead>
                                        <tr style="border-bottom: 2px solid var(--card-border); text-align: left; background: rgba(0,0,0,0.01);">
                                            <th style="padding: 0.5rem; width: 40px; text-align: center; color: var(--text-secondary);">No</th>
                                            <th style="padding: 0.5rem; width: 130px; color: var(--text-secondary);">Kode SLS</th>
                                            <th style="padding: 0.5rem; color: var(--text-secondary);">Nama SLS</th>
                                            <th style="padding: 0.5rem; color: var(--text-secondary);">Desa / Kelurahan</th>
                                            <th style="padding: 0.5rem; color: var(--text-secondary);">Kecamatan</th>
                                            <th style="padding: 0.5rem; color: var(--text-secondary);">Kabupaten</th>
                                            <th style="padding: 0.5rem; text-align: right; width: 80px; color: var(--text-secondary);">Target HH</th>
                                            <th style="padding: 0.5rem; text-align: center; width: 220px; color: var(--text-secondary);">Progres Pengerjaan</th>
                                        </tr>
                                    </thead>
                                    <tbody id="petugas-sls-tbody-${escapedUser}">
                                        <tr><td colspan="8" style="text-align: center; padding: 1rem; color: var(--text-secondary);">Memuat rincian SLS...</td></tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');

        renderPetugasPaginationButtons(maxPage);
    };

    // Superset Sync table rendering
    // Superset Sync table rendering
    window.syncCurrentPage = 1;
    let SYNC_ITEMS_PER_PAGE = 25;
    window.syncSort = { column: 'kab_name', order: 'asc' };

    window.changeSyncLimit = function (val) {
        SYNC_ITEMS_PER_PAGE = parseInt(val) || 25;
        window.syncCurrentPage = 1;
        renderSyncTable();
    };

    window.sortSyncTable = function (column) {
        const current = window.syncSort;
        if (current.column === column) {
            current.order = current.order === 'asc' ? 'desc' : 'asc';
        } else {
            current.column = column;
            current.order = 'asc';
        }
        window.syncCurrentPage = 1; // reset page on sort
        renderSyncTable();
    };

    let isSyncFiltersPopulated = false;
    function populateSyncFilters() {
        if (!window.ASSIGN_SLS_DATA || window.ASSIGN_SLS_DATA.length === 0 || isSyncFiltersPopulated) return;

        const kabSelect = document.getElementById('sync-kab-filter');
        if (!kabSelect) return;

        // Extract unique regions
        const uniqueKabs = [...new Set(window.ASSIGN_SLS_DATA.map(i => i.kab_name))].sort();

        kabSelect.innerHTML = '<option value="all">Semua Kabupaten</option>' +
            uniqueKabs.map(k => `<option value="${k}">${k}</option>`).join('');

        // Register cascade change listeners
        kabSelect.addEventListener('change', () => {
            updateSyncKecOptions();
            window.syncCurrentPage = 1;
            renderSyncTable();
        });

        const kecSelect = document.getElementById('sync-kec-filter');
        if (kecSelect) {
            kecSelect.addEventListener('change', () => {
                updateSyncDesaOptions();
                window.syncCurrentPage = 1;
                renderSyncTable();
            });
        }

        const desaSelect = document.getElementById('sync-desa-filter');
        if (desaSelect) {
            desaSelect.addEventListener('change', () => {
                updateSyncPetugasOptions();
                window.syncCurrentPage = 1;
                renderSyncTable();
            });
        }

        const petugasSelect = document.getElementById('sync-petugas-filter');
        if (petugasSelect) {
            petugasSelect.addEventListener('change', () => {
                window.syncCurrentPage = 1;
                renderSyncTable();
            });
        }

        const statusSelect = document.getElementById('sync-status-filter');
        if (statusSelect) {
            statusSelect.addEventListener('change', () => {
                window.syncCurrentPage = 1;
                renderSyncTable();
            });
        }

        isSyncFiltersPopulated = true;
        updateSyncKecOptions();
    }

    function updateSyncKecOptions() {
        const kabVal = document.getElementById('sync-kab-filter')?.value || 'all';
        const kecSelect = document.getElementById('sync-kec-filter');
        if (!kecSelect) return;

        if (kabVal === 'all') {
            kecSelect.innerHTML = '<option value="all">Semua Kecamatan</option>';
            kecSelect.disabled = true;
            updateSyncDesaOptions();
            return;
        }

        kecSelect.disabled = false;
        const filteredSls = window.ASSIGN_SLS_DATA.filter(i => i.kab_name === kabVal);
        const uniqueKecs = [...new Set(filteredSls.map(i => i.kec_name))].sort();

        kecSelect.innerHTML = '<option value="all">Semua Kecamatan</option>' +
            uniqueKecs.map(k => `<option value="${k}">${k}</option>`).join('');

        updateSyncDesaOptions();
    }

    function updateSyncDesaOptions() {
        const kabFilterEl = document.getElementById('sync-kab-filter');
        const kecFilterEl = document.getElementById('sync-kec-filter');
        if (!kabFilterEl || !kecFilterEl) return;
        const kabVal = kabFilterEl.value;
        const kecVal = kecFilterEl.value;

        const desaSelect = document.getElementById('sync-desa-filter');
        if (!desaSelect) return;

        if (kecVal === 'all') {
            desaSelect.innerHTML = '<option value="all">Semua Desa</option>';
            desaSelect.disabled = true;
            updateSyncPetugasOptions();
            return;
        }

        desaSelect.disabled = false;
        const filteredSls = window.ASSIGN_SLS_DATA.filter(i => i.kab_name === kabVal && i.kec_name === kecVal);
        const uniqueDesas = [...new Set(filteredSls.map(i => i.desa_name))].sort();

        desaSelect.innerHTML = '<option value="all">Semua Desa</option>' +
            uniqueDesas.map(d => `<option value="${d}">${d}</option>`).join('');

        updateSyncPetugasOptions();
    }

    function updateSyncPetugasOptions() {
        const kabVal = document.getElementById('sync-kab-filter')?.value || 'all';
        const kecVal = document.getElementById('sync-kec-filter')?.value || 'all';
        const desaVal = document.getElementById('sync-desa-filter')?.value || 'all';
        const petugasSelect = document.getElementById('sync-petugas-filter');
        if (!petugasSelect) return;

        const filtered = window.ASSIGN_SLS_DATA.filter(item => {
            if (kabVal !== 'all' && item.kab_name !== kabVal) return false;
            if (kecVal !== 'all' && item.kec_name !== kecVal) return false;
            if (desaVal !== 'all' && item.desa_name !== desaVal) return false;
            return true;
        });

        const officerSet = new Set();
        filtered.forEach(item => {
            if (item.officers && Array.isArray(item.officers)) {
                item.officers.forEach(ofc => {
                    if (ofc && ofc !== '-') {
                        officerSet.add(ofc);
                    }
                });
            }
        });

        const sortedOfficers = Array.from(officerSet).sort();
        const currentSelected = petugasSelect.value;

        petugasSelect.innerHTML = '<option value="all">Semua Petugas</option>' +
            sortedOfficers.map(o => `<option value="${o}">${o}</option>`).join('');

        if (sortedOfficers.includes(currentSelected)) {
            petugasSelect.value = currentSelected;
        } else {
            petugasSelect.value = 'all';
        }
    }

    function renderSyncTableHeaders() {
        const headerRow = document.getElementById('sync-table-headers');
        if (!headerRow) return;

        const getIcon = (col) => {
            if (window.syncSort.column !== col) return ' ↕';
            return window.syncSort.order === 'asc' ? ' ▲' : ' ▼';
        };

        headerRow.innerHTML = `
            <th style="width: 60px; text-align: center;">No</th>
            <th onclick="window.sortSyncTable('kab_name')" style="font-family: 'Outfit', sans-serif; cursor: pointer; user-select: none;">Kabupaten${getIcon('kab_name')}</th>
            <th onclick="window.sortSyncTable('kec_name')" style="font-family: 'Outfit', sans-serif; cursor: pointer; user-select: none;">Kecamatan${getIcon('kec_name')}</th>
            <th onclick="window.sortSyncTable('desa_name')" style="font-family: 'Outfit', sans-serif; cursor: pointer; user-select: none;">Desa${getIcon('desa_name')}</th>
            <th onclick="window.sortSyncTable('sls_name')" style="font-family: 'Outfit', sans-serif; cursor: pointer; user-select: none;">Kode & Nama SLS${getIcon('sls_name')}</th>
            <th onclick="window.sortSyncTable('assign')" style="font-family: 'Outfit', sans-serif; text-align: center; cursor: pointer; user-select: none; width: 130px;">Assign (Real-time)${getIcon('assign')}</th>
            <th onclick="window.sortSyncTable('sync_count')" style="font-family: 'Outfit', sans-serif; text-align: center; cursor: pointer; user-select: none; width: 130px;">Sync (Real-time)${getIcon('sync_count')}</th>
            <th onclick="window.sortSyncTable('unsynced')" style="font-family: 'Outfit', sans-serif; text-align: center; color: #f59e0b; cursor: pointer; user-select: none; width: 130px;">Belum Sync${getIcon('unsynced')}</th>
            <th onclick="window.sortSyncTable('sync_status')" style="font-family: 'Outfit', sans-serif; text-align: center; cursor: pointer; user-select: none; width: 120px;">Status${getIcon('sync_status')}</th>
        `;

        // Populate global sync
        updateGlobalSyncProgress();
    }

    window.renderSyncTable = function () {
        const tbody = document.getElementById('sync-table-body');
        const paginationInfo = document.getElementById('sync-pagination-info');
        if (!tbody || !paginationInfo) return;

        if (!window.ASSIGN_SLS_DATA || window.ASSIGN_SLS_DATA.length === 0) {
            tbody.innerHTML = `<tr><td colspan="10" style="text-align: center; padding: 2rem; color: var(--text-secondary);">Data SLS belum tersedia. Pastikan sinkronisasi data sedang berjalan.</td></tr>`;
            paginationInfo.innerText = `Menampilkan 0 - 0 dari 0 SLS`;
            return;
        }

        populateSyncFilters();

        const searchInputEl = document.getElementById('sync-search-input');
        const searchVal = searchInputEl ? searchInputEl.value.toLowerCase().trim() : '';
        const kabFilter = document.getElementById('sync-kab-filter')?.value || 'all';
        const kecFilter = document.getElementById('sync-kec-filter')?.value || 'all';
        const desaFilter = document.getElementById('sync-desa-filter')?.value || 'all';
        const petugasFilter = document.getElementById('sync-petugas-filter')?.value || 'all';
        const statusFilter = document.getElementById('sync-status-filter')?.value || 'all';

        // Map directly from ASSIGN_SLS_DATA (Real-time)
        const joinedData = window.ASSIGN_SLS_DATA.map(item => {
            return {
                kab_name: item.kab_name || '',
                kec_name: item.kec_name || '',
                desa_name: item.desa_name || '',
                sls_code: item.sls_code || '',
                sls_name: item.sls_name || '',
                assign: item.assigned || 0,
                sync_count: item.sync_count || 0,
                unsynced: Math.max(0, (item.assigned || 0) - (item.sync_count || 0)),
                sync_status: (item.sync_count || 0) > 0 ? 'synced' : 'not_synced',
                officers: item.officers || []
            };
        });

        // Filter
        let filtered = joinedData.filter(item => {
            if (kabFilter !== 'all' && item.kab_name !== kabFilter) return false;
            if (kecFilter !== 'all' && item.kec_name !== kecFilter) return false;
            if (desaFilter !== 'all' && item.desa_name !== desaFilter) return false;

            // Exclude dummy SLS
            if (item.desa_name === '-' || item.sls_name === '-') return false;

            // Petugas filter
            if (petugasFilter !== 'all') {
                if (!item.officers || !item.officers.includes(petugasFilter)) return false;
            }

            if (statusFilter !== 'all' && item.sync_status !== statusFilter) return false;

            if (searchVal) {
                const officersStr = (item.officers || []).join(' ');
                const matchText = (item.kab_name + ' ' + item.kec_name + ' ' + item.desa_name + ' ' + item.sls_name + ' ' + item.sls_code + ' ' + officersStr).toLowerCase();
                if (!matchText.includes(searchVal)) return false;
            }
            return true;
        });

        const totalItems = filtered.length;
        if (totalItems === 0) {
            tbody.innerHTML = `<tr><td colspan="10" style="text-align: center; padding: 2rem; color: var(--text-secondary);">Tidak ada data SLS Sync yang cocok dengan filter.</td></tr>`;
            paginationInfo.innerText = `Menampilkan 0 - 0 dari 0 SLS`;
            renderSyncPaginationButtons(0);
            return;
        }

        // Sort
        const col = window.syncSort.column;
        const order = window.syncSort.order === 'asc' ? 1 : -1;
        filtered.sort((a, b) => {
            let valA = a[col];
            let valB = b[col];
            if (typeof valA === 'string') {
                return valA.localeCompare(valB) * order;
            }
            return ((valA || 0) - (valB || 0)) * order;
        });

        // Render headers
        renderSyncTableHeaders();

        const maxPage = Math.ceil(totalItems / SYNC_ITEMS_PER_PAGE);
        if (window.syncCurrentPage > maxPage) window.syncCurrentPage = maxPage;
        if (window.syncCurrentPage < 1) window.syncCurrentPage = 1;

        const startIdx = (window.syncCurrentPage - 1) * SYNC_ITEMS_PER_PAGE;
        const endIdx = Math.min(startIdx + SYNC_ITEMS_PER_PAGE, totalItems);

        paginationInfo.innerText = `Menampilkan ${startIdx + 1} - ${endIdx} dari ${totalItems} SLS`;

        const pageData = filtered.slice(startIdx, endIdx);

        tbody.innerHTML = pageData.map((item, index) => {
            const rowNumber = startIdx + index + 1;
            const hl = (txt) => highlightText(txt, searchVal);

            const isSynced = item.sync_count > 0;
            const statusBadge = isSynced
                ? `<span style="display: inline-block; padding: 0.15rem 0.5rem; border-radius: 0.25rem; background: rgba(16, 185, 129, 0.1); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.2); font-size: 0.75rem; font-weight: 700;">SYNCED</span>`
                : `<span style="display: inline-block; padding: 0.15rem 0.5rem; border-radius: 0.25rem; background: rgba(239, 68, 68, 0.1); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.2); font-size: 0.75rem; font-weight: 700;">NOT SYNCED</span>`;

            const officers = item.officers && item.officers.length > 0 ? item.officers.join(', ') : '-';

            return `
                <tr style="border-bottom: 1px solid var(--card-border); transition: background-color 0.15s;">
                    <td style="padding: 0.75rem 1rem; text-align: center; color: var(--text-secondary); font-weight: 500;">${rowNumber}</td>
                    <td style="padding: 1rem; color: var(--text-secondary); font-weight: 500;">${hl(item.kab_name)}</td>
                    <td style="padding: 1rem; color: var(--text-secondary);">${hl(item.kec_name)}</td>
                    <td style="padding: 1rem; color: var(--text-secondary);">${hl(item.desa_name)}</td>
                    <td style="padding: 1rem; font-weight: 600; color: var(--text);">${hl(item.sls_name)} 
                        <span style="font-size: 0.75rem; font-weight: 400; color: var(--text-secondary); display:block;">${hl(item.sls_code)}</span>
                        <span style="font-size: 0.75rem; font-weight: 400; color: var(--text-secondary); display:block; margin-top: 0.25rem;">Petugas: ${hl(officers)}</span>
                    </td>
                    <td style="padding: 0.75rem 1rem; text-align: center; font-family: monospace; font-weight: 700; color: var(--text-secondary);">${item.assign}</td>
                    <td style="padding: 0.75rem 1rem; text-align: center; font-family: monospace; font-weight: 700; color: ${isSynced ? '#10b981' : 'var(--text-secondary)'};">${item.sync_count}</td>
                    <td style="padding: 0.75rem 1rem; text-align: center; font-family: monospace; font-weight: 700; color: #f59e0b;">${item.unsynced}</td>
                    <td style="padding: 0.75rem 1rem; text-align: center;">${statusBadge}</td>
                </tr>
            `;
        }).join('');

        renderSyncPaginationButtons(maxPage);
    };

    window.downloadSyncCSV = function () {
        if (!window.ASSIGN_SLS_DATA || window.ASSIGN_SLS_DATA.length === 0) {
            alert("Tidak ada data SLS untuk diunduh.");
            return;
        }

        const searchInputEl = document.getElementById('sync-search-input');
        const searchVal = searchInputEl ? searchInputEl.value.toLowerCase().trim() : '';
        const kabFilter = document.getElementById('sync-kab-filter')?.value || 'all';
        const kecFilter = document.getElementById('sync-kec-filter')?.value || 'all';
        const desaFilter = document.getElementById('sync-desa-filter')?.value || 'all';
        const petugasFilter = document.getElementById('sync-petugas-filter')?.value || 'all';
        const statusFilter = document.getElementById('sync-status-filter')?.value || 'all';

        const joinedData = window.ASSIGN_SLS_DATA.map(item => {
            return {
                kab_name: item.kab_name || '',
                kec_name: item.kec_name || '',
                desa_name: item.desa_name || '',
                sls_code: item.sls_code || '',
                sls_name: item.sls_name || '',
                assign: item.assigned || 0,
                sync_count: item.sync_count || 0,
                unsynced: Math.max(0, (item.assigned || 0) - (item.sync_count || 0)),
                sync_status: (item.sync_count || 0) > 0 ? 'synced' : 'not_synced',
                officers: item.officers || []
            };
        });

        let filtered = joinedData.filter(item => {
            if (kabFilter !== 'all' && item.kab_name !== kabFilter) return false;
            if (kecFilter !== 'all' && item.kec_name !== kecFilter) return false;
            if (desaFilter !== 'all' && item.desa_name !== desaFilter) return false;

            // Exclude dummy SLS
            if (item.desa_name === '-' || item.sls_name === '-') return false;

            // Petugas filter
            if (petugasFilter !== 'all') {
                if (!item.officers || !item.officers.includes(petugasFilter)) return false;
            }

            if (statusFilter !== 'all' && item.sync_status !== statusFilter) return false;

            if (searchVal) {
                const officersStr = (item.officers || []).join(' ');
                const matchText = (item.kab_name + ' ' + item.kec_name + ' ' + item.desa_name + ' ' + item.sls_name + ' ' + item.sls_code + ' ' + officersStr).toLowerCase();
                if (!matchText.includes(searchVal)) return false;
            }
            return true;
        });

        const col = window.syncSort.column;
        const order = window.syncSort.order === 'asc' ? 1 : -1;
        filtered.sort((a, b) => {
            let valA = a[col];
            let valB = b[col];
            if (typeof valA === 'string') {
                return valA.localeCompare(valB) * order;
            }
            return ((valA || 0) - (valB || 0)) * order;
        });

        const headers = ["Kabupaten", "Kecamatan", "Desa", "Kode SLS", "Nama SLS", "Assign (Real-time)", "Sync (Real-time)", "Belum Sync", "Status", "Petugas"];
        const rows = filtered.map(item => [
            item.kab_name,
            item.kec_name,
            item.desa_name,
            item.sls_code,
            item.sls_name,
            item.assign,
            item.sync_count,
            item.unsynced,
            item.sync_status === 'synced' ? 'SYNCED' : 'NOT SYNCED',
            item.officers.join(', ')
        ]);

        let csvContent = "data:text/csv;charset=utf-8,\uFEFF";
        csvContent += [headers.join(",")].concat(rows.map(r => r.map(val => `"${String(val).replace(/"/g, '""')}"`).join(","))).join("\n");

        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);

        const activeSubtab = localStorage.getItem('active_assign_subtab') || 'se2026';
        link.setAttribute("download", `rincian_sync_capi_realtime_${activeSubtab}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    function renderSyncPaginationButtons(maxPage) {
        const btnContainer = document.getElementById('sync-pagination-buttons');
        if (!btnContainer) return;
        btnContainer.innerHTML = '';
        if (maxPage <= 1) return;

        const btnStyle = `padding: 0.4rem 0.75rem; font-size: 0.8rem; font-weight: 600; border-radius: 0.5rem; border: 1px solid var(--card-border); background-color: var(--card-bg); color: var(--text); cursor: pointer; transition: all 0.2s;`;
        const activeStyle = `padding: 0.4rem 0.75rem; font-size: 0.8rem; font-weight: 700; border-radius: 0.5rem; border: 1px solid transparent; background-color: var(--primary); color: white; cursor: default;`;

        // Prev button
        if (window.syncCurrentPage > 1) {
            const prevBtn = document.createElement('button');
            prevBtn.innerHTML = '&lt;';
            prevBtn.style.cssText = btnStyle;
            prevBtn.addEventListener('click', () => {
                window.syncCurrentPage--;
                renderSyncTable();
            });
            btnContainer.appendChild(prevBtn);
        }

        // Logic to display limited page range
        let startPage = Math.max(1, window.syncCurrentPage - 2);
        let endPage = Math.min(maxPage, window.syncCurrentPage + 2);

        if (startPage > 1) {
            const page1 = document.createElement('button');
            page1.textContent = '1';
            page1.style.cssText = btnStyle;
            page1.addEventListener('click', () => {
                window.syncCurrentPage = 1;
                renderSyncTable();
            });
            btnContainer.appendChild(page1);

            if (startPage > 2) {
                const dots = document.createElement('span');
                dots.textContent = '...';
                dots.style.cssText = 'color: var(--text-secondary); font-size: 0.8rem; padding: 0 0.25rem;';
                btnContainer.appendChild(dots);
            }
        }

        for (let i = startPage; i <= endPage; i++) {
            const btn = document.createElement('button');
            btn.textContent = i;
            if (i === window.syncCurrentPage) {
                btn.style.cssText = activeStyle;
            } else {
                btn.style.cssText = btnStyle;
                btn.addEventListener('click', () => {
                    window.syncCurrentPage = i;
                    renderSyncTable();
                });
            }
            btnContainer.appendChild(btn);
        }

        if (endPage < maxPage) {
            if (endPage < maxPage - 1) {
                const dots = document.createElement('span');
                dots.textContent = '...';
                dots.style.cssText = 'color: var(--text-secondary); font-size: 0.8rem; padding: 0 0.25rem;';
                btnContainer.appendChild(dots);
            }

            const pageLast = document.createElement('button');
            pageLast.textContent = maxPage;
            pageLast.style.cssText = btnStyle;
            pageLast.addEventListener('click', () => {
                window.syncCurrentPage = maxPage;
                renderSyncTable();
            });
            btnContainer.appendChild(pageLast);
        }

        if (window.syncCurrentPage < maxPage) {
            const nextBtn = document.createElement('button');
            nextBtn.innerHTML = '&gt;';
            nextBtn.style.cssText = btnStyle;
            nextBtn.addEventListener('click', () => {
                window.syncCurrentPage++;
                renderSyncTable();
            });
            btnContainer.appendChild(nextBtn);
        }
    }

    function renderPetugasPaginationButtons(maxPage) {
        const btnContainer = document.getElementById('petugas-pagination-buttons');
        if (!btnContainer) return;
        btnContainer.innerHTML = '';

        const btnStyle = `padding: 0.4rem 0.75rem; font-size: 0.8rem; font-weight: 600; border-radius: 0.5rem; border: 1px solid var(--card-border); background-color: var(--card-bg); color: var(--text); cursor: pointer; transition: all 0.2s;`;
        const activeStyle = `padding: 0.4rem 0.75rem; font-size: 0.8rem; font-weight: 700; border-radius: 0.5rem; border: 1px solid transparent; background-color: var(--primary); color: white; cursor: default;`;

        if (window.petugasCurrentPage > 1) {
            const prevBtn = document.createElement('button');
            prevBtn.innerHTML = '&lt;';
            prevBtn.style.cssText = btnStyle;
            prevBtn.addEventListener('click', () => {
                window.petugasCurrentPage--;
                renderPetugasTable();
            });
            btnContainer.appendChild(prevBtn);
        }

        let startPage = Math.max(1, window.petugasCurrentPage - 2);
        let endPage = Math.min(maxPage, window.petugasCurrentPage + 2);

        if (startPage > 1) {
            const page1 = document.createElement('button');
            page1.textContent = '1';
            page1.style.cssText = btnStyle;
            page1.addEventListener('click', () => { window.petugasCurrentPage = 1; renderPetugasTable(); });
            btnContainer.appendChild(page1);

            if (startPage > 2) {
                const dots = document.createElement('span');
                dots.textContent = '...';
                dots.style.cssText = 'color: var(--text-secondary); font-size: 0.8rem; padding: 0 0.25rem;';
                btnContainer.appendChild(dots);
            }
        }

        for (let i = startPage; i <= endPage; i++) {
            const btn = document.createElement('button');
            btn.textContent = i;
            if (i === window.petugasCurrentPage) {
                btn.style.cssText = activeStyle;
            } else {
                btn.style.cssText = btnStyle;
                btn.addEventListener('click', () => { window.petugasCurrentPage = i; renderPetugasTable(); });
            }
            btnContainer.appendChild(btn);
        }

        if (endPage < maxPage) {
            if (endPage < maxPage - 1) {
                const dots = document.createElement('span');
                dots.textContent = '...';
                dots.style.cssText = 'color: var(--text-secondary); font-size: 0.8rem; padding: 0 0.25rem;';
                btnContainer.appendChild(dots);
            }

            const pageLast = document.createElement('button');
            pageLast.textContent = maxPage;
            pageLast.style.cssText = btnStyle;
            pageLast.addEventListener('click', () => { window.petugasCurrentPage = maxPage; renderPetugasTable(); });
            btnContainer.appendChild(pageLast);
        }

        if (window.petugasCurrentPage < maxPage) {
            const nextBtn = document.createElement('button');
            nextBtn.innerHTML = '&gt;';
            nextBtn.style.cssText = btnStyle;
            nextBtn.addEventListener('click', () => {
                window.petugasCurrentPage++;
                renderPetugasTable();
            });
            btnContainer.appendChild(nextBtn);
        }
    }

    // --- CSV DOWNLOAD UTILITIES ---
    function exportToCSV(filename, headers, rows) {
        let csvContent = "\ufeff"; // BOM for Excel UTF-8 support
        csvContent += headers.map(h => `"${h.replace(/"/g, '""')}"`).join(",") + "\n";

        rows.forEach(row => {
            csvContent += row.map(cell => {
                const str = String(cell === null || cell === undefined ? "" : cell);
                return `"${str.replace(/"/g, '""')}"`;
            }).join(",") + "\n";
        });

        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.setAttribute("href", url);
        link.setAttribute("download", filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    window.downloadKabSummaryCSV = function () {
        const activeSubtab = localStorage.getItem('active_assign_subtab') || 'se2026';
        const rawData = window.ASSIGN_DATA || [];
        if (rawData.length === 0) {
            alert("Tidak ada data kabupaten untuk diunduh.");
            return;
        }

        // Aggregate SLS stats per kabupaten for %assign SLS and %sync
        const slsStatsByKab = {};
        rawData.forEach(d => { slsStatsByKab[d.kode_kab] = { total: 0, assigned: 0, synced: 0 }; });
        if (window.ASSIGN_SLS_DATA && window.ASSIGN_SLS_DATA.length > 0) {
            window.ASSIGN_SLS_DATA.forEach(sls => {
                const code = sls.sls_code || sls.sls_id;
                const kodeKab = code ? code.substring(0, 4) : '';
                if (kodeKab && slsStatsByKab[kodeKab]) {
                    slsStatsByKab[kodeKab].total++;
                    if ((sls.assigned || 0) > 0) slsStatsByKab[kodeKab].assigned++;
                    if ((sls.sync_count || 0) > 0) slsStatsByKab[kodeKab].synced++;
                }
            });
        } else if (window.SUPERSET_SYNC_SLS_DATA) {
            window.SUPERSET_SYNC_SLS_DATA.forEach(sls => {
                const code = sls.sls_code || sls.sls_id;
                const kodeKab = code ? code.substring(0, 4) : '';
                if (kodeKab && slsStatsByKab[kodeKab]) {
                    slsStatsByKab[kodeKab].total++;
                    slsStatsByKab[kodeKab].assigned++;
                    if ((sls.sync_count || 0) > 0) slsStatsByKab[kodeKab].synced++;
                }
            });
        }

        const headers = ["No", "Kode Kabupaten", "Kabupaten/Kota", "Total Target", "Sudah Ditugaskan", "Belum Ditugaskan", "% Assign HH", "% Assign SLS", "% Sync SLS"];
        let totalUsaha = 0, totalSudah = 0, totalBelum = 0;
        let totalSlsTotal = 0, totalSlsAssigned = 0, totalSlsSynced = 0;

        const rows = rawData.map((d, idx) => {
            const total = d.total || 0;
            const assigned = d.assigned || 0;
            const unassigned = d.have_not_assigned || 0;
            totalUsaha += total;
            totalSudah += assigned;
            totalBelum += unassigned;
            const pct = floorPct(assigned, total);
            const name = d.nama_kab.replace(/\[\d+\]\s*/, '').trim().toUpperCase();

            const slsStats = slsStatsByKab[d.kode_kab] || { total: 0, assigned: 0, synced: 0 };
            totalSlsTotal += slsStats.total;
            totalSlsAssigned += slsStats.assigned;
            totalSlsSynced += slsStats.synced;
            const pctSlsAssign = floorPct(slsStats.assigned, slsStats.total);
            const pctSlsSync = floorPct(slsStats.synced, slsStats.total);

            return [idx + 1, d.kode_kab, name, total, assigned, unassigned, pct, pctSlsAssign, pctSlsSync];
        });

        // Add total row
        const totalPct = floorPct(totalSudah, totalUsaha);
        const totalPctSlsAssign = floorPct(totalSlsAssigned, totalSlsTotal);
        const totalPctSlsSync = floorPct(totalSlsSynced, totalSlsTotal);
        rows.push(["", "", "TOTAL", totalUsaha, totalSudah, totalBelum, totalPct, totalPctSlsAssign, totalPctSlsSync]);

        const prefix = activeSubtab === 'ub' ? 'UB' : 'SE2026';
        exportToCSV(`rekap_kabupaten_${prefix.toLowerCase()}.csv`, headers, rows);
    };

    window.downloadSlsCSV = function () {
        const activeSubtab = localStorage.getItem('active_assign_subtab') || 'se2026';
        const slsData = window.ASSIGN_SLS_DATA || [];
        if (slsData.length === 0) {
            alert("Tidak ada data SLS untuk diunduh.");
            return;
        }

        // Apply filters exactly like renderSlsTable
        const searchInput = document.getElementById('sls-search-input');
        const searchVal = searchInput ? searchInput.value.toLowerCase().trim() : '';
        const kabVal = document.getElementById('sls-kab-filter') ? document.getElementById('sls-kab-filter').value : 'all';
        const kecVal = document.getElementById('sls-kec-filter') ? document.getElementById('sls-kec-filter').value : 'all';
        const desaVal = document.getElementById('sls-desa-filter') ? document.getElementById('sls-desa-filter').value : 'all';
        const assignVal = document.getElementById('sls-assignment-filter') ? document.getElementById('sls-assignment-filter').value : 'all';

        let filtered = slsData.filter(item => {
            if (kabVal !== 'all' && item.kab_name && !item.kab_name.includes(kabVal)) return false;
            if (kecVal !== 'all' && item.kec_name !== kecVal) return false;
            if (desaVal !== 'all' && item.desa_name !== desaVal) return false;

            // Exclude dummy SLS
            if (item.desa_name === '-' || item.sls_name === '-') return false;

            if (assignVal !== 'all') {
                if (assignVal === 'fully_assigned' && item.unassigned !== 0) return false;
                if (assignVal === 'unassigned' && item.assigned !== 0) return false;
                if (assignVal === 'partially_assigned' && (item.assigned === 0 || item.unassigned === 0)) return false;
            }

            if (searchVal) {
                const matchText = (item.kab_name + ' ' + item.kec_name + ' ' + item.desa_name + ' ' + item.sls_name + ' ' + item.sls_code + ' ' + (item.officers || []).join(' ')).toLowerCase();
                if (!matchText.includes(searchVal)) return false;
            }
            return true;
        });

        // Apply sort
        const col = window.slsSort.column;
        const order = window.slsSort.order === 'asc' ? 1 : -1;
        filtered.sort((a, b) => {
            let valA = a[col];
            let valB = b[col];
            if (typeof valA === 'string') {
                return valA.localeCompare(valB) * order;
            }
            return ((valA || 0) - (valB || 0)) * order;
        });

        const headers = ["Kabupaten", "Kecamatan", "Desa", "Kode SLS", "Nama SLS", "Total Target", "Ditugaskan", "Belum Ditugaskan", "Status", "Petugas"];
        const rows = filtered.map(item => {
            let status = 'Sebagian Ditugaskan';
            if (item.unassigned === 0) status = 'Sudah Ditugaskan';
            else if (item.assigned === 0) status = 'Belum Ditugaskan';

            const officers = item.officers && item.officers.length > 0 ? item.officers.join(', ') : '-';
            return [item.kab_name, item.kec_name, item.desa_name, item.sls_code, item.sls_name, item.total, item.assigned, item.unassigned, status, officers];
        });

        const prefix = activeSubtab === 'ub' ? 'UB' : 'SE2026';
        exportToCSV(`rincian_sls_${prefix.toLowerCase()}.csv`, headers, rows);
    };

    window.downloadPetugasCSV = function () {
        const activeSubtab = localStorage.getItem('active_assign_subtab') || 'se2026';
        const petugasData = window.PETUGAS_DATA || [];
        if (petugasData.length === 0) {
            alert("Tidak ada data petugas untuk diunduh.");
            return;
        }

        const searchInputEl = document.getElementById('petugas-search-input');
        const searchVal = searchInputEl ? searchInputEl.value.toLowerCase().trim() : '';

        const roleFilterEl = document.getElementById('petugas-role-filter');
        const roleFilterVal = roleFilterEl ? roleFilterEl.value : 'all';

        const kabFilterEl = document.getElementById('petugas-kab-filter');
        const kabFilterVal = kabFilterEl ? kabFilterEl.value : 'all';

        const workloadFilterEl = document.getElementById('petugas-workload-filter');
        const workloadFilterVal = workloadFilterEl ? workloadFilterEl.value : 'all';

        // Precalculate workload (totalHH)
        const slsTotalMap = {};
        if (window.ASSIGN_SLS_DATA) {
            window.ASSIGN_SLS_DATA.forEach(sls => {
                const code = sls.sls_code || sls.sls_id;
                if (code) {
                    slsTotalMap[code] = sls.total || 0;
                }
            });
        }
        petugasData.forEach(item => {
            let totalHH = 0;
            if (item.regions && item.regions.length > 0) {
                item.regions.forEach(reg => {
                    const code = reg.regionCode || '';
                    const slsCode = code.length === 16 ? code.substring(0, 14) : code;
                    totalHH += (slsTotalMap[slsCode] || 0);
                });
            }
            item.totalHH = totalHH;
        });

        let filteredData = petugasData.filter(item => {
            if (searchVal) {
                const uNameStr = item.username || '';
                const emailStr = item.email || '';
                const roleStr = item.roleName || '';
                const regionsStr = (item.regions || []).map(r => r.regionName).join(' ');
                const matchText = (uNameStr + ' ' + emailStr + ' ' + roleStr + ' ' + regionsStr).toLowerCase();
                if (!matchText.includes(searchVal)) return false;
            }

            if (roleFilterVal !== 'all' && item.roleName !== roleFilterVal) return false;

            if (kabFilterVal !== 'all') {
                const hasMatchingRegion = (item.regions || []).some(r => {
                    if (!r.regionCode) return false;
                    if (r.regionCode === '72') return true;
                    return r.regionCode.startsWith(kabFilterVal);
                });
                if (!hasMatchingRegion) return false;
            }

            if (workloadFilterVal !== 'all') {
                if (workloadFilterVal === 'overloaded' && item.totalHH <= 800) return false;
                if (workloadFilterVal === 'medium' && (item.totalHH <= 500 || item.totalHH > 800)) return false;
                if (workloadFilterVal === 'light' && item.totalHH > 500) return false;
            }

            return true;
        });

        const col = window.petugasSort.column;
        const order = window.petugasSort.order === 'asc' ? 1 : -1;
        filteredData.sort((a, b) => {
            let valA = a[col];
            let valB = b[col];
            if (col === 'totalRegions') {
                valA = a.regions ? a.regions.length : 0;
                valB = b.regions ? b.regions.length : 0;
                return (valA - valB) * order;
            }
            if (col === 'workload' || col === 'totalHH') {
                valA = a.totalHH || 0;
                valB = b.totalHH || 0;
                return (valA - valB) * order;
            }
            if (typeof valA === 'string') {
                return (valA || '').localeCompare(valB || '') * order;
            }
            return ((valA || 0) - (valB || 0)) * order;
        });

        const headers = ["No", "Username", "Email", "Peran", "Beban Kerja (HH)", "Jumlah Wilayah Tugas", "Daftar Wilayah Tugas"];
        const rows = filteredData.map((item, idx) => {
            const regionsStr = (item.regions || []).map(r => `${r.regionName} (${r.regionCode})`).join('; ');
            return [idx + 1, item.username || '-', item.email || '-', item.roleName || '-', item.totalHH || 0, item.regions ? item.regions.length : 0, regionsStr];
        });

        const prefix = activeSubtab === 'ub' ? 'UB' : 'SE2026';
        exportToCSV(`daftar_petugas_${prefix.toLowerCase()}.csv`, headers, rows);
    };

    // Interval to check for updates from other scripts
    setInterval(() => {
        const searchVal = (document.getElementById('search-input')?.value || '').toLowerCase().trim();
        const statusFilterEl = document.getElementById('status-filter');
        const filterVal = statusFilterEl ? statusFilterEl.value : null;
        const activeTab = localStorage.getItem('active_tab') || 'se_umum';

        // Only reload email data if we are NOT using Supabase (Supabase has realtime if we want, but polling is simpler for now)
        if (!isSupabaseUsedGlobal && typeof window.EMAIL_DATA !== 'undefined' && window.EMAIL_DATA !== sourceData) {
            sourceData = window.EMAIL_DATA;
            // --- BARIS YANG DITAMBAHKAN ---
            companies = processGroupedData(sourceData);
            // -----------------------------
            updateFiltersAndStats();
            renderList();
            if (activeTab === 'email') window.updateLastUpdatedText(activeTab);
        }

        // Reload IPAS data if updated
        if (typeof window.IPAS_DATA !== 'undefined') {
            if (window.IPAS_DATA.se_umum && window.IPAS_DATA.se_umum !== se_umumData) {
                se_umumData = window.IPAS_DATA.se_umum;
                if (activeTab === 'se_umum') renderSeDashboard('se_umum');
            }
            if (window.IPAS_DATA.se_ub && window.IPAS_DATA.se_ub !== se_ubData) {
                se_ubData = window.IPAS_DATA.se_ub;
                if (activeTab === 'se_ub') renderSeDashboard('se_ub');
            }
        }

        // Reload Assign data if updated
        if (typeof window.ASSIGN_DATA !== 'undefined' && activeTab === 'assign') {
            renderAssignChart();
            renderKabSummaryTable();
            renderSlsTable();
        }
    }, 5000);

    window.updateLastUpdatedText = function (tabId) {
        if (!tabId) {
            tabId = localStorage.getItem('active_tab') || 'se_umum';
        }

        const el = document.getElementById('last-updated-text');
        if (!el) return;

        let statusText = '';
        if (tabId === 'se_umum' || tabId === 'se_ub') {
            const ipasDataObj = window.IPAS_DATA;
            if (ipasDataObj && ipasDataObj.updated_at) {
                try {
                    const d = new Date(ipasDataObj.updated_at);
                    const formatted = d.toLocaleString('id-ID', {
                        day: '2-digit',
                        month: 'short',
                        year: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit'
                    });
                    statusText = `Update Terakhir: ${formatted} (Sync BPS)`;
                } catch (e) {
                    statusText = `Update Terakhir: ${ipasDataObj.updated_at}`;
                }
            } else {
                statusText = `Update Terakhir: Baru saja (Sync BPS)`;
            }
        } else if (tabId === 'assign') {
            const assignData = window.ASSIGN_DATA_UMUM || window.ASSIGN_DATA_UB || [];
            if (assignData.length > 0 && assignData[0].timestamp) {
                try {
                    const d = new Date(assignData[0].timestamp);
                    const formatted = d.toLocaleString('id-ID', {
                        day: '2-digit',
                        month: 'short',
                        year: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit'
                    });
                    statusText = `Update Terakhir: ${formatted} (Sync Petugas)`;
                } catch (e) {
                    statusText = `Update Terakhir: ${assignData[0].timestamp}`;
                }
            } else {
                statusText = `Update Terakhir: Hari ini (Sync Petugas)`;
            }
        } else if (tabId === 'email') {
            if (supabaseClient && isSupabaseUsedGlobal) {
                statusText = lastUpdatedEmailTextGlobal || `Update Terakhir: Baru saja (Sync Email)`;
            } else if (window.LAST_UPDATED) {
                statusText = `Update Terakhir: ${window.LAST_UPDATED} (Sync Email)`;
            } else {
                statusText = `Update Terakhir: Hari ini (Sync Email)`;
            }
        }

        el.innerHTML = `
            <span style="width: 8px; height: 8px; border-radius: 50%; background-color: #10b981; display: inline-block; animation: pulse 2s infinite; margin-right: 0.35rem;"></span>
            <span>${statusText}</span>
        `;
    };

    // Modal Functions
    let activeModalBusinesses = [];
    let modalFilterType = null; // 'usaha', 'rumah', or null

    window.openNewBusinessesModal = function (kabupatenName, encodedBusinessesJSON, filterType) {
        const modal = document.getElementById('businesses-modal');
        const titleText = document.getElementById('modal-title-text');
        const searchInput = document.getElementById('modal-search-input');
        if (!modal || !titleText || !searchInput) return;

        modalFilterType = filterType || null;

        // BRUTE FORCE CSS: Paksa modal overlay tampil
        modal.style.display = 'flex';
        modal.style.zIndex = '999999';

        // BRUTE FORCE CSS: Paksa kotak putihnya tampil
        const container = modal.querySelector('.modal-container');
        if (container) {
            container.style.display = 'flex';
            container.style.flexDirection = 'column';
            container.style.opacity = '1';
            container.style.visibility = 'visible';
            container.style.transform = 'none'; // Hilangkan efek transisi nyangkut
        }

        const cleanKab = (kabupatenName || "").replace(/\[\d+\]\s*/, '').trim().toUpperCase();
        titleText.innerText = `${modalFilterType === 'rumah' ? 'Penambahan Rumah Baru' : 'Penambahan Usaha Baru'}: KAB. ${cleanKab}`;
        searchInput.value = '';

        try {
            // Decode kembali datanya
            activeModalBusinesses = JSON.parse(decodeURIComponent(encodedBusinessesJSON));
        } catch (e) {
            try { activeModalBusinesses = JSON.parse(encodedBusinessesJSON); } catch (err) { activeModalBusinesses = []; }
        }

        // Jika kosong, coba filter dari NEW_BUSINESSES_DATA (dari file js granular terpisah)
        if (activeModalBusinesses.length === 0 && window.NEW_BUSINESSES_DATA && window.NEW_BUSINESSES_DATA.length > 0) {
            let targetKab = cleanKab;
            let targetKec = null;
            if (cleanKab.includes(' - ')) {
                const parts = cleanKab.split(' - ');
                targetKab = parts[0].trim();
                targetKec = parts[1].trim();
            }

            const extracted = window.NEW_BUSINESSES_DATA.filter(r => {
                const rKab = (r.kabupaten || '').replace(/^\[\d+\]\s*/, '').trim().toUpperCase();
                if (rKab !== targetKab) return false;
                if (targetKec) {
                    const rKec = (r.kecamatan || '').trim().toUpperCase();
                    if (rKec !== targetKec) return false;
                }
                return true;
            });

            activeModalBusinesses = extracted.map(r => {
                return {
                    name: r.name || '-',
                    code: r.code_identity || '-',
                    sls: r.sls || '-',
                    is_usaha: r.is_usaha,
                    type: r.type,
                    timestamp: r.timestamp || ''
                };
            });
        }

        // Jika MASIH kosong, coba fetch dari Supabase (ipas_data slim - new_businesses disimpan terpisah)
        if (activeModalBusinesses.length === 0 && typeof supabaseClient !== 'undefined' && supabaseClient) {
            const surveyType = document.getElementById('assign-sls-survey-filter')?.value || 'se_umum';
            const kabCodeMap = {
                'BANGGAI KEPULAUAN': '7201', 'BANGGAI': '7202', 'MOROWALI': '7203',
                'POSO': '7204', 'DONGGALA': '7205', 'TOLI-TOLI': '7206', 'BUOL': '7207',
                'PARIGI MOUTONG': '7208', 'TOJO UNA-UNA': '7209', 'SIGI': '7210',
                'BANGGAI LAUT': '7211', 'MOROWALI UTARA': '7212', 'PALU': '7271'
            };
            const kabCode = kabCodeMap[cleanKab] || null;
            if (kabCode) {
                const nbKey = `new_businesses_${surveyType}_${kabCode}`;
                // Show loading state
                const container = document.getElementById('modal-business-list');
                if (container) container.innerHTML = '<div style="text-align:center;padding:2rem;color:var(--text-secondary);">Memuat data dari server...</div>';
                supabaseClient.from('dashboard_store').select('value').eq('key', nbKey).single().then(({ data, error }) => {
                    if (!error && data && data.value) {
                        let biz = data.value;
                        if (typeof biz === 'string') try { biz = JSON.parse(biz); } catch(e) { biz = []; }
                        activeModalBusinesses = Array.isArray(biz) ? biz : [];
                        // Cache ke IPAS_DATA agar tidak perlu fetch ulang
                        const ipasDataObj = window.IPAS_DATA || {};
                        const surveyArr = ipasDataObj[surveyType] || [];
                        const kabItem = surveyArr.find(k => (k.kabupaten || '').replace(/^\[\d+\]\s*/, '').trim().toUpperCase() === cleanKab);
                        if (kabItem) kabItem.new_businesses = activeModalBusinesses;
                    } else {
                        activeModalBusinesses = [];
                    }
                    renderModalList();
                }).catch(() => { activeModalBusinesses = []; renderModalList(); });
                modal.classList.add('active');
                return;
            }
        }

        renderModalList();
        modal.classList.add('active');
    };

    window.openProvincialNewBusinessesModal = function (surveyType, filterType) {
        const modal = document.getElementById('businesses-modal');
        const titleText = document.getElementById('modal-title-text');
        const searchInput = document.getElementById('modal-search-input');
        if (!modal || !titleText || !searchInput) return;

        modalFilterType = filterType || null;

        modal.style.display = 'flex';
        modal.style.zIndex = '999999';

        const container = modal.querySelector('.modal-container');
        if (container) {
            container.style.display = 'flex';
            container.style.flexDirection = 'column';
            container.style.opacity = '1';
            container.style.visibility = 'visible';
            container.style.transform = 'none';
        }

        titleText.innerText = `${modalFilterType === 'rumah' ? 'Penambahan Rumah Baru' : 'Penambahan Usaha Baru'}: PROVINSI SULAWESI TENGAH (${surveyType === 'se_umum' ? 'SE2026' : 'Usaha Besar'})`;
        searchInput.value = '';

        const ipasDataObj = window.IPAS_DATA || { se_umum: [], se_ub: [] };
        const surveyData = ipasDataObj[surveyType] || [];

        activeModalBusinesses = [];
        surveyData.forEach(kab => {
            const cleanKab = (kab.kabupaten || "").replace(/\[\d+\]\s*/, '').trim().toUpperCase();
            const list = kab.new_businesses || [];
            list.forEach(b => {
                if (b) activeModalBusinesses.push({ ...b, kabName: cleanKab });
            });
        });

        renderModalList();
        modal.classList.add('active');
    };

    window.closeNewBusinessesModal = function () {
        const modal = document.getElementById('businesses-modal');
        if (modal) {
            modal.classList.remove('active');
            modal.style.display = 'none'; // Sembunyikan tuntas
        }
    };

    window.renderModalList = function () {
        const container = document.getElementById('modal-business-list');
        const searchInput = document.getElementById('modal-search-input');
        if (!container || !searchInput) return;

        const q = searchInput.value.toLowerCase().trim();
        const filtered = activeModalBusinesses.filter(b => {
            const matchesSearch = (b.name || '').toLowerCase().includes(q) || (b.code || '').toLowerCase().includes(q);
            if (!matchesSearch) return false;

            if (modalFilterType === 'usaha') {
                return b.type !== 'rumah';
            } else if (modalFilterType === 'rumah') {
                return b.type === 'rumah';
            }
            return true;
        });

        if (filtered.length === 0) {
            container.innerHTML = `<div style="text-align: center; padding: 3rem 1rem; color: var(--text-secondary); font-size: 0.9rem;">Tidak ada penambahan ${modalFilterType === 'rumah' ? 'rumah baru' : 'usaha baru'} yang ditemukan.</div>`;
            return;
        }

        // Generate list dengan inline CSS cantik
        container.innerHTML = filtered.map(b => {
            const isToday = b.date === 'today';
            const isYesterday = b.date === 'yesterday';
            const badgeColor = isToday ? '#10b981' : (isYesterday ? '#f59e0b' : 'var(--text-muted)');
            const badgeBg = isToday ? 'rgba(16,185,129,0.1)' : (isYesterday ? 'rgba(245,158,11,0.1)' : 'rgba(255,255,255,0.05)');
            const badgeBorder = isToday ? 'rgba(16,185,129,0.3)' : (isYesterday ? 'rgba(245,158,11,0.3)' : 'var(--card-border)');
            const badgeText = isToday ? 'Hari Ini' : (isYesterday ? 'Kemarin' : 'Sebelumnya');
            const kabSub = b.kabName ? `<span style="font-size: 0.75rem; color: var(--text-secondary); background: rgba(255,255,255,0.05); padding: 0.2rem 0.5rem; border-radius: 0.25rem; margin-right: 0.5rem; border: 1px solid var(--card-border);">${b.kabName}</span>` : '';
            const typeBadgeColor = b.type === 'rumah' ? '#ec4899' : 'var(--primary)';
            const typeBadgeBg = b.type === 'rumah' ? 'rgba(236,72,153,0.1)' : 'rgba(59,130,246,0.1)';
            const typeBadgeText = b.type === 'rumah' ? 'RUMAH' : 'USAHA';

            // Map jenis to colors
            let jenisColor = 'var(--primary)';
            let jenisBg = 'rgba(59,130,246,0.1)';
            if (b.jenis) {
                if (b.jenis.includes('Kosong')) {
                    jenisColor = '#94a3b8';
                    jenisBg = 'rgba(148, 163, 184, 0.1)';
                } else if (b.jenis.includes('Keluarga Usaha')) {
                    jenisColor = '#10b981';
                    jenisBg = 'rgba(16, 185, 129, 0.1)';
                } else if (b.jenis.includes('Keluarga')) {
                    jenisColor = '#ec4899';
                    jenisBg = 'rgba(236, 72, 153, 0.1)';
                } else if (b.jenis.includes('UMKM')) {
                    jenisColor = '#8b5cf6';
                    jenisBg = 'rgba(139, 92, 246, 0.1)';
                }
            }
            const jenisBadge = b.jenis ? `<span style="background: ${jenisBg}; padding: 0.25rem 0.6rem; border-radius: 0.5rem; font-size: 0.7rem; font-weight: 800; color: ${jenisColor}; border: 1px solid ${jenisColor}33; text-transform: uppercase; margin-right: 0.25rem;">${b.jenis}</span>` : '';

            // Parse SLS Code from codeIdentity (format: "SLS_CODE - NAME - ...")
            const codeParts = (b.code || '').split(' - ');
            const slsCode = codeParts[0] ? codeParts[0].trim() : '-';

            return `
                <div style="padding: 1rem; border-bottom: 1px solid var(--card-border); display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
                    <div style="display: flex; flex-direction: column; gap: 0.25rem;">
                        <span style="font-weight: 700; color: var(--text-primary); font-size: 0.95rem;">${b.name || '-'}</span>
                        <span style="font-family: monospace; color: var(--text-secondary); font-size: 0.85rem;">Kode SLS: ${slsCode}</span>
                        ${b.kecName && b.kecName !== '-' ? `<span style="font-size: 0.75rem; color: var(--text-muted);">Kecamatan: ${b.kecName}</span>` : ''}
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap;">
                        ${kabSub}
                        ${jenisBadge}
                        <span style="background: ${typeBadgeBg}; padding: 0.25rem 0.6rem; border-radius: 0.5rem; font-size: 0.7rem; font-weight: 800; color: ${typeBadgeColor}; text-transform: uppercase;">${typeBadgeText}</span>
                        <span style="background: rgba(255,255,255,0.05); padding: 0.25rem 0.6rem; border-radius: 0.5rem; font-size: 0.7rem; font-weight: 700; color: var(--text-secondary); text-transform: uppercase; border: 1px solid var(--card-border);">${b.status || 'DRAFT'}</span>
                        <span style="background: ${badgeBg}; border: 1px solid ${badgeBorder}; padding: 0.25rem 0.6rem; border-radius: 0.5rem; font-size: 0.7rem; font-weight: 800; color: ${badgeColor};">${badgeText}</span>
                    </div>
                </div>
            `;
        }).join('');
    };

    window.filterModalList = function () {
        renderModalList();
    };
    // (Kode bawahnya biarkan seperti semula: window.renderAssignChart = ...)

    // Escapement for modal click
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeNewBusinessesModal();
    });

    // Bind functions to window so they are globally accessible by filterAssignData in assign_data.js
    window.renderAssignChart = renderAssignChart;
    window.renderKabSummaryTable = renderKabSummaryTable;
    window.renderSlsTable = renderSlsTable;

    // Switch Tab function
    window.switchTab = function (tabId) {
        // Hide all tab contents
        document.querySelectorAll('.tab-content').forEach(el => {
            el.style.display = 'none';
        });

        // Deactivate all tab buttons
        document.querySelectorAll('.btn-tab').forEach(btn => {
            btn.classList.remove('active');
        });

        // Show active tab content
        const activeContent = document.getElementById('tab-content-' + tabId);
        if (activeContent) {
            activeContent.style.display = 'block';
        }

        // Activate clicked tab button
        const activeBtn = document.getElementById('tab-btn-' + tabId);
        if (activeBtn) {
            activeBtn.classList.add('active');
        }

        // Update main header text & subheader
        const mainHeader = document.getElementById('main-header');
        const mainSubheader = document.getElementById('main-subheader');
        const btnDownloadXlsx = document.getElementById('btn-download-xlsx');
        const btnDownloadBackupCsv = document.getElementById('btn-download-backup-csv');

        if (tabId === 'se_umum') {
            if (mainHeader) mainHeader.textContent = 'Dashboard Sensus Ekonomi 2026';
            if (mainSubheader) mainSubheader.textContent = 'Rekapitulasi progres pendataan Sensus Ekonomi 2026';
            if (btnDownloadXlsx) btnDownloadXlsx.style.display = 'none';
            if (btnDownloadBackupCsv) btnDownloadBackupCsv.style.display = 'none';
            renderSeDashboard('se_umum');
        } else if (tabId === 'se_ub') {
            if (mainHeader) mainHeader.textContent = 'Dashboard Sensus Ekonomi Usaha Besar';
            if (mainSubheader) mainSubheader.textContent = 'Rekapitulasi progres pendataan Sensus Ekonomi 2026 untuk kategori Usaha Besar (UB)';
            if (btnDownloadXlsx) btnDownloadXlsx.style.display = 'none';
            if (btnDownloadBackupCsv) btnDownloadBackupCsv.style.display = 'none';
            renderSeDashboard('se_ub');
        } else if (tabId === 'timeline') {
            if (mainHeader) mainHeader.textContent = 'Tren Submit & Progres Harian';
            if (mainSubheader) mainSubheader.textContent = 'Analisis tren pengiriman data kuesioner per hari';
            if (btnDownloadXlsx) btnDownloadXlsx.style.display = 'none';
            if (btnDownloadBackupCsv) btnDownloadBackupCsv.style.display = 'none';
            window.updateTimelineView();
        } else if (tabId === 'assign') {
            if (mainHeader) mainHeader.textContent = 'Status Alokasi Penugasan Petugas';
            if (mainSubheader) mainSubheader.textContent = 'Rekap alokasi wilayah tugas SLS kepada petugas sensus di setiap Kabupaten/Kota';
            const activeSubtab = localStorage.getItem('active_assign_subtab') || 'se2026';
            if (btnDownloadXlsx) btnDownloadXlsx.style.display = 'none';
            if (btnDownloadBackupCsv) btnDownloadBackupCsv.style.display = 'none';
            if (typeof filterAssignData === 'function') {
                filterAssignData(activeSubtab);
            } else {
                renderAssignChart();
                renderKabSummaryTable();
                renderSlsTable();
            }
            renderSyncTable();
        } else if (tabId === 'target') {
            if (mainHeader) mainHeader.textContent = 'Progres Harian';
            if (mainSubheader) mainSubheader.textContent = 'Detail target tugas sampai level terbawah per kecamatan';
            if (btnDownloadXlsx) btnDownloadXlsx.style.display = 'none';
            if (btnDownloadBackupCsv) btnDownloadBackupCsv.style.display = 'none';
            // Always show summary section and render immediately from IPAS_DATA
            const summarySection = document.getElementById('petugas-summary-section');
            if (summarySection) summarySection.style.display = 'block';
            if (window.renderPetugasSummaryTable) {
                window.renderPetugasSummaryTable(window.GRANULAR_ASSIGNMENTS_DATA || null);
            }
            if (typeof window.loadGranularAssignmentsData === 'function') {
                window.loadGranularAssignmentsData();
            }
        } else if (tabId === 'anomali') {
            if (mainHeader) mainHeader.textContent = 'Pemantauan Anomali';
            if (mainSubheader) mainSubheader.textContent = 'Daftar anomali dan tindak lanjut petugas di lapangan';
            if (btnDownloadXlsx) btnDownloadXlsx.style.display = 'none';
            if (btnDownloadBackupCsv) btnDownloadBackupCsv.style.display = 'none';
            // Activate button
            const anomaliBtn = document.getElementById('tab-btn-anomali');
            if (anomaliBtn) anomaliBtn.classList.add('active');
            // Check if user is already logged in
            const loggedUser = sessionStorage.getItem('anomali_user');
            if (loggedUser) {
                window.showAnomaliDataSection();
            }
        } else if (tabId === 'palu') {
            if (mainHeader) mainHeader.textContent = '🔴 Monitoring Harian Kota Palu';
            if (mainSubheader) mainSubheader.textContent = 'Pantau progres petugas Palu secara detail hingga 15 Juli 2026';
            if (btnDownloadXlsx) btnDownloadXlsx.style.display = 'none';
            if (btnDownloadBackupCsv) btnDownloadBackupCsv.style.display = 'none';
            if (typeof window.initPaluMonitoring === 'function') {
                window.initPaluMonitoring();
            }
        } else {
            if (mainHeader) mainHeader.textContent = 'Pemantauan Email Usaha Besar';
            if (mainSubheader) mainSubheader.textContent = 'Daftar pemantauan status pengiriman email kuesioner kepada responden Usaha Besar (UB)';
            if (btnDownloadXlsx) btnDownloadXlsx.style.display = 'inline-flex';
            if (btnDownloadBackupCsv) btnDownloadBackupCsv.style.display = 'inline-flex';
            renderList();
        }

        window.updateLastUpdatedText(tabId);
        localStorage.setItem('active_tab', tabId);
    };

    // Asynchronously fetch data from Supabase or fallback to data.js & load ipas_data.js
    async function fetchDataAndRender() {
        // Timeout helper to prevent hanging on restricted networks
        const withTimeout = (promise, ms = 2500) => {
            return Promise.race([
                promise,
                new Promise((_, reject) => setTimeout(() => reject(new Error('Query Timeout')), ms))
            ]);
        };

        const isFileProtocol = window.location.protocol === 'file:';
        const getScriptUrl = (filename) => {
            return isFileProtocol ? filename : filename + '?v=' + Date.now();
        };

        // 1. Check selected snapshot date
        const snapshotSelect = document.getElementById('select-snapshot-date');
        const snapshotDate = snapshotSelect ? snapshotSelect.value : 'live';

        // 2. Populate snapshot dates once if using Supabase
        if (supabaseClient && !window.isSnapshotDateDropdownPopulated) {
            try {
                const { data: keysData, error: keysError } = await withTimeout(supabaseClient
                    .from('dashboard_store')
                    .select('key')
                );
                if (!keysError && keysData) {
                    const dateSet = new Set();
                    keysData.forEach(item => {
                        const k = item.key || '';
                        if (k.startsWith('assign_data:')) {
                            const datePart = k.split(':')[1];
                            if (datePart && /^\d{4}-\d{2}-\d{2}$/.test(datePart)) {
                                dateSet.add(datePart);
                            }
                        }
                    });
                    const dates = Array.from(dateSet).sort().reverse();
                    if (snapshotSelect) {
                        snapshotSelect.innerHTML = '<option value="live" style="background-color: var(--card-bg); color: var(--text-primary);">Terbaru (Live DB)</option>' +
                            dates.map(d => `<option value="${d}" style="background-color: var(--card-bg); color: var(--text-primary);">${d}</option>`).join('');
                        snapshotSelect.value = snapshotDate;

                        // Register change listener once
                        if (!window.isSnapshotDateListenerRegistered) {
                            snapshotSelect.addEventListener('change', () => {
                                fetchDataAndRender();
                            });
                            window.isSnapshotDateListenerRegistered = true;
                        }
                        window.isSnapshotDateDropdownPopulated = true;
                    }
                }
            } catch (e) {
                console.warn("Failed to load historical snapshot dates:", e);
            }
        }

        const companyListContainer = document.getElementById('company-list');
        if (companyListContainer) {
            companyListContainer.innerHTML = `
                <div style="text-align: center; padding: 4rem 2rem; color: var(--text-secondary);">
                    <svg style="animation: spin 1s linear infinite; margin: 0 auto 1rem; width: 32px; height: 32px; color: var(--primary);" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle style="opacity: 0.25;" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path style="opacity: 0.75;" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <style>
                        @keyframes spin {
                            from { transform: rotate(0deg); }
                            to { transform: rotate(360deg); }
                        }
                    </style>
                    <h3>Memuat data terbaru...</h3>
                </div>
            `;
        }

        let sourceData = [];
        isSupabaseUsedGlobal = false;

        if (supabaseClient && snapshotDate !== 'local') {
            try {
                let allData = [];
                let fromOffset = 0;
                const limitVal = 1000;
                let keepFetching = true;

                while (keepFetching) {
                    const { data, error } = await withTimeout(supabaseClient
                        .from('email_logs')
                        .select('*')
                        .range(fromOffset, fromOffset + limitVal - 1)
                    );

                    if (error) throw error;

                    if (data && data.length > 0) {
                        allData = allData.concat(data);
                        fromOffset += limitVal;
                        if (data.length < limitVal) {
                            keepFetching = false;
                        }
                    } else {
                        keepFetching = false;
                    }
                }

                if (allData.length > 0) {
                    sourceData = allData;
                    isSupabaseUsedGlobal = true;
                    console.log(`Loaded ${allData.length} records dynamically from Supabase.`);
                }
            } catch (e) {
                console.warn("Supabase fetch failed, falling back to local data.js:", e);
            }
        }

        // Dynamically fetch/reload email data.js
        await new Promise((resolve) => {
            const script = document.createElement('script');
            script.src = getScriptUrl('data.js');
            script.onload = () => resolve();
            script.onerror = () => resolve();
            document.head.appendChild(script);
        });

        if (sourceData.length === 0) {
            sourceData = window.EMAIL_DATA || [];
            console.log(`Loaded ${sourceData.length} records from local data.js.`);
        }

        let ipasLoadedFromDb = false;
        let assignLoadedFromDb = false;
        let syncLoadedFromDb = false;

        const ipasKey = snapshotDate === 'live' ? 'ipas_data' : `ipas_data:${snapshotDate}`;
        const assignKey = snapshotDate === 'live' ? 'assign_data' : `assign_data:${snapshotDate}`;
        const syncKey = snapshotDate === 'live' ? 'superset_sync_data' : `superset_sync_data:${snapshotDate}`;
        const timelineKey = snapshotDate === 'live' ? 'daily_submission_stats' : `daily_submission_stats:${snapshotDate}`;

        let timelineLoadedFromDb = false;

        if (snapshotDate !== 'live' && snapshotDate !== 'local') {
            // Set loaded flags to true to prevent local script reloading fallbacks
            ipasLoadedFromDb = true;
            assignLoadedFromDb = true;
            syncLoadedFromDb = true;
            timelineLoadedFromDb = true;

            // Clear current data first in case snapshot date has missing tables
            window.IPAS_DATA = null;
            window.ASSIGN_DATA_UMUM = [];
            window.ASSIGN_DATA_UB = [];
            window.ASSIGN_SLS_DATA_UMUM = [];
            window.ASSIGN_SLS_DATA_UB = [];
            window.PETUGAS_DATA_UMUM = [];
            window.PETUGAS_DATA_UB = [];
            window.SUPERSET_SYNC_SLS_DATA = [];
            window.DAILY_SUBMISSION_STATS = [];
        }

        if (supabaseClient && snapshotDate !== 'local') {
            try {
                const { data: ipasDbData, error: ipasError } = await withTimeout(supabaseClient
                    .from('dashboard_store')
                    .select('value')
                    .eq('key', ipasKey)
                    .single()
                );
                if (!ipasError && ipasDbData && ipasDbData.value) {
                    window.IPAS_DATA = ipasDbData.value;
                    ipasLoadedFromDb = true;
                    console.log(`Loaded IPAS_DATA (${ipasKey}) from Supabase.`);
                }
            } catch (e) {
                console.warn(`Failed to fetch IPAS_DATA (${ipasKey}) from Supabase:`, e);
            }

            try {
                const { data: assignDbData, error: assignError } = await withTimeout(supabaseClient
                    .from('dashboard_store')
                    .select('value')
                    .eq('key', assignKey)
                    .single()
                );
                if (!assignError && assignDbData && assignDbData.value) {
                    let assignVal = assignDbData.value;
                    if (assignVal.is_compressed && assignVal.compressed_data) {
                        assignVal = window.decompressAndParsePayload(assignVal.compressed_data);
                    }
                    window.ASSIGN_DATA_UMUM = assignVal.assign_data_umum || [];
                    window.ASSIGN_DATA_UB = assignVal.assign_data_ub || [];

                    const decompressSls = (list) => {
                        if (!list || !Array.isArray(list)) return [];
                        if (list.length > 0 && !Array.isArray(list[0])) return list; // Already decompressed / old format
                        return list.map(item => {
                            if (item.length === 9) {
                                return {
                                    sls_code: item[0],
                                    sls_name: item[1],
                                    desa_name: item[2],
                                    kec_name: item[3],
                                    kab_name: item[4],
                                    total: item[5],
                                    assigned: item[6],
                                    unassigned: item[7],
                                    sync_count: 0,
                                    officers: item[8] || []
                                };
                            } else {
                                return {
                                    sls_code: item[0],
                                    sls_name: item[1],
                                    desa_name: item[2],
                                    kec_name: item[3],
                                    kab_name: item[4],
                                    total: item[5],
                                    assigned: item[6],
                                    unassigned: item[7],
                                    sync_count: item[8],
                                    officers: item[9] || []
                                };
                            }
                        });
                    };

                    window.ASSIGN_SLS_DATA_UMUM = decompressSls(assignVal.assign_sls_data_umum);
                    window.ASSIGN_SLS_DATA_UB = decompressSls(assignVal.assign_sls_data_ub);
                    window.PETUGAS_DATA_UMUM = assignVal.petugas_data_umum || [];
                    window.PETUGAS_DATA_UB = assignVal.petugas_data_ub || [];

                    const activeSubtab = localStorage.getItem('active_assign_subtab') || 'se2026';
                    if (activeSubtab === 'se2026') {
                        window.ASSIGN_DATA = window.ASSIGN_DATA_UMUM;
                        window.ASSIGN_SLS_DATA = window.ASSIGN_SLS_DATA_UMUM;
                        window.PETUGAS_DATA = window.PETUGAS_DATA_UMUM;
                    } else {
                        window.ASSIGN_DATA = window.ASSIGN_DATA_UB;
                        window.ASSIGN_SLS_DATA = window.ASSIGN_SLS_DATA_UB;
                        window.PETUGAS_DATA = window.PETUGAS_DATA_UB;
                    }
                    assignLoadedFromDb = true;
                    console.log(`Loaded ASSIGN_DATA (${assignKey}) from Supabase.`);
                }
            } catch (e) {
                console.warn(`Failed to fetch ASSIGN_DATA (${assignKey}) from Supabase:`, e);
            }

            try {
                const { data: syncDbData, error: syncError } = await withTimeout(supabaseClient
                    .from('dashboard_store')
                    .select('value')
                    .eq('key', syncKey)
                    .single()
                );
                if (!syncError && syncDbData && syncDbData.value) {
                    window.SUPERSET_SYNC_SLS_DATA = syncDbData.value;
                    syncLoadedFromDb = true;
                    console.log(`Loaded SUPERSET_SYNC_SLS_DATA (${syncKey}) from Supabase.`);
                }
            } catch (e) {
                console.warn(`Failed to fetch SUPERSET_SYNC_SLS_DATA (${syncKey}) from Supabase:`, e);
            }

            try {
                const { data: timelineDbData, error: timelineError } = await withTimeout(supabaseClient
                    .from('dashboard_store')
                    .select('value')
                    .eq('key', timelineKey)
                    .single()
                );
                if (!timelineError && timelineDbData && timelineDbData.value) {
                    let tv = timelineDbData.value;
                    // Normalize: could be array, or object wrapping array
                    if (Array.isArray(tv)) {
                        window.DAILY_SUBMISSION_STATS = tv;
                    } else if (tv && typeof tv === 'object') {
                        // Try common wrapper keys
                        window.DAILY_SUBMISSION_STATS = tv.data || tv.stats || tv.records || [];
                    } else {
                        window.DAILY_SUBMISSION_STATS = [];
                    }
                    timelineLoadedFromDb = true;
                    console.log(`Loaded DAILY_SUBMISSION_STATS (${timelineKey}) from Supabase. Count: ${window.DAILY_SUBMISSION_STATS.length}`);
                }
            } catch (e) {
                console.warn(`Failed to fetch DAILY_SUBMISSION_STATS (${timelineKey}) from Supabase:`, e);
            }
        }

        if (!ipasLoadedFromDb) {
            // Dynamically reload IPAS ipas_data.js
            await new Promise((resolve) => {
                const script = document.createElement('script');
                script.src = getScriptUrl('ipas_data.js');
                script.onload = () => resolve();
                script.onerror = () => resolve();
                document.head.appendChild(script);
            });
        }

        if (!assignLoadedFromDb) {
            // Dynamically reload assign_data.js
            await new Promise((resolve) => {
                const script = document.createElement('script');
                script.src = getScriptUrl('fast_master_assign_data.js');
                script.onload = () => resolve();
                script.onerror = () => resolve();
                document.head.appendChild(script);
            });
        }

        if (!syncLoadedFromDb) {
            // Dynamically reload sync_data.js
            await new Promise((resolve) => {
                const script = document.createElement('script');
                script.src = getScriptUrl('sync_data.js');
                script.onload = () => resolve();
                script.onerror = () => resolve();
                document.head.appendChild(script);
            });
        }

        if (!timelineLoadedFromDb) {
            // Dynamically reload daily_submission_stats.js
            await new Promise((resolve) => {
                const script = document.createElement('script');
                script.src = getScriptUrl('daily_submission_stats.js');
                script.onload = () => resolve();
                script.onerror = () => resolve();
                document.head.appendChild(script);
            });
        }

        const activeSubtab = localStorage.getItem('active_assign_subtab') || 'se2026';
        if (activeSubtab === 'se2026') {
            window.ASSIGN_DATA = window.ASSIGN_DATA_UMUM;
            window.ASSIGN_SLS_DATA = window.ASSIGN_SLS_DATA_UMUM;
            window.PETUGAS_DATA = window.PETUGAS_DATA_UMUM;
        } else {
            window.ASSIGN_DATA = window.ASSIGN_DATA_UB;
            window.ASSIGN_SLS_DATA = window.ASSIGN_SLS_DATA_UB;
            window.PETUGAS_DATA = window.PETUGAS_DATA_UB;
        }

        // Sinkronisasi data local SLS dengan real-time Superset data
        syncLocalSlsWithSupersetData();

        companies = processGroupedData(sourceData);

        // Generate last updated text templates
        if (isSupabaseUsedGlobal) {
            const timestamps = sourceData.map(r => new Date(r.created_at)).filter(d => !isNaN(d));
            if (timestamps.length > 0) {
                const latestTime = new Date(Math.max(...timestamps));
                lastUpdatedEmailTextGlobal = `Terakhir Diperbarui: ${latestTime.toLocaleString('id-ID', {
                    day: '2-digit',
                    month: 'short',
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit'
                })} (Live DB)`;
            } else {
                lastUpdatedEmailTextGlobal = `Terakhir Diperbarui: Baru saja (Live DB)`;
            }
        }

        currentPage = 1; // Reset page on refresh/fetch
        updateFiltersAndStats();
        renderList();
        renderSeDashboard('se_umum');
        renderSeDashboard('se_ub');

        // Refresh last updated text for all tabs
        window.updateLastUpdatedText();

        const activeTab = localStorage.getItem('active_tab') || 'se_umum';
        if (activeTab === 'timeline') {
            window.updateTimelineView();
        } else if (activeTab === 'target') {
            if (typeof window.loadGranularAssignmentsData === 'function') {
                window.loadGranularAssignmentsData();
            }
        } else if (activeTab === 'assign') {
            const activeSubtab = localStorage.getItem('active_assign_subtab') || 'se2026';
            if (typeof filterAssignData === 'function') {
                filterAssignData(activeSubtab);
            } else {
                renderAssignChart();
                renderSlsTable();
            }
            renderSyncTable();
        }
    }

    // Refresh button handler
    const refreshBtn = document.getElementById('btn-refresh');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            fetchDataAndRender();
        });
    }

    // CSV Backup download handler
    const btnDownloadBackupCsv = document.getElementById('btn-download-backup-csv');
    if (btnDownloadBackupCsv) {
        btnDownloadBackupCsv.addEventListener('click', () => {
            if (!companies || companies.length === 0) {
                alert('Data tidak tersedia untuk diunduh.');
                return;
            }

            // Generate CSV content
            let csvContent = "\ufeff"; // BOM for Excel UTF-8 support
            // Header row
            csvContent += "Kode Identitas,Nama Perusahaan,Kabupaten/Kota,Status Dokumen,Email Tujuan,Status Pengiriman Email\n";

            companies.forEach(comp => {
                const code = comp.code || "";
                const name = (comp.company_name || "").replace(/"/g, '""');
                const prefix = code ? code.substring(0, 4) : "";
                const kabkot = kabkotMapping[prefix] || "Lainnya";
                const surveyStatus = comp.survey_status || "-";
                const email = comp.email || "";
                const emailStatus = comp.global_status || "-";

                csvContent += `"${code}","${name}","${kabkot}","${surveyStatus}","${email}","${emailStatus}"\n`;
            });

            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const url = URL.createObjectURL(blob);
            const link = document.createElement("a");
            link.setAttribute("href", url);
            const timestampStr = new Date().toISOString().slice(0, 10);
            link.setAttribute("download", `backup_data_ub_${timestampStr}.csv`);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        });
    }
    // Intercept filterAssignData to reset populated states and filters on subtab switch
    const originalFilterAssignData = window.filterAssignData;
    window.filterAssignData = function (type) {
        if (type === 'ub' || type === 'se_ub') {
            type = 'se2026';
        }
        // Reset populated state of filters so they rebuild with the correct subtab data
        isSlsFiltersPopulated = false;
        isSyncFiltersPopulated = false;

        // Reset filter select elements to "all"
        const resetSelect = (id) => {
            const el = document.getElementById(id);
            if (el) el.value = 'all';
        };
        resetSelect('sls-kab-filter');
        resetSelect('sls-kec-filter');
        resetSelect('sls-desa-filter');
        resetSelect('sls-petugas-filter');
        resetSelect('sls-assignment-filter');
        resetSelect('assign-sls-status-filter');

        resetSelect('sync-kab-filter');
        resetSelect('sync-kec-filter');
        resetSelect('sync-desa-filter');
        resetSelect('sync-petugas-filter');
        resetSelect('sync-status-filter');

        resetSelect('diff-kab-filter');

        localStorage.setItem('active_assign_subtab', type);
        const btnUmum = document.getElementById("subtab-btn-se2026");
        const btnUB = document.getElementById("subtab-btn-ub");

        const chartTitle = document.getElementById("assign-chart-title");
        const slsTitle = document.getElementById("assign-sls-title");

        if (type === 'se2026') {
            if (btnUmum) { btnUmum.style.backgroundColor = 'var(--primary)'; btnUmum.style.color = 'white'; }
            if (btnUB) { btnUB.style.backgroundColor = 'transparent'; btnUB.style.color = 'var(--text-secondary)'; }
            if (chartTitle) chartTitle.innerText = "Status Assign Petugas (Semua Usaha - SE Umum)";
            if (slsTitle) slsTitle.innerText = "Ringkasan Assignment per Kabupaten/Kota (SE Umum)";

            window.ASSIGN_DATA = window.ASSIGN_DATA_UMUM;
            window.ASSIGN_SLS_DATA = window.ASSIGN_SLS_DATA_UMUM;
            window.PETUGAS_DATA = window.PETUGAS_DATA_UMUM;
        } else {
            if (btnUB) { btnUB.style.backgroundColor = 'var(--primary)'; btnUB.style.color = 'white'; }
            if (btnUmum) { btnUmum.style.backgroundColor = 'transparent'; btnUmum.style.color = 'var(--text-secondary)'; }
            if (chartTitle) chartTitle.innerText = "Status Assign Petugas (Usaha Besar - UB)";
            if (slsTitle) slsTitle.innerText = "Ringkasan Assignment per Kabupaten/Kota (UB)";

            window.ASSIGN_DATA = window.ASSIGN_DATA_UB;
            window.ASSIGN_SLS_DATA = window.ASSIGN_SLS_DATA_UB;
            window.PETUGAS_DATA = window.PETUGAS_DATA_UB;
        }

        if (typeof originalFilterAssignData === 'function') {
            originalFilterAssignData(type);
        } else {
            if (typeof renderAssignChart === 'function') renderAssignChart();
            if (typeof renderKabSummaryTable === 'function') renderKabSummaryTable();
            if (typeof renderSlsTable === 'function') {
                window.slsCurrentPage = 1;
                renderSlsTable();
            }
            if (typeof renderPetugasTable === 'function') {
                window.petugasCurrentPage = 1;
                renderPetugasTable();
            }
        }

        // Initialize/reset active subtab to 'kab' on survey type switch
        window.switchAssignSubtab('kab');

        renderSyncTable();

        window.diffCurrentPage = 1;
        renderDiffTable();
    };

    // --- DIFFERENCE (SELISIH ALOKASI) TABLE ---
    window.activeDiffTab = 'p_only';
    window.diffCurrentPage = 1;
    let diffRowsPerPage = 50;

    window.switchDiffTab = function (tab) {
        window.activeDiffTab = tab;
        window.diffCurrentPage = 1;

        // Update tab buttons
        const btnP = document.getElementById('btn-diff-p-only');
        const btnW = document.getElementById('btn-diff-w-only');

        if (tab === 'p_only') {
            if (btnP) {
                btnP.style.backgroundColor = 'var(--primary)';
                btnP.style.color = 'white';
                btnP.style.border = 'none';
            }
            if (btnW) {
                btnW.style.backgroundColor = 'transparent';
                btnW.style.color = 'var(--text-secondary)';
                btnW.style.border = '1px solid var(--card-border)';
            }
            const header = document.getElementById('diff-table-header-officer');
            if (header) header.innerText = 'Pencacah';
        } else {
            if (btnW) {
                btnW.style.backgroundColor = 'var(--primary)';
                btnW.style.color = 'white';
                btnW.style.border = 'none';
            }
            if (btnP) {
                btnP.style.backgroundColor = 'transparent';
                btnP.style.color = 'var(--text-secondary)';
                btnP.style.border = '1px solid var(--card-border)';
            }
            const header = document.getElementById('diff-table-header-officer');
            if (header) header.innerText = 'Pengawas';
        }

        window.renderDiffTable();
    };

    window.changeDiffLimit = function (val) {
        diffRowsPerPage = parseInt(val) || 50;
        window.diffCurrentPage = 1;
        window.renderDiffTable();
    };

    window.renderDiffTable = function () {
        const petugasData = window.PETUGAS_DATA || [];
        const tbody = document.getElementById('diff-table-body');
        const paginationInfo = document.getElementById('diff-pagination-info');
        if (!tbody || !paginationInfo) return;

        // 1. Map all regions by role from window.PETUGAS_DATA
        const pencacahRegions = {};
        const pengawasRegions = {};

        petugasData.forEach(p => {
            const role = p.roleName;
            const displayName = `${p.username} (${p.email})`;
            if (p.regions) {
                p.regions.forEach(r => {
                    const code = r.regionCode;
                    if (!code) return;

                    if (role === 'Pencacah') {
                        if (!pencacahRegions[code]) {
                            pencacahRegions[code] = { name: r.regionName || 'LAINNYA', officers: new Set() };
                        }
                        pencacahRegions[code].officers.add(displayName);
                    } else if (role === 'Pengawas') {
                        if (!pengawasRegions[code]) {
                            pengawasRegions[code] = { name: r.regionName || 'LAINNYA', officers: new Set() };
                        }
                        pengawasRegions[code].officers.add(displayName);
                    }
                });
            }
        });

        // 2. Identify differences
        const pencacahNotPengawas = [];
        const pengawasNotPencacah = [];

        for (const code in pencacahRegions) {
            if (!pengawasRegions[code]) {
                pencacahNotPengawas.push({
                    code: code,
                    name: pencacahRegions[code].name,
                    officer: Array.from(pencacahRegions[code].officers).join(', ')
                });
            }
        }

        for (const code in pengawasRegions) {
            if (!pencacahRegions[code]) {
                pengawasNotPencacah.push({
                    code: code,
                    name: pengawasRegions[code].name,
                    officer: Array.from(pengawasRegions[code].officers).join(', ')
                });
            }
        }

        // Apply filters to calculate counts for the selected Kabupaten/search query
        const kabFilterEl = document.getElementById('diff-kab-filter');
        const kabFilterVal = kabFilterEl ? kabFilterEl.value : 'all';

        const searchInputEl = document.getElementById('diff-search-input');
        const searchVal = searchInputEl ? searchInputEl.value.toLowerCase().trim() : '';

        const filterItem = (item) => {
            if (kabFilterVal !== 'all' && !item.code.startsWith(kabFilterVal)) {
                return false;
            }
            if (searchVal) {
                const matchText = (item.code + ' ' + item.name + ' ' + item.officer).toLowerCase();
                if (!matchText.includes(searchVal)) return false;
            }
            return true;
        };

        const filteredPOnly = pencacahNotPengawas.filter(filterItem);
        const filteredWOnly = pengawasNotPencacah.filter(filterItem);

        // Update counts in pill buttons to reflect filtered state
        const pOnlyCountEl = document.getElementById('count-diff-p-only');
        const wOnlyCountEl = document.getElementById('count-diff-w-only');
        if (pOnlyCountEl) pOnlyCountEl.innerText = filteredPOnly.length;
        if (wOnlyCountEl) wOnlyCountEl.innerText = filteredWOnly.length;

        // Choose source array based on active mismatch subtab
        const filtered = window.activeDiffTab === 'p_only' ? filteredPOnly : filteredWOnly;

        // Sort alphabetically by code
        filtered.sort((a, b) => a.code.localeCompare(b.code));

        const totalItems = filtered.length;
        if (totalItems === 0) {
            tbody.innerHTML = `<tr><td colspan="4" style="text-align: center; padding: 2rem; color: var(--text-secondary);">Tidak ada data selisih alokasi yang cocok.</td></tr>`;
            paginationInfo.innerText = `Menampilkan 0 - 0 dari 0 SLS`;
            renderDiffPaginationButtons(0);
            return;
        }

        const maxPage = Math.ceil(totalItems / diffRowsPerPage);
        if (window.diffCurrentPage > maxPage) window.diffCurrentPage = maxPage;
        if (window.diffCurrentPage < 1) window.diffCurrentPage = 1;

        const startIdx = (window.diffCurrentPage - 1) * diffRowsPerPage;
        const endIdx = Math.min(startIdx + diffRowsPerPage, totalItems);

        paginationInfo.innerText = `Menampilkan ${startIdx + 1} - ${endIdx} dari ${totalItems} SLS`;

        const pageData = filtered.slice(startIdx, endIdx);

        tbody.innerHTML = pageData.map((item, index) => {
            const rowNumber = startIdx + index + 1;
            const hl = (txt) => highlightText(txt, searchVal);

            return `
                <tr style="border-bottom: 1px solid var(--card-border); transition: background-color 0.2s;">
                    <td style="padding: 1rem; color: var(--text-secondary); text-align: center; font-weight: 500;">${rowNumber}</td>
                    <td style="padding: 1rem; font-family: monospace; font-weight: 600; color: var(--text-secondary);">${hl(item.code)}</td>
                    <td style="padding: 1rem; font-weight: 600; color: var(--text);">${hl(item.name)}</td>
                    <td style="padding: 1rem; color: var(--text-primary);">${hl(item.officer || '-')}</td>
                </tr>
            `;
        }).join('');

        renderDiffPaginationButtons(maxPage);
    };

    function renderDiffPaginationButtons(maxPage) {
        const btnContainer = document.getElementById('diff-pagination-buttons');
        if (!btnContainer) return;
        btnContainer.innerHTML = '';

        const btnStyle = `padding: 0.4rem 0.75rem; font-size: 0.8rem; font-weight: 600; border-radius: 0.5rem; border: 1px solid var(--card-border); background-color: var(--card-bg); color: var(--text); cursor: pointer; transition: all 0.2s;`;
        const activeStyle = `padding: 0.4rem 0.75rem; font-size: 0.8rem; font-weight: 700; border-radius: 0.5rem; border: 1px solid transparent; background-color: var(--primary); color: white; cursor: default;`;

        if (window.diffCurrentPage > 1) {
            const prevBtn = document.createElement('button');
            prevBtn.innerHTML = '&lt;';
            prevBtn.style.cssText = btnStyle;
            prevBtn.addEventListener('click', () => {
                window.diffCurrentPage--;
                renderDiffTable();
            });
            btnContainer.appendChild(prevBtn);
        }

        let startPage = Math.max(1, window.diffCurrentPage - 2);
        let endPage = Math.min(maxPage, window.diffCurrentPage + 2);

        if (startPage > 1) {
            const page1 = document.createElement('button');
            page1.textContent = '1';
            page1.style.cssText = btnStyle;
            page1.addEventListener('click', () => { window.diffCurrentPage = 1; renderDiffTable(); });
            btnContainer.appendChild(page1);

            if (startPage > 2) {
                const dots = document.createElement('span');
                dots.textContent = '...';
                dots.style.cssText = 'color: var(--text-secondary); font-size: 0.8rem; padding: 0 0.25rem;';
                btnContainer.appendChild(dots);
            }
        }

        for (let i = startPage; i <= endPage; i++) {
            const btn = document.createElement('button');
            btn.textContent = i;
            if (i === window.diffCurrentPage) {
                btn.style.cssText = activeStyle;
            } else {
                btn.style.cssText = btnStyle;
                btn.addEventListener('click', () => { window.diffCurrentPage = i; renderDiffTable(); });
            }
            btnContainer.appendChild(btn);
        }

        if (endPage < maxPage) {
            if (endPage < maxPage - 1) {
                const dots = document.createElement('span');
                dots.textContent = '...';
                dots.style.cssText = 'color: var(--text-secondary); font-size: 0.8rem; padding: 0 0.25rem;';
                btnContainer.appendChild(dots);
            }

            const pageLast = document.createElement('button');
            pageLast.textContent = maxPage;
            pageLast.style.cssText = btnStyle;
            pageLast.addEventListener('click', () => { window.diffCurrentPage = maxPage; renderDiffTable(); });
            btnContainer.appendChild(pageLast);
        }

        if (window.diffCurrentPage < maxPage) {
            const nextBtn = document.createElement('button');
            nextBtn.innerHTML = '&gt;';
            nextBtn.style.cssText = btnStyle;
            nextBtn.addEventListener('click', () => {
                window.diffCurrentPage++;
                renderDiffTable();
            });
            btnContainer.appendChild(nextBtn);
        }
    }

    window.downloadDiffCSV = function () {
        const petugasData = window.PETUGAS_DATA || [];
        const activeSubtab = localStorage.getItem('active_assign_subtab') || 'se2026';
        const prefix = activeSubtab === 'ub' ? 'UB' : 'SE2026';

        const pencacahRegions = {};
        const pengawasRegions = {};

        petugasData.forEach(p => {
            const role = p.roleName;
            const displayName = `${p.username} (${p.email})`;
            if (p.regions) {
                p.regions.forEach(r => {
                    const code = r.regionCode;
                    if (!code) return;

                    if (role === 'Pencacah') {
                        if (!pencacahRegions[code]) {
                            pencacahRegions[code] = { name: r.regionName || 'LAINNYA', officers: new Set() };
                        }
                        pencacahRegions[code].officers.add(displayName);
                    } else if (role === 'Pengawas') {
                        if (!pengawasRegions[code]) {
                            pengawasRegions[code] = { name: r.regionName || 'LAINNYA', officers: new Set() };
                        }
                        pengawasRegions[code].officers.add(displayName);
                    }
                });
            }
        });

        const pencacahNotPengawas = [];
        const pengawasNotPencacah = [];

        for (const code in pencacahRegions) {
            if (!pengawasRegions[code]) {
                pencacahNotPengawas.push({
                    code: code,
                    name: pencacahRegions[code].name,
                    officer: Array.from(pencacahRegions[code].officers).join('; ')
                });
            }
        }

        for (const code in pengawasRegions) {
            if (!pencacahRegions[code]) {
                pengawasNotPencacah.push({
                    code: code,
                    name: pengawasRegions[code].name,
                    officer: Array.from(pengawasRegions[code].officers).join('; ')
                });
            }
        }

        const sourceArray = window.activeDiffTab === 'p_only' ? pencacahNotPengawas : pengawasNotPencacah;

        const kabFilterEl = document.getElementById('diff-kab-filter');
        const kabFilterVal = kabFilterEl ? kabFilterEl.value : 'all';

        const searchInputEl = document.getElementById('diff-search-input');
        const searchVal = searchInputEl ? searchInputEl.value.toLowerCase().trim() : '';

        let filtered = sourceArray.filter(item => {
            if (kabFilterVal !== 'all' && !item.code.startsWith(kabFilterVal)) {
                return false;
            }
            if (searchVal) {
                const matchText = (item.code + ' ' + item.name + ' ' + item.officer).toLowerCase();
                if (!matchText.includes(searchVal)) return false;
            }
            return true;
        });

        filtered.sort((a, b) => a.code.localeCompare(b.code));

        const roleHeader = window.activeDiffTab === 'p_only' ? "Pencacah" : "Pengawas";
        const headers = ["No", "Kode SLS", "Nama SLS", `Petugas (${roleHeader})`];
        const rows = filtered.map((item, idx) => [
            idx + 1,
            item.code,
            item.name,
            item.officer || '-'
        ]);

        const filePrefix = window.activeDiffTab === 'p_only' ? 'pencacah_saja' : 'pengawas_saja';
        exportToCSV(`selisih_alokasi_${filePrefix}_${prefix.toLowerCase()}.csv`, headers, rows);
    };

    window.loadGranularAssignmentsData = loadGranularAssignmentsData;
    window.toggleStatsDetail = function (section) {
        const container = document.getElementById(`${section}-stats-expanded`);
        const btn = document.getElementById(`${section}-toggle-detail`);
        if (!container || !btn) return;

        if (container.style.display === 'none') {
            container.style.display = 'flex';
            btn.classList.add('expanded');
            btn.innerHTML = 'Sembunyikan Detail ▲';
        } else {
            container.style.display = 'none';
            btn.classList.remove('expanded');
            btn.innerHTML = section === 'email' ? 'Lihat Kegagalan Email ▼' : 'Lihat Detail Lainnya ▼';
        }
    };

    // =========================================================================
    // DAILY SUBMISSION TIMELINE & GRANULAR LOOKUP LOGIC
    // =========================================================================

    let dailySubmissionChartInstance = null;

    function renderDailySubmissionChart(dates, counts) {
        const ctx = document.getElementById('dailySubmissionChart');
        if (!ctx) return;

        if (dailySubmissionChartInstance) {
            dailySubmissionChartInstance.destroy();
        }

        const isDark = document.body.classList.contains('dark-theme');
        const textColor = isDark ? '#e2e8f0' : '#475569';
        const borderColor = isDark ? '#f97316' : '#ea580c';

        dailySubmissionChartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [{
                    label: 'Jumlah Submit Sensus',
                    data: counts,
                    borderColor: borderColor,
                    backgroundColor: isDark ? 'rgba(249, 115, 22, 0.15)' : 'rgba(234, 88, 12, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.3,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    pointBackgroundColor: borderColor,
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 1.5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        padding: 10,
                        backgroundColor: isDark ? '#1e293b' : '#ffffff',
                        titleColor: isDark ? '#ffffff' : '#0f172a',
                        bodyColor: isDark ? '#cbd5e1' : '#334155',
                        borderColor: isDark ? '#334155' : '#e2e8f0',
                        borderWidth: 1,
                        titleFont: { family: 'Outfit', weight: 'bold' },
                        bodyFont: { family: 'Outfit' }
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { color: textColor, font: { family: 'Outfit', size: 11 } }
                    },
                    y: {
                        grid: { color: isDark ? '#334155' : '#e2e8f0', drawBorder: false },
                        ticks: { color: textColor, font: { family: 'Outfit', size: 11 }, beginAtZero: true, precision: 0 }
                    }
                }
            }
        });
    }

    function renderTimelineTable(dates, dateMap, kabFilter, typeFilter) {
        const tbody = document.getElementById('timeline-table-body');
        if (!tbody) return;

        if (!window.DAILY_SUBMISSION_STATS || window.DAILY_SUBMISSION_STATS.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; padding: 2rem; color: var(--text-secondary);">Tidak ada data progres harian.</td></tr>`;
            return;
        }

        const filtered = window.DAILY_SUBMISSION_STATS.filter(r => {
            if (kabFilter !== 'all') {
                const cleanFilter = kabFilter.replace(/^\[\d+\]\s*/, '').trim().toUpperCase();
                if ((r.kab_name || '').toUpperCase() !== cleanFilter) return false;
            }
            if (typeFilter !== 'all' && r.survey_type !== typeFilter) return false;
            return true;
        });

        filtered.sort((a, b) => b.date.localeCompare(a.date) || a.kab_name.localeCompare(b.kab_name));

        if (filtered.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; padding: 2rem; color: var(--text-secondary);">Tidak ada data untuk filter terpilih.</td></tr>`;
            return;
        }

        const fmt = (n) => new Intl.NumberFormat('id-ID').format(n || 0);
        let rowsHtml = '';

        filtered.forEach((r, index) => {
            const surveyLabel = r.survey_type === 'se_umum' ? 'SE Umum' : 'SE UB';
            const badgeClass = r.survey_type === 'se_umum' ? 'table-badge-umum' : 'table-badge-ub';

            rowsHtml += `
                <tr style="border-bottom: 1px solid var(--card-border); transition: background-color 0.15s;">
                    <td style="padding: 0.75rem 1.25rem; text-align: center; vertical-align: middle; font-weight: 600; color: var(--text-secondary);">${index + 1}</td>
                    <td style="padding: 0.75rem 1.25rem; text-align: center; vertical-align: middle; font-weight: 700; color: var(--text-primary);">${r.date}</td>
                    <td style="padding: 0.75rem 1.25rem; text-align: left; vertical-align: middle; font-weight: 600; color: var(--text-primary);">${r.kab_name}</td>
                    <td style="padding: 0.75rem 1.25rem; text-align: center; vertical-align: middle;">
                        <span class="table-badge ${badgeClass}">${surveyLabel}</span>
                    </td>
                    <td style="padding: 0.75rem 1.25rem; text-align: right; vertical-align: middle; font-weight: 800; color: var(--primary); font-family: monospace; font-size: 0.95rem;">${fmt(r.count)}</td>
                </tr>
            `;
        });

        tbody.innerHTML = rowsHtml;
    }

    window.updateTimelineView = function () {
        if (typeof window.initTrenFilters === 'function') window.initTrenFilters();
        if (typeof window.renderTrenChart === 'function') window.renderTrenChart();
    };

    // --- GRANULAR DATA UTILITIES ---

    window.decompressAndParsePayload = function (compressedBase64) {
        try {
            console.log("Decompressing payload...");
            const binaryString = atob(compressedBase64);
            const len = binaryString.length;
            const bytes = new Uint8Array(len);
            for (let i = 0; i < len; i++) {
                bytes[i] = binaryString.charCodeAt(i);
            }
            const decompressed = pako.ungzip(bytes, { to: 'string' });
            return JSON.parse(decompressed);
        } catch (e) {
            console.error("Failed to decompress payload:", e);
            return null;
        }
    };

    window.decompressAndParseGranular = function (compressedBase64) {
        try {
            console.log("Decompressing granular data...");
            const binaryString = atob(compressedBase64);
            const len = binaryString.length;
            const bytes = new Uint8Array(len);
            for (let i = 0; i < len; i++) {
                bytes[i] = binaryString.charCodeAt(i);
            }
            const decompressed = pako.ungzip(bytes, { to: 'string' });
            const payload = JSON.parse(decompressed);

            const regions = payload.regions || [];
            const petugas = payload.petugas || [];
            const statuses = payload.statuses || [];
            const targets = payload.targets || [];
            const remarksDict = payload.remarks || {};


            console.log(`Rebuilding ${targets.length} targets...`);
            const rebuilt = targets.map((t) => {
                const regIdx = t[5];
                const petIdx = t[4];
                const statIdx = t[3];
                const pengawasIdx = t.length > 8 ? t[8] : -1;

                const reg = regIdx >= 0 && regIdx < regions.length ? regions[regIdx] : ["-", "-", "-", "-", "-", "-", "-", "-"];
                const pet = petIdx >= 0 && petIdx < petugas.length ? petugas[petIdx] : ["-", "-"];
                const pengawas = pengawasIdx >= 0 && pengawasIdx < petugas.length ? petugas[pengawasIdx] : ["-", "-"];
                const stat = statIdx >= 0 && statIdx < statuses.length ? statuses[statIdx] : "OPEN";
                const tid = t[0];
                const rmk = remarksDict[tid] || "";

                return {
                    id: t[0],
                    codeIdentity: t[1],
                    data1: t[2],
                    status: stat,
                    petugas_username: pet[0],
                    petugas_fullname: pet[1],
                    pengawas_username: pengawas[0],
                    pengawas_fullname: pengawas[1],
                    kab_code: reg[0],
                    kab_name: reg[1],
                    kec_code: reg[2],
                    kec_name: reg[3],
                    desa_code: reg[4],
                    desa_name: reg[5],
                    sls_code: reg[6],
                    sls_name: reg[7],
                    dateModifiedEpoch: t[6],
                    survey_type: t[7] === 0 ? 'se_umum' : 'se_ub',
                    remark: rmk
                };
            });

            console.log("Decompression success. Rebuilt targets:", rebuilt.length);
            return rebuilt;
        } catch (e) {
            console.error("Failed to decompress or rebuild granular data:", e);
            return [];
        }
    };

    let isGranularLoading = false;
    window.GRANULAR_ASSIGNMENTS_DATA = null;

    window.updateGranularStatusFilterOptions = function () {
        const statusSelect = document.getElementById('assign-sls-status-filter');
        if (!statusSelect) return;
        const currentSelectedStatus = statusSelect.value || 'all';
        
        let optionsHTML = `<option value="all">Semua Status</option>`;
        [
            'OPEN', 
            'DRAFT', 
            'SUBMITTED BY Pencacah', 
            'SUBMITTED RESPONDENT', 
            'APPROVED BY Pengawas', 
            'REJECTED BY Pengawas', 
            'EDITED BY Admin Kabupaten', 
            'REVOKED BY Pengawas', 
            'COMPLETED BY Admin Kabupaten', 
            'REJECTED BY Admin Kabupaten'
        ].forEach(s => {
            optionsHTML += `<option value="${s}">${s}</option>`;
        });
        statusSelect.innerHTML = optionsHTML;
        statusSelect.value = currentSelectedStatus;
    };

    
    async function loadGranularAssignmentsData(kabVal = null, surveyTypeFilter = null) {
        if (!kabVal) {
            kabVal = document.getElementById('assign-sls-kab-filter')?.value || 'all';
        }
        if (!surveyTypeFilter) {
            const surveyFilterEl = document.getElementById('assign-sls-survey-filter');
            surveyTypeFilter = surveyFilterEl ? surveyFilterEl.value : (localStorage.getItem('active_assign_subtab') === 'se2026' ? 'se_umum' : 'se_ub');
        }

        const tbody = document.getElementById('assign-sls-table-body');
        
        if (kabVal === 'all') {
            if (tbody) {
                tbody.innerHTML = `<tr><td colspan="12" style="text-align: center; padding: 3rem; color: var(--text-secondary);">Silakan pilih Kabupaten/Kota terlebih dahulu untuk memuat rincian data assignment.</td></tr>`;
            }
            window.GRANULAR_ASSIGNMENTS_DATA = null;
            
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
        } else {
            // Fetch Granular Assignments from Supabase
            const match = kabVal.match(/\[(\d+)\]/);
            if (match && supabaseClient) {
                const code = match[1];
                const fullKabCode = `72${code}`;
                const dbKey = `granular_assignments_${surveyTypeFilter}_${fullKabCode}`;
                
                if (tbody) {
                    tbody.innerHTML = `<tr><td colspan="12" style="text-align: center; padding: 3rem; color: var(--text-secondary);"><div class="loading-spinner" style="display:inline-block; margin-right:0.5rem; width:1.2rem; height:1.2rem; border:2px solid var(--primary); border-top-color:transparent; border-radius:50%; animation:spin 1s linear infinite;"></div> Memuat rincian data assignment dari database...</td></tr>`;
                }
                
                try {
                    console.log(`Fetching granular assignments for ${kabVal} (key: ${dbKey}) from Supabase...`);
                    const { data: dbData, error: dbError } = await supabaseClient
                        .from('dashboard_store')
                        .select('value')
                        .eq('key', dbKey)
                        .single();
                        
                    if (!dbError && dbData && dbData.value) {
                        let payload = dbData.value;
                        if (typeof payload === 'string') {
                            try {
                                payload = JSON.parse(payload);
                            } catch(pe) {
                                console.error("Failed to parse payload string:", pe);
                            }
                        }
                        
                        if (payload && payload.is_chunked) {
                            const totalChunks = payload.total_chunks;
                            console.log(`Key ${dbKey} is chunked into ${totalChunks} chunks. Fetching in parallel...`);
                            
                            // Generate array of keys to fetch: key__chunk_0, key__chunk_1, etc.
                            const chunkKeys = [];
                            for (let i = 0; i < totalChunks; i++) {
                                chunkKeys.push(`${dbKey}__chunk_${i}`);
                            }
                            
                            // Fetch all chunks concurrently
                            const chunkResults = await Promise.all(
                                chunkKeys.map(async (chunkKey) => {
                                    const { data, error } = await supabaseClient
                                        .from('dashboard_store')
                                        .select('value')
                                        .eq('key', chunkKey)
                                        .single();
                                    if (error || !data) {
                                        throw new Error(`Failed to fetch chunk ${chunkKey}: ${error?.message || 'No data'}`);
                                    }
                                    let chunkPayload = data.value;
                                    if (typeof chunkPayload === 'string') {
                                        chunkPayload = JSON.parse(chunkPayload);
                                    }
                                    return chunkPayload.compressed_data || '';
                                })
                            );
                            
                            // Reassemble the compressed data
                            const assembledCompressedData = chunkResults.join('');
                            console.log(`Reassembled compressed data: ${assembledCompressedData.length} chars.`);
                            window.GRANULAR_ASSIGNMENTS_DATA = window.decompressAndParseGranular(assembledCompressedData);
                        } else if (payload && payload.compressed_data) {
                            window.GRANULAR_ASSIGNMENTS_DATA = window.decompressAndParseGranular(payload.compressed_data);
                        } else {
                            window.GRANULAR_ASSIGNMENTS_DATA = payload;
                        }
                        console.log(`Loaded ${window.GRANULAR_ASSIGNMENTS_DATA ? window.GRANULAR_ASSIGNMENTS_DATA.length : 0} granular assignments.`);
                    } else {
                        // Key per-kab not found — try fallback to combined key (e.g. granular_assignments_se_ub)
                        const fallbackKey = `granular_assignments_${surveyTypeFilter}`;
                        console.warn(`Key ${dbKey} not found, trying fallback key: ${fallbackKey}`);
                        try {
                            const { data: fbData, error: fbError } = await supabaseClient
                                .from('dashboard_store')
                                .select('value')
                                .eq('key', fallbackKey)
                                .single();
                            if (!fbError && fbData && fbData.value) {
                                let fbPayload = fbData.value;
                                if (typeof fbPayload === 'string') { try { fbPayload = JSON.parse(fbPayload); } catch(e){} }
                                let allRecords = null;
                                if (fbPayload && fbPayload.compressed_data) {
                                    allRecords = window.decompressAndParseGranular(fbPayload.compressed_data);
                                } else if (Array.isArray(fbPayload)) {
                                    allRecords = fbPayload;
                                }
                                if (allRecords && allRecords.length > 0) {
                                    const cleanKabFb = kabVal.replace(/^\[\d+\]\s*/, '').trim().toUpperCase();
                                    const filtered = allRecords.filter(r => {
                                        const rKab = (r.kab_name || '').replace(/^\[\d+\]\s*/, '').trim().toUpperCase();
                                        return rKab === cleanKabFb;
                                    });
                                    window.GRANULAR_ASSIGNMENTS_DATA = filtered.length > 0 ? filtered : allRecords;
                                    console.log(`Fallback: loaded ${window.GRANULAR_ASSIGNMENTS_DATA.length} records from ${fallbackKey}`);
                                } else {
                                    console.warn(`Fallback key ${fallbackKey} also has no data.`);
                                    window.GRANULAR_ASSIGNMENTS_DATA = null;
                                }
                            } else {
                                console.warn(`Fallback key ${fallbackKey} also not found:`, fbError?.message);
                                window.GRANULAR_ASSIGNMENTS_DATA = null;
                            }
                        } catch (fbEx) {
                            console.error('Fallback fetch error:', fbEx);
                            window.GRANULAR_ASSIGNMENTS_DATA = null;
                        }
                    }
                } catch (e) {
                    console.error("Failed to load granular data from Supabase:", e);
                    window.GRANULAR_ASSIGNMENTS_DATA = null;
                }
            } else {
                window.GRANULAR_ASSIGNMENTS_DATA = null;
            }
        }

        // Fetch Petugas Summary from MySQL
        const summarySection = document.getElementById('petugas-summary-section');
        // Always show the summary section (toggle visible for both Petugas and Desa)
        if (summarySection) summarySection.style.display = 'block';

        if (kabVal !== 'all') {
            const matchCode = kabVal.match(/\[(\d+)\]/);
            const kabCodeParam = !matchCode ? '' : `72${matchCode[1]}`;
            if (window.MYSQL_DATA_STATIC && window.MYSQL_DATA_STATIC[kabCodeParam]) {
                window.PETUGAS_SUMMARY_MYSQL = window.MYSQL_DATA_STATIC[kabCodeParam];
            } else {
                window.PETUGAS_SUMMARY_MYSQL = [];
            }
            if (window.renderPetugasSummaryTable) {
                window.renderPetugasSummaryTable(window.GRANULAR_ASSIGNMENTS_DATA);
            }
        } else {
            // No kab selected: Petugas table shows empty, but Desa view can use IPAS_DATA
            window.PETUGAS_SUMMARY_MYSQL = [];
            if (window.renderPetugasSummaryTable) {
                window.renderPetugasSummaryTable(window.GRANULAR_ASSIGNMENTS_DATA);
            }
        }

        window.updateGranularStatusFilterOptions();
        window.renderGranularAssignmentsTable(true);
    }

    // --- REKAP BELUM DITUGASKAN PER KECAMATAN ---
    window.openRekapBelumModal = function () {
        const modal = document.getElementById('rekap-belum-modal');
        if (modal) {
            modal.style.display = 'flex';
            renderRekapBelum();
        }
    };

    function renderRekapBelum() {
        const tbody = document.getElementById('rekap-belum-modal-tbody');
        const summaryEl = document.getElementById('rekap-belum-modal-summary');
        if (!tbody) return;

        if (!window.GRANULAR_ASSIGNMENTS_DATA) {
            tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:2rem;color:var(--text-secondary);">Data granular belum dimuat. Pilih Kabupaten/Kota terlebih dahulu.</td></tr>`;
            return;
        }

        // Apply same kab + survey type filter as main table
        const kabVal = document.getElementById('assign-sls-kab-filter')?.value || 'all';
        const cleanKabVal = kabVal.replace(/^\[\d+\]\s*/, '').trim().toUpperCase();
        const surveyFilterEl = document.getElementById('assign-sls-survey-filter');
        const surveyTypeFilter = surveyFilterEl ? surveyFilterEl.value :
            (localStorage.getItem('active_assign_subtab') === 'se2026' ? 'se_umum' : 'se_ub');

        const base = window.GRANULAR_ASSIGNMENTS_DATA.filter(r => {
            if (r.survey_type !== surveyTypeFilter) return false;
            if (kabVal !== 'all') {
                const cleanRKab = (r.kab_name || '').replace(/^\[\d+\]\s*/, '').trim().toUpperCase();
                if (cleanRKab !== cleanKabVal) return false;
            }
            return true;
        });

        if (base.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:2rem;color:var(--text-secondary);">Tidak ada data untuk filter aktif saat ini.</td></tr>`;
            if (summaryEl) summaryEl.textContent = '';
            return;
        }

        // Aggregate per kab+kec
        const pivot = {};
        base.forEach(r => {
            const cleanKab = (r.kab_name || '?').replace(/^\[\d+\]\s*/, '').trim();
            const key = `${cleanKab}|||${r.kec_name || '?'}`;
            if (!pivot[key]) pivot[key] = { kab: cleanKab, kec: r.kec_name || '?', total: 0, assigned: 0, unassigned: 0 };
            pivot[key].total++;
            const hasOfficer = !!(r.petugas_username && r.petugas_username !== '-' && r.petugas_username !== '');
            if (hasOfficer) pivot[key].assigned++;
            else pivot[key].unassigned++;
        });

        // Sort by unassigned desc
        const rows = Object.values(pivot).sort((a, b) => b.unassigned - a.unassigned);

        const totalUnassigned = rows.reduce((s, r) => s + r.unassigned, 0);
        const totalAll = rows.reduce((s, r) => s + r.total, 0);
        if (summaryEl) summaryEl.textContent = totalUnassigned > 0
            ? `${totalUnassigned.toLocaleString('id-ID')} usaha belum ditugaskan di ${rows.filter(r => r.unassigned > 0).length} kecamatan`
            : '✅ Semua sudah ditugaskan';

        if (rows.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:2rem;color:#22c55e;font-weight:700;">✅ Semua usaha sudah ditugaskan!</td></tr>`;
            return;
        }

        // Build lookup: key → list of unassigned usaha records
        const unassignedByKec = {};
        base.forEach(r => {
            const hasOfficer = !!(r.petugas_username && r.petugas_username !== '-' && r.petugas_username !== '');
            if (!hasOfficer) {
                const cleanKab = (r.kab_name || '?').replace(/^\[\d+\]\s*/, '').trim();
                const key = `${cleanKab}|||${r.kec_name || '?'}`;
                if (!unassignedByKec[key]) unassignedByKec[key] = [];
                unassignedByKec[key].push(r);
            }
        });

        const tdBase = 'padding: 0.55rem 1rem; border-bottom: 1px solid var(--card-border); vertical-align: middle;';

        const rowsHtml = rows.map((r, i) => {
            const pct = r.total > 0 ? (r.assigned / r.total * 100) : 0;
            const pctColor = pct >= 90 ? '#22c55e' : pct >= 50 ? '#f59e0b' : '#ef4444';
            const barW = Math.round(pct);
            const rowBg = r.unassigned > 0 ? '' : 'background: rgba(34,197,94,0.04);';
            const key = `${r.kab}|||${r.kec}`;
            const safeKey = encodeURIComponent(key);
            const canExpand = r.unassigned > 0;

            return `<tr id="rekap-row-${i}" data-rekap-key="${safeKey}" style="${rowBg} cursor: ${canExpand ? 'pointer' : 'default'};"
                    ${canExpand ? `onclick="window.toggleRekapDetail('${safeKey}', ${i})"` : ''}
                    onmouseenter="this.style.background='${canExpand ? 'var(--hover-bg)' : 'rgba(34,197,94,0.06)'}'"
                    onmouseleave="this.style.background='${r.unassigned > 0 ? '' : 'rgba(34,197,94,0.04)'}'"
                    title="${canExpand ? 'Klik untuk lihat daftar usaha belum ditugaskan' : ''}">
                <td style="${tdBase} text-align: center; font-size: 0.75rem; color: var(--text-secondary);">
                    ${canExpand ? `<span id="rekap-icon-${i}" style="font-size:0.8rem; color:#ef4444;">▶</span>` : `<span style="color:#22c55e;">✓</span>`}
                </td>
                <td style="${tdBase} font-size: 0.8rem; color: var(--text-secondary);">${r.kab}</td>
                <td style="${tdBase} font-weight: 600;">${r.kec}</td>
                <td style="${tdBase} text-align: right; font-weight: 600;">${r.total.toLocaleString('id-ID')}</td>
                <td style="${tdBase} text-align: right; font-weight: 700; color: ${r.unassigned > 0 ? '#ef4444' : '#22c55e'};">
                    ${r.unassigned > 0 ? `<span style="display:inline-flex;align-items:center;gap:0.3rem;">${r.unassigned.toLocaleString('id-ID')} <span style="font-size:0.68rem;color:#ef4444;opacity:0.7;">klik ▼</span></span>` : '✅ 0'}
                </td>
                <td style="${tdBase} text-align: right; color: #22c55e; font-weight: 600;">${r.assigned.toLocaleString('id-ID')}</td>
                <td style="${tdBase} text-align: center;">
                    <div style="display:flex;align-items:center;gap:0.4rem;justify-content:flex-end;">
                        <div style="width:80px;height:6px;background:var(--card-border);border-radius:99px;overflow:hidden;flex-shrink:0;">
                            <div style="height:100%;width:${barW}%;background:${pctColor};border-radius:99px;transition:width 0.4s;"></div>
                        </div>
                        <span style="font-size:0.76rem;font-weight:700;color:${pctColor};min-width:38px;text-align:right;">${pct.toFixed(1)}%</span>
                    </div>
                </td>
            </tr>
            <tr id="rekap-detail-${i}" style="display: none;">
                <td colspan="7" style="padding: 0; background: rgba(239,68,68,0.025);">
                    <div id="rekap-detail-content-${i}" style="padding: 0.5rem 1.5rem 0.75rem;"></div>
                </td>
            </tr>`;
        }).join('');

        tbody.innerHTML = rowsHtml;

        window._rekapRows = rows;
        window._rekapUnassignedByKec = unassignedByKec;

        window.toggleRekapDetail = function (safeKey, idx) {
            const detailRow = document.getElementById(`rekap-detail-${idx}`);
            const icon = document.getElementById(`rekap-icon-${idx}`);
            if (!detailRow) return;

            const isOpen = detailRow.style.display !== 'none';
            detailRow.style.display = isOpen ? 'none' : 'table-row';
            if (icon) icon.textContent = isOpen ? '▶' : '▼';
            if (icon) icon.style.color = isOpen ? '#ef4444' : '#f59e0b';

            if (!isOpen) {
                const key = decodeURIComponent(safeKey);
                const usahaList = (window._rekapUnassignedByKec || {})[key] || [];
                const contentDiv = document.getElementById(`rekap-detail-content-${idx}`);
                if (!contentDiv) return;

                if (usahaList.length === 0) {
                    contentDiv.innerHTML = `<div style="text-align:center;padding:1rem;color:var(--text-secondary);font-size:0.83rem;">Tidak ada usaha belum ditugaskan.</div>`;
                    return;
                }

                const sorted = [...usahaList].sort((a, b) => {
                    const da = (a.desa_name || '').localeCompare(b.desa_name || '');
                    if (da !== 0) return da;
                    return (a.sls_name || '').localeCompare(b.sls_name || '');
                });

                const thS = 'padding: 0.4rem 0.75rem; font-size: 0.71rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; color: var(--text-secondary); background: var(--card-bg); border-bottom: 1.5px solid var(--card-border); white-space: nowrap;';
                const tdS = 'padding: 0.42rem 0.75rem; font-size: 0.8rem; border-bottom: 1px solid var(--card-border);';

                const tableRows = sorted.map((u, j) => `
                    <tr onmouseenter="this.style.background='var(--hover-bg)'" onmouseleave="this.style.background=''">
                        <td style="${tdS} text-align:center; color:var(--text-secondary); font-size:0.72rem;">${j + 1}</td>
                        <td style="${tdS}">${u.desa_name || '-'}</td>
                        <td style="${tdS} color:var(--text-secondary);">${u.sls_name || '-'}</td>
                        <td style="${tdS} font-weight: 600;">${u.data1 || u.target_name || '-'}</td>
                        <td style="${tdS} font-family: monospace; font-size: 0.75rem; color: var(--text-secondary);">${u.codeIdentity || u.target_code || '-'}</td>
                        <td style="${tdS} text-align:center;">
                            <span style="background:rgba(239,68,68,0.1);color:#ef4444;padding:0.15rem 0.5rem;border-radius:99px;font-size:0.72rem;font-weight:700;">Belum</span>
                        </td>
                    </tr>`).join('');

                contentDiv.innerHTML = `
                    <div style="font-size:0.78rem;font-weight:700;color:#ef4444;margin-bottom:0.5rem;padding-top:0.25rem;">
                        ${usahaList.length} usaha belum ditugaskan di ${key.split('|||')[1]}
                    </div>
                    <div style="overflow-x:auto;border-radius:0.5rem;border:1px solid var(--card-border);">
                        <table style="width:100%;border-collapse:collapse;font-family:'Plus Jakarta Sans',sans-serif;">
                            <thead><tr>
                                <th style="${thS} text-align:center; width:38px;">No</th>
                                <th style="${thS}">Desa</th>
                                <th style="${thS}">SLS</th>
                                <th style="${thS}">Nama Usaha</th>
                                <th style="${thS}">Kode</th>
                                <th style="${thS} text-align:center;">Status</th>
                            </tr></thead>
                            <tbody>${tableRows}</tbody>
                        </table>
                    </div>`;
            }
        };

        // Totals footer
        const totalAssigned = rows.reduce((s, r) => s + r.assigned, 0);
        const totalPct = totalAll > 0 ? (totalAssigned / totalAll * 100) : 0;
        const totalPctColor = totalPct >= 90 ? '#22c55e' : totalPct >= 50 ? '#f59e0b' : '#ef4444';
        const footerRow = `<tr style="background: rgba(249,115,22,0.04); border-top: 2px solid var(--card-border);">
            <td style="${tdBase} text-align: center; color: var(--text-secondary); font-size: 0.75rem;" colspan="2"></td>
            <td style="${tdBase} font-weight: 800; color: var(--primary); font-family: 'Outfit', sans-serif;">TOTAL</td>
            <td style="${tdBase} text-align: right; font-weight: 800; font-size: 0.9rem;">${totalAll.toLocaleString('id-ID')}</td>
            <td style="${tdBase} text-align: right; font-weight: 800; color: #ef4444;">${totalUnassigned.toLocaleString('id-ID')}</td>
            <td style="${tdBase} text-align: right; font-weight: 800; color: #22c55e;">${totalAssigned.toLocaleString('id-ID')}</td>
            <td style="${tdBase} text-align: center;">
                <div style="display:flex;align-items:center;gap:0.4rem;justify-content:flex-end;">
                    <div style="width:80px;height:6px;background:var(--card-border);border-radius:99px;overflow:hidden;flex-shrink:0;">
                        <div style="height:100%;width:${Math.round(totalPct)}%;background:${totalPctColor};border-radius:99px;"></div>
                    </div>
                    <span style="font-size:0.76rem;font-weight:800;color:${totalPctColor};min-width:38px;text-align:right;">${totalPct.toFixed(1)}%</span>
                </div>
            </td>
        </tr>`;
        tbody.innerHTML += footerRow;
    }

    // Expose so renderGranularAssignmentsTable can refresh it when open
    window.renderRekapBelum = renderRekapBelum;

    // --- GRANULAR TABLE FILTERS, SORT & RENDER ---

    window.granularCurrentPage = 1;
    window.granularPageLimit = 50;
    window.granularSortField = 'kab';
    window.granularSortAsc = true;

    window.changeGranularLimit = function (limit) {
        window.granularPageLimit = parseInt(limit);
        window.renderGranularAssignmentsTable(true);
    };

    window.sortGranularTable = function (field) {
        if (window.granularSortField === field) {
            window.granularSortAsc = !window.granularSortAsc;
        } else {
            window.granularSortField = field;
            window.granularSortAsc = true;
        }

        const fields = ['kab', 'kec', 'desa', 'sls', 'petugas', 'pengawas', 'target_code', 'target_name', 'status', 'date_modified'];
        fields.forEach(f => {
            const el = document.getElementById(`granular-sort-${f}`);
            if (el) {
                if (f === field) {
                    el.innerText = window.granularSortAsc ? '▲' : '▼';
                } else {
                    el.innerText = '↕';
                }
            }
        });

        window.renderGranularAssignmentsTable(false);
    };

    window.handleGranularSurveyFilterChange = async function () {
        const kabSelect = document.getElementById('assign-sls-kab-filter');
        const surveyFilterEl = document.getElementById('assign-sls-survey-filter');
        if (!surveyFilterEl) return;
        const surveyTypeFilter = surveyFilterEl.value;
        const kabVal = kabSelect ? kabSelect.value : 'all';

        // Reset sub filters to all & disabled
        const kecSelect = document.getElementById('assign-sls-kec-filter');
        const desaSelect = document.getElementById('assign-sls-desa-filter');
        const slsSelect = document.getElementById('assign-sls-sls-filter');
        if (kecSelect) { kecSelect.innerHTML = '<option value="all">Semua Kecamatan</option>'; kecSelect.disabled = true; }
        if (desaSelect) { desaSelect.innerHTML = '<option value="all">Semua Desa</option>'; desaSelect.disabled = true; }
        if (slsSelect) { slsSelect.innerHTML = '<option value="all">Semua SLS</option>'; slsSelect.disabled = true; }

        await loadGranularAssignmentsData(kabVal, surveyTypeFilter);

        // Re-update granular filters from 'kab' level to populate kecamatan if kab is selected
        if (kabVal !== 'all') {
            await window.updateGranularFilters('kab');
        }
    };

    window.updateGranularFilters = async function (changedLevel) {
        const kabVal = document.getElementById('assign-sls-kab-filter')?.value || 'all';
        const kecSelect = document.getElementById('assign-sls-kec-filter');
        const desaSelect = document.getElementById('assign-sls-desa-filter');
        const slsSelect = document.getElementById('assign-sls-sls-filter');
        const statusSelect = document.getElementById('assign-sls-status-filter');

        if (changedLevel === 'kab') {
            const surveyFilterEl = document.getElementById('assign-sls-survey-filter');
            const surveyTypeFilter = surveyFilterEl ? surveyFilterEl.value : (localStorage.getItem('active_assign_subtab') === 'se2026' ? 'se_umum' : 'se_ub');
            await loadGranularAssignmentsData(kabVal, surveyTypeFilter);
        }

        const cleanKabVal = kabVal.replace(/^\[\d+\]\s*/, '').trim().toUpperCase();

        if (changedLevel === 'kab') {
            if (kabVal === 'all') {
                if (kecSelect) { kecSelect.innerHTML = '<option value="all">Semua Kecamatan</option>'; kecSelect.disabled = true; }
                if (desaSelect) { desaSelect.innerHTML = '<option value="all">Semua Desa</option>'; desaSelect.disabled = true; }
                if (slsSelect) { slsSelect.innerHTML = '<option value="all">Semua SLS</option>'; slsSelect.disabled = true; }
            } else {
                const kecs = new Set();
                if (window.GRANULAR_ASSIGNMENTS_DATA) {
                    window.GRANULAR_ASSIGNMENTS_DATA.forEach(r => {
                        if ((r.kab_name || '').toUpperCase() === cleanKabVal && r.kec_name && r.kec_name !== '-') {
                            kecs.add(r.kec_name);
                        }
                    });
                } else if (window.IPAS_DATA) {
                    const surveyFilterEl = document.getElementById('assign-sls-survey-filter');
                    const surveyTypeFilter = surveyFilterEl ? surveyFilterEl.value : (localStorage.getItem('active_assign_subtab') === 'se2026' ? 'se_umum' : 'se_ub');
                    const surveyData = window.IPAS_DATA[surveyTypeFilter] || [];
                    const kabData = surveyData.find(k => k.kabupaten === kabVal);
                    if (kabData && kabData.kecamatan_list) {
                        kabData.kecamatan_list.forEach(k => {
                            if (k.kecamatan && k.kecamatan !== '[000] -') {
                                kecs.add(k.kecamatan);
                            }
                        });
                    }
                }
                const sortedKecs = Array.from(kecs).sort();
                if (kecSelect) {
                    kecSelect.innerHTML = '<option value="all">Semua Kecamatan</option>' +
                        sortedKecs.map(k => `<option value="${k}">${k}</option>`).join('');
                    kecSelect.disabled = false;
                }
                if (desaSelect) { desaSelect.innerHTML = '<option value="all">Semua Desa</option>'; desaSelect.disabled = true; }
                if (slsSelect) { slsSelect.innerHTML = '<option value="all">Semua SLS</option>'; slsSelect.disabled = true; }
            }
        } else if (changedLevel === 'kec') {
            const kecVal = kecSelect?.value || 'all';
            if (kecVal === 'all') {
                if (desaSelect) { desaSelect.innerHTML = '<option value="all">Semua Desa</option>'; desaSelect.disabled = true; }
                if (slsSelect) { slsSelect.innerHTML = '<option value="all">Semua SLS</option>'; slsSelect.disabled = true; }
            } else {
                const desas = new Set();
                if (window.GRANULAR_ASSIGNMENTS_DATA) {
                    window.GRANULAR_ASSIGNMENTS_DATA.forEach(r => {
                        if ((r.kab_name || '').toUpperCase() === cleanKabVal && r.kec_name === kecVal && r.desa_name && r.desa_name !== '-') {
                            desas.add(r.desa_name);
                        }
                    });
                }
                const sortedDesas = Array.from(desas).sort();
                if (desaSelect) {
                    desaSelect.innerHTML = '<option value="all">Semua Desa</option>' +
                        sortedDesas.map(d => `<option value="${d}">${d}</option>`).join('');
                    desaSelect.disabled = false;
                }
                if (slsSelect) { slsSelect.innerHTML = '<option value="all">Semua SLS</option>'; slsSelect.disabled = true; }
            }
        } else if (changedLevel === 'desa') {
            const kecVal = kecSelect?.value || 'all';
            const desaVal = desaSelect?.value || 'all';
            if (desaVal === 'all') {
                if (slsSelect) { slsSelect.innerHTML = '<option value="all">Semua SLS</option>'; slsSelect.disabled = true; }
            } else {
                const slss = new Set();
                if (window.GRANULAR_ASSIGNMENTS_DATA) {
                    window.GRANULAR_ASSIGNMENTS_DATA.forEach(r => {
                        if ((r.kab_name || '').toUpperCase() === cleanKabVal && r.kec_name === kecVal && r.desa_name === desaVal && r.sls_name && r.sls_name !== '-') {
                            slss.add(`${r.sls_code} - ${r.sls_name}`);
                        }
                    });
                }
                const sortedSlss = Array.from(slss).sort();
                if (slsSelect) {
                    slsSelect.innerHTML = '<option value="all">Semua SLS</option>' +
                        sortedSlss.map(s => `<option value="${s.split(' - ')[0]}">${s}</option>`).join('');
                    slsSelect.disabled = false;
                }
            }
        }
        window.updateGranularStatusFilterOptions();
        window.renderGranularAssignmentsTable(true);
    };

    window.petugasSortField = window.petugasSortField || 'pct';
    window.petugasSortOrder = window.petugasSortOrder || -1;

    window.sortPetugasSummary = function (field) {
        if (window.petugasSortField === field) {
            window.petugasSortOrder *= -1;
        } else {
            window.petugasSortField = field;
            window.petugasSortOrder = field === 'name' ? 1 : -1;
        }
        if (window.lastBaseFiltered && window.renderPetugasSummaryTable) {
            window.renderPetugasSummaryTable(window.lastBaseFiltered);
        }
    };

    // ===== GRANULAR SUMMARY VIEW TOGGLE =====
    window.granularSummaryView = window.granularSummaryView || 'petugas';
    window.desaSortField = window.desaSortField || 'total';
    window.desaSortOrder = window.desaSortOrder || -1;

    window.switchGranularSummaryView = function(view) {
        window.granularSummaryView = view;

        const btnPetugas = document.getElementById('btn-summary-petugas');
        const btnDesa = document.getElementById('btn-summary-desa');
        const btnPalu = document.getElementById('btn-summary-palu');
        const petugasContainer = document.getElementById('petugas-summary-table-container');
        const desaContainer = document.getElementById('desa-summary-table-container');
        const paluContainer = document.getElementById('palu-monitoring-container');
        const searchInput = document.getElementById('petugas-summary-search-input');
        const titleEl = document.getElementById('petugas-summary-title');
        const descEl = document.getElementById('petugas-summary-desc');

        // Reset all active states
        btnPetugas?.classList.remove('active');
        btnDesa?.classList.remove('active');
        if (petugasContainer) petugasContainer.style.display = 'none';
        if (desaContainer) desaContainer.style.display = 'none';

        if (view === 'petugas') {
            btnPetugas?.classList.add('active');
            if (petugasContainer) petugasContainer.style.display = 'block';
            if (searchInput) searchInput.placeholder = 'Cari nama petugas...';
            if (titleEl) titleEl.innerHTML = `<svg fill="none" height="18" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" style="margin-right:0.75rem;color:var(--primary);" viewbox="0 0 24 24" width="18"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>Rekapitulasi Capaian per Petugas`;
            if (descEl) descEl.innerHTML = 'Data agregat progres masing-masing petugas (berdasarkan wilayah terpilih di filter atas). <span class="badge bg-primary ms-2" style="font-size:0.7rem; vertical-align:middle;">Live FAST CSV</span>';
        } else {
            btnDesa?.classList.add('active');
            if (desaContainer) desaContainer.style.display = 'block';
            if (searchInput) searchInput.placeholder = 'Cari nama kecamatan/desa...';
            if (titleEl) titleEl.innerHTML = `<svg fill="none" height="18" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" style="margin-right:0.75rem;color:var(--primary);" viewbox="0 0 24 24" width="18"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg>Rekapitulasi Capaian per Kecamatan / Desa`;
            if (descEl) descEl.innerHTML = 'Data progres pengerjaan per kecamatan/desa. <span class="badge bg-secondary ms-2" style="font-size:0.7rem; vertical-align:middle;">Sumber: Data Granular (Detail)</span><br><small class="text-muted mt-1 d-block"><i class="fas fa-info-circle me-1"></i> Data pada tabel ini bergantung pada tarikan Granular terakhir dan mungkin sedikit delay dibandingkan tabel Petugas.</small>';
        }

        if (window.renderPetugasSummaryTable) {
            window.renderPetugasSummaryTable(window.GRANULAR_ASSIGNMENTS_DATA || null);
        }
    };

    window.sortDesaSummary = function(field) {
        if (window.desaSortField === field) {
            window.desaSortOrder *= -1;
        } else {
            window.desaSortField = field;
            window.desaSortOrder = (field === 'desa' || field === 'kec') ? 1 : -1;
        }
        document.querySelectorAll('.sort-icon-desa').forEach(el => { el.textContent = ''; });
        const currentTh = document.querySelector(`[onclick="window.sortDesaSummary('${field}')"] .sort-icon-desa`);
        if (currentTh) currentTh.textContent = window.desaSortOrder === 1 ? ' ▲' : ' ▼';
        if (window.renderPetugasSummaryTable) {
            window.renderPetugasSummaryTable(window.GRANULAR_ASSIGNMENTS_DATA || null);
        }
    };

    window._showPetugasHistory = true;
    window.togglePetugasHistory = function() {
        window._showPetugasHistory = !window._showPetugasHistory;
        const btn = document.getElementById('btn-toggle-history-petugas');
        if (btn) {
            btn.innerHTML = window._showPetugasHistory ? 'Sembunyikan History' : 'Tampilkan History';
            btn.style.background = window._showPetugasHistory ? 'rgba(99,102,241,0.1)' : 'transparent';
        }
        if (window.renderPetugasSummaryTable) {
            window.renderPetugasSummaryTable(window.GRANULAR_ASSIGNMENTS_DATA || null);
        }
    };

    window.renderPetugasSummaryTable = function (data) {
        if (window.granularSummaryView === 'desa') {
            let totalAll = 0, selesaiAll = 0, belumAll = 0, desaMap = {};
            
            if (Array.isArray(data) && data.length > 0) {
                // Granular mode: aggregate per desa from granular assignment records
                data.forEach(r => {
                    const kecName = r.kec_name || '-', desaName = r.desa_name || '-', key = `${kecName} | ${desaName}`;
                    if (!desaMap[key]) desaMap[key] = { kec: kecName, desa: desaName, total: 0, selesai: 0, belum: 0 };
                    desaMap[key].total += 1; totalAll += 1;
                    if (r.status === 'OPEN' || r.status === 'DRAFT') { desaMap[key].belum += 1; belumAll += 1; }
                    else { desaMap[key].selesai += 1; selesaiAll += 1; }
                });
            } else {
                // Fallback: aggregate from IPAS_DATA kecamatan list (always available)
                const surveyFilter = document.getElementById('assign-sls-survey-filter')?.value || 'se_umum';
                const kabFilter = document.getElementById('assign-sls-kab-filter')?.value || 'all';
                const ipasData = window.IPAS_DATA || {};
                const seData = ipasData[surveyFilter] || ipasData['se_umum'] || [];
                
                seData.forEach(kab => {
                    // If a kab is selected, filter to that kab only
                    if (kabFilter !== 'all') {
                        const cleanKab = kabFilter.replace(/^\[\d+\]\s*/, '').trim().toUpperCase();
                        const cleanItemKab = (kab.kabupaten || '').replace(/^\[\d+\]\s*/, '').trim().toUpperCase();
                        if (cleanItemKab !== cleanKab) return;
                    }
                    (kab.kecamatan_list || []).forEach(kec => {
                        if (!kec.kec_name || kec.kec_name === '-') return;
                        const key = `${kec.kec_name} | (data per kecamatan)`;
                        const total = kec.total_prelist || 0;
                        const selesai = kec.total_submitted || 0;
                        const belum = Math.max(0, total - selesai);
                        if (!desaMap[key]) desaMap[key] = { kec: kec.kec_name, desa: '(data per kecamatan)', total: 0, selesai: 0, belum: 0 };
                        desaMap[key].total += total;
                        desaMap[key].selesai += selesai;
                        desaMap[key].belum += belum;
                        totalAll += total; selesaiAll += selesai; belumAll += belum;
                    });
                });
            }
            
            if (totalAll > 0) {
                const pctSelesaiAll = ((selesaiAll / totalAll) * 100).toFixed(1);
                const pctBelumAll = ((belumAll / totalAll) * 100).toFixed(1);
                const petStatTotal = document.getElementById('petugas-stat-total'), petStatSelesai = document.getElementById('petugas-stat-selesai'), petStatBelum = document.getElementById('petugas-stat-belum');
                if (petStatTotal) petStatTotal.textContent = totalAll.toLocaleString('id-ID');
                if (petStatSelesai) petStatSelesai.innerHTML = `${selesaiAll.toLocaleString('id-ID')} <span style="font-size: 0.9rem; opacity: 0.8; font-weight: 500;">(${pctSelesaiAll}%)</span>`;
                if (petStatBelum) petStatBelum.innerHTML = `${belumAll.toLocaleString('id-ID')} <span style="font-size: 0.9rem; opacity: 0.8; font-weight: 500;">(${pctBelumAll}%)</span>`;
            }
            let arr = Object.values(desaMap);
            const searchInput = document.getElementById('petugas-summary-search-input');
            if (searchInput && searchInput.value.trim()) { const term = searchInput.value.toLowerCase().trim(); arr = arr.filter(d => d.desa.toLowerCase().includes(term) || d.kec.toLowerCase().includes(term)); }
            arr.sort((a, b) => {
                let valA, valB;
                switch (window.desaSortField) {
                    case 'kec': valA = a.kec; valB = b.kec; break;
                    case 'desa': valA = a.desa; valB = b.desa; break;
                    case 'belum': valA = a.belum; valB = b.belum; break;
                    case 'selesai': valA = a.selesai; valB = b.selesai; break;
                    case 'pct': valA = (a.total > 0 ? a.selesai / a.total : 0); valB = (b.total > 0 ? b.selesai / b.total : 0); break;
                    default: valA = a.total; valB = b.total; break;
                }
                return (typeof valA === 'string' ? valA.localeCompare(valB) : (valA - valB)) * window.desaSortOrder;
            });
            window.lastDesaSummaryArr = arr;
            const tbody = document.getElementById('desa-summary-table-body');
            if (!tbody) return;
            if (arr.length === 0) { tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; padding: 2rem; color: var(--text-secondary);">${(!data || data.length === 0) ? 'Silakan muat data atau pilih wilayah terlebih dahulu...' : 'Tidak ada desa yang cocok dengan pencarian...'}</td></tr>`; return; }
            let html = '';
            arr.forEach((d, i) => {
                const pct = d.total > 0 ? ((d.selesai / d.total) * 100).toFixed(1) : 0, isComplete = pct === "100.0";
                const badgeHtml = isComplete ? `<div style="background: rgba(34, 197, 94, 0.1); color: var(--color-delivered); border: 1px solid rgba(34, 197, 94, 0.2); padding: 0.25rem 0.5rem; border-radius: 0.5rem; display: inline-flex; align-items: center; gap: 0.25rem; font-size: 0.75rem; font-weight: 700;"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg> Tuntas</div>` : `<div style="display: flex; align-items: center; gap: 0.5rem; width: 100%;"><div style="flex-grow: 1; height: 6px; background: rgba(0,0,0,0.05); border-radius: 3px; overflow: hidden;"><div style="height: 100%; width: ${pct}%; background: var(--primary); border-radius: 3px;"></div></div><span style="font-weight: 700; color: var(--text-primary); min-width: 35px; text-align: right;">${pct}%</span></div>`;
                html += `<tr style="border-bottom: 1px solid var(--border-light); transition: all 0.2s;"><td style="text-align: center; font-weight: 600; color: var(--text-secondary);">${idxReal + 1}</td><td style="font-weight: 600; color: var(--text-primary);">${d.kec}</td><td style="font-weight: 600; color: var(--text-primary);">${d.desa}</td><td style="text-align: center; font-family: monospace; font-weight: 700;">${d.total.toLocaleString('id-ID')}</td><td style="text-align: center; font-family: monospace; color: #ef4444;">${d.belum.toLocaleString('id-ID')}</td><td style="text-align: center; font-family: monospace; color: var(--color-delivered); font-weight: 700;">${d.selesai.toLocaleString('id-ID')}</td><td style="text-align: center;">${badgeHtml}</td></tr>`;
            });
            tbody.innerHTML = html;
            return;
        }

        let totalAll = 0;
        let selesaiAll = 0;
        let belumAll = 0;
        let petugasMap = {};
        
        let mitraMap = {};
        let nameToEmailMap = {};
        if (window.MITRA_DATA && Array.isArray(window.MITRA_DATA)) {
            window.MITRA_DATA.forEach(m => {
                if (m.email) {
                    mitraMap[m.email.trim().toLowerCase()] = m.nama.trim();
                }
                if (m.nama) {
                    const cleanName = m.nama.trim().toLowerCase();
                    mitraMap[cleanName] = m.nama.trim();
                    if (m.email) nameToEmailMap[cleanName] = m.email.trim().toLowerCase();
                }
            });
        }

        // Fall back to mysqlData if at Kabupaten level ONLY for Tojo Una-Una (7209), because Supabase data is outdated for Tojo Una-Una and lacks emails.
        // For other Kabupatens (like Palu), they have fresh granular data, so DO NOT fall back to mysqlData!
        const kabVal = document.getElementById('sls-kab-filter') ? document.getElementById('sls-kab-filter').value : 'all';
        const isKabLevel = kabVal !== 'all' &&
            (document.getElementById('sls-kec-filter') ? document.getElementById('sls-kec-filter').value : 'all') === 'all' &&
            (document.getElementById('sls-desa-filter') ? document.getElementById('sls-desa-filter').value : 'all') === 'all' &&
            (document.getElementById('sls-sls-filter') ? document.getElementById('sls-sls-filter').value : 'all') === 'all';

        // Check if granular data exists.
        const useGranular = Array.isArray(data) && data.length > 0 && !(isKabLevel && kabVal.includes('7209'));

        if (useGranular) {
            data.forEach(r => {
                // Proses Pencacah
                let ukeyPencacah = (r.petugas_username !== '-' && r.petugas_username) ? r.petugas_username.trim().toLowerCase() : null;
                let displayPencacah = (r.petugas_fullname !== '-' && r.petugas_fullname) ? r.petugas_fullname : ukeyPencacah;
                
                if (!ukeyPencacah) {
                    const isCompleted = r.status !== 'OPEN' && r.status !== 'DRAFT';
                    displayPencacah = isCompleted ? 'CAWI / Mandiri (Tanpa Petugas)' : 'Belum Ada Petugas';
                    ukeyPencacah = displayPencacah;
                } else {
                    if (mitraMap[ukeyPencacah]) {
                        displayPencacah = mitraMap[ukeyPencacah];
                    } else if (window.userMap) {
                        let mapped = window.userMap[ukeyPencacah] || window.userMap[ukeyPencacah.split('@')[0]];
                        if (mapped) displayPencacah = mapped;
                    }
                }
 
                if (!petugasMap[ukeyPencacah]) {
                    petugasMap[ukeyPencacah] = { name: displayPencacah, email: r.petugas_username || '-', emails: new Set(), total: 0, selesai: 0, belum: 0 };
                    if (r.petugas_username && r.petugas_username !== '-') {
                        petugasMap[ukeyPencacah].emails.add(r.petugas_username.trim().toLowerCase());
                    }
                }
 
                petugasMap[ukeyPencacah].total += 1;
                totalAll += 1;
 
                if (r.status === 'OPEN' || r.status === 'DRAFT') {
                    petugasMap[ukeyPencacah].belum += 1;
                    belumAll += 1;
                } else {
                    petugasMap[ukeyPencacah].selesai += 1;
                    selesaiAll += 1;
                }

                // Proses Pengawas (agar tidak dobel hitung di totalAll, update hanya untuk map Pengawas)
                let ukeyPengawas = (r.pengawas_username !== '-' && r.pengawas_username) ? r.pengawas_username.trim().toLowerCase() : null;
                if (ukeyPengawas) {
                    let displayPengawas = (r.pengawas_fullname !== '-' && r.pengawas_fullname) ? r.pengawas_fullname : ukeyPengawas;
                    if (mitraMap[ukeyPengawas]) {
                        displayPengawas = mitraMap[ukeyPengawas];
                    } else if (window.userMap) {
                        let mapped = window.userMap[ukeyPengawas] || window.userMap[ukeyPengawas.split('@')[0]];
                        if (mapped) displayPengawas = mapped;
                    }

                    if (!petugasMap[ukeyPengawas]) {
                        petugasMap[ukeyPengawas] = { name: displayPengawas, email: r.pengawas_username, emails: new Set([ukeyPengawas]), total: 0, selesai: 0, belum: 0 };
                    }

                    petugasMap[ukeyPengawas].total += 1;
                    if (r.status === 'OPEN' || r.status === 'DRAFT') {
                        petugasMap[ukeyPengawas].belum += 1;
                    } else {
                        petugasMap[ukeyPengawas].selesai += 1;
                    }
                }
            });
        } else {
            const mysqlData = window.PETUGAS_SUMMARY_MYSQL || [];
            mysqlData.forEach(r => {
                let displayName = r.petugas_fullname || r.petugas_username || 'Belum Ada Petugas';
                if (displayName === '-' || !displayName.trim()) displayName = 'Belum Ada Petugas';
                
                let ukey = (r.petugas_username !== '-' && r.petugas_username) ? r.petugas_username.trim().toLowerCase() : null;
                
                // If MySQL data doesn't have email (which is common for API), recover it from MITRA_DATA
                if (!ukey && displayName !== 'Belum Ada Petugas') {
                    const cleanName = displayName.trim().toLowerCase();
                    if (nameToEmailMap[cleanName]) {
                        ukey = nameToEmailMap[cleanName];
                    }
                }
                
                if (!ukey) {
                    ukey = displayName;
                } else {
                    if (mitraMap[ukey]) {
                        displayName = mitraMap[ukey];
                    } else if (window.userMap) {
                        let mapped = window.userMap[ukey] || window.userMap[ukey.split('@')[0]];
                        if (mapped) displayName = mapped;
                    }
                }
 
                const total = parseInt(r.total_target) || 0;
                const selesai = parseInt(r.selesai) || 0;
                const belum = parseInt(r.belum_selesai) || 0;
 
                if (!petugasMap[ukey]) {
                    // Set email field properly so it shows up in the table column
                    petugasMap[ukey] = { name: displayName, email: ukey !== displayName ? ukey : '-', emails: new Set(), total: 0, selesai: 0, belum: 0 };
                    if (ukey !== displayName) {
                        petugasMap[ukey].emails.add(ukey);
                    }
                }
 
                petugasMap[ukey].total += total;
                petugasMap[ukey].selesai += selesai;
                petugasMap[ukey].belum += belum;
            });
        }

        // --- PREPARE WILAYAH PREFIX ---
        const kabFilterDashboard = document.getElementById('assign-sls-kab-filter')?.value || 'all';
        const kecFilterDashboard = document.getElementById('assign-sls-kec-filter')?.value || 'all';
        
        let resolvedKabPrefix = '';
        const kabPrefixMatch = kabFilterDashboard.match(/\[(\d+)\]/);
        if (kabPrefixMatch) resolvedKabPrefix = kabPrefixMatch[1];

        let resolvedKecPrefix = '';
        const kecPrefixMatch = kecFilterDashboard.match(/\[(\d+)\]/);
        if (kecPrefixMatch) {
            resolvedKecPrefix = kecPrefixMatch[1];
        } else if (kecFilterDashboard !== 'all' && window.IPAS_DATA) {
            const surveyFilterEl = document.getElementById('assign-sls-survey-filter');
            const surveyTypeFilter = surveyFilterEl ? surveyFilterEl.value : (localStorage.getItem('active_assign_subtab') === 'se2026' ? 'se_umum' : 'se_ub');
            const surveyData = window.IPAS_DATA[surveyTypeFilter] || [];
            const kabData = surveyData.find(k => k.kabupaten === kabFilterDashboard);
            if (kabData && kabData.kecamatan_list) {
                const foundKec = kabData.kecamatan_list.find(k => k.kecamatan.toUpperCase().includes(kecFilterDashboard.toUpperCase()));
                if (foundKec) {
                    const foundMatch = foundKec.kecamatan.match(/\[(\d+)\]/);
                    if (foundMatch) resolvedKecPrefix = foundMatch[1];
                }
            }
        }

        // --- SINKRONISASI DENGAN PETUGAS_PROGRESS_MAP (DATA FAST TERBARU) ---
        // KARTU ATAS DIHITUNG ULANG DARI DATA FAST (PENCACAH SAJA AGAR TIDAK DOUBLE COUNT)
        if (window.PETUGAS_PROGRESS_MAP && window.PETUGAS_PROGRESS_MAP['Pencacah']) {
            let realTotalAll = 0;
            let realSelesaiAll = 0;
            let realBelumAll = 0;
            
            for (const [email, pMapData] of Object.entries(window.PETUGAS_PROGRESS_MAP['Pencacah'])) {
                let isPetugasInWilayah = false;
                if ((kabFilterDashboard !== 'all' || kecFilterDashboard !== 'all') && window.PETUGAS_REGION_MAP) {
                    const regions = window.PETUGAS_REGION_MAP[email.toLowerCase()];
                    if (regions && regions.length > 0) {
                        isPetugasInWilayah = regions.some(rc => {
                            if (!rc) return false;
                            let match = true;
                            if (resolvedKabPrefix) match = match && rc.startsWith('72' + resolvedKabPrefix);
                            if (resolvedKabPrefix && resolvedKecPrefix) match = match && rc.startsWith('72' + resolvedKabPrefix + resolvedKecPrefix);
                            return match;
                        });
                    }
                } else {
                    isPetugasInWilayah = true;
                }
                
                if (isPetugasInWilayah) {
                    const pTotal = pMapData.target || 0;
                    const pBelum = (pMapData.open || 0) + (pMapData.draft || 0);
                    const pSelesai = pTotal - pBelum;
                    
                    realTotalAll += pTotal;
                    realSelesaiAll += pSelesai;
                    realBelumAll += pBelum;
                }
            }
            
            const pctSelesaiAll = realTotalAll > 0 ? ((realSelesaiAll / realTotalAll) * 100).toFixed(1) : 0;
            const pctBelumAll = realTotalAll > 0 ? ((realBelumAll / realTotalAll) * 100).toFixed(1) : 0;
            
            const totalEl = document.getElementById('petugas-stat-total');
            const selesaiEl = document.getElementById('petugas-stat-selesai');
            const belumEl = document.getElementById('petugas-stat-belum');
            
            if (totalEl) totalEl.textContent = realTotalAll.toLocaleString('id-ID');
            if (selesaiEl) selesaiEl.innerHTML = `${realSelesaiAll.toLocaleString('id-ID')} <span style="font-size: 0.9rem; opacity: 0.8; font-weight: 500;">(${pctSelesaiAll}%)</span>`;
            if (belumEl) belumEl.innerHTML = `${realBelumAll.toLocaleString('id-ID')} <span style="font-size: 0.9rem; opacity: 0.8; font-weight: 500;">(${pctBelumAll}%)</span>`;
        } else if (Array.isArray(data) && data.length > 0) {
            // Fallback
            const pctSelesaiAll = totalAll > 0 ? ((selesaiAll / totalAll) * 100).toFixed(1) : 0;
            const pctBelumAll = totalAll > 0 ? ((belumAll / totalAll) * 100).toFixed(1) : 0;
            document.getElementById('petugas-stat-total').textContent = totalAll.toLocaleString('id-ID');
            document.getElementById('petugas-stat-selesai').innerHTML = `${selesaiAll.toLocaleString('id-ID')} <span style="font-size: 0.9rem; opacity: 0.8; font-weight: 500;">(${pctSelesaiAll}%)</span>`;
            document.getElementById('petugas-stat-belum').innerHTML = `${belumAll.toLocaleString('id-ID')} <span style="font-size: 0.9rem; opacity: 0.8; font-weight: 500;">(${pctBelumAll}%)</span>`;
        }

        // 2. TABEL PETUGAS: Gunakan murni data dari CSV FAST (window.PETUGAS_PROGRESS_MAP)
        const tbody = document.getElementById('petugas-summary-table-body');
        if (!tbody) return;

        if (kabFilterDashboard === 'all') {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 2.5rem 1rem; color: var(--text-secondary);"><div style="font-size:1.5rem;margin-bottom:0.5rem;">📋</div><div style="font-weight:600;margin-bottom:0.35rem;color:var(--text);">Pilih Kabupaten/Kota terlebih dahulu</div><div style="font-size:0.82rem;">Gunakan dropdown filter di atas untuk memuat data rekap petugas per kabupaten.</div></td></tr>';
            return;
        }

        let arr = [];
        if (!window.currentPetugasTab) window.currentPetugasTab = 'Pencacah'; // Default

        // Update tab UI styling
        const tabPencacah = document.getElementById('tab-pencacah');
        const tabPengawas = document.getElementById('tab-pengawas');
        if (tabPencacah && tabPengawas) {
            if (window.currentPetugasTab === 'Pencacah') {
                tabPencacah.classList.add('active');
                tabPengawas.classList.remove('active');
            } else {
                tabPengawas.classList.add('active');
                tabPencacah.classList.remove('active');
            }
        }

        if (window.PETUGAS_PROGRESS_MAP) {
            ['Pencacah', 'Pengawas'].forEach(roleKey => {
                if (window.PETUGAS_PROGRESS_MAP[roleKey]) {
                    const roleData = window.PETUGAS_PROGRESS_MAP[roleKey];
                    for (const [email, pMapData] of Object.entries(roleData)) {
                        let isPetugasInWilayah = false;
                        if ((kabFilterDashboard !== 'all' || kecFilterDashboard !== 'all') && window.PETUGAS_REGION_MAP) {
                            const regions = window.PETUGAS_REGION_MAP[email.toLowerCase()];
                            if (regions && regions.length > 0) {
                                isPetugasInWilayah = regions.some(rc => {
                                    if (!rc) return false;
                                    let match = true;
                                    if (resolvedKabPrefix) match = match && rc.startsWith('72' + resolvedKabPrefix);
                                    if (resolvedKabPrefix && resolvedKecPrefix) match = match && rc.startsWith('72' + resolvedKabPrefix + resolvedKecPrefix);
                                    return match;
                                });
                            }
                        } else {
                            isPetugasInWilayah = true;
                        }
                        
                        if (!isPetugasInWilayah) {
                            continue;
                        }

                        let displayName = email;
                        if (mitraMap && mitraMap[email]) {
                            displayName = mitraMap[email];
                        } else if (window.userMap) {
                            let mapped = window.userMap[email] || window.userMap[email.split('@')[0]];
                            if (mapped) displayName = mapped;
                        }

                        let pBelum = 0;
                        let pSelesaiReal = 0;

                        if (roleKey === 'Pengawas') {
                            pSelesaiReal = (pMapData.approved || 0) + (pMapData.rejected || 0) + (pMapData.revoked || 0);
                            pBelum = (pMapData.open || 0) + (pMapData.draft || 0) + (pMapData.submitted_pencacah || 0) + 
                                     (pMapData.edited_admin || 0) + (pMapData.completed_admin || 0) + 
                                     (pMapData.submitted_respondent || 0) + (pMapData.edited_pengawas || 0);
                        } else {
                            // Pencacah: Selain Open dan Draft adalah Selesai
                            pBelum = (pMapData.open || 0) + (pMapData.draft || 0);
                            pSelesaiReal = (pMapData.submitted_pencacah || 0) + (pMapData.approved || 0) + (pMapData.rejected || 0) + 
                                           (pMapData.edited_admin || 0) + (pMapData.completed_admin || 0) + (pMapData.submitted_respondent || 0) + 
                                           (pMapData.revoked || 0) + (pMapData.edited_pengawas || 0);
                        }

                        // Total sebaiknya adalah jumlah dari assign aktual (belum + selesai), ATAU target asli jika lebih besar
                        const pTotal = Math.max(pMapData.target || 0, pBelum + pSelesaiReal);
                        // Selalu gunakan pSelesaiReal agar tidak pernah minus atau over-inflated
                        const pSelesai = pSelesaiReal;

                        arr.push({
                            name: displayName,
                            email: email,
                            total: pTotal,
                            selesai: pSelesai,
                            belum: pBelum,
                            role: roleKey,
                            open: pMapData.open || 0,
                            draft: pMapData.draft || 0,
                            submitted_pencacah: pMapData.submitted_pencacah || 0,
                            approved: pMapData.approved || 0,
                            completed_admin: pMapData.completed_admin || 0,
                            rejected: pMapData.rejected || 0,
                            revoked: pMapData.revoked || 0,
                            edited_pengawas: pMapData.edited_pengawas || 0,
                            edited_admin: pMapData.edited_admin || 0,
                            submitted_respondent: pMapData.submitted_respondent || 0
                        });
                    }
                }
            });
        } else {
            arr = Object.values(petugasMap);
        }

        // Jangan tampilkan CAWI / Mandiri atau Belum Ada Petugas di dalam daftar baris agar tidak terlihat menumpuk
        arr = arr.filter(p => p.name !== 'Belum Ada Petugas' && p.name !== 'CAWI / Mandiri (Tanpa Petugas)' && (!p.role || p.role === window.currentPetugasTab));

        const searchInput = document.getElementById('petugas-summary-search-input');
        if (searchInput && searchInput.value.trim()) {
            const term = searchInput.value.toLowerCase().trim();
            arr = arr.filter(p => p.name.toLowerCase().includes(term) || (p.email && p.email.toLowerCase().includes(term)));
        }

        arr.sort((a, b) => {
            let valA, valB;
            // Default to 'pct' (Capaian) if not specified
            const sortField = window.petugasSortField || 'pct';
            const sortOrder = window.petugasSortOrder || -1;
            
            switch (sortField) {
                case 'name': valA = a.name; valB = b.name; break;
                case 'email': valA = a.email || ''; valB = b.email || ''; break;
                case 'belum': valA = a.belum; valB = b.belum; break;
                case 'selesai': valA = a.selesai; valB = b.selesai; break;
                case 'total': valA = a.total; valB = b.total; break;
                case 'pct':
                default:
                    valA = (a.total > 0 ? a.selesai / a.total : 0); 
                    valB = (b.total > 0 ? b.selesai / b.total : 0); 
                    break;
            }
            if (typeof valA === 'string' && typeof valB === 'string') {
                const cmp = valA.localeCompare(valB) * sortOrder;
                if (cmp !== 0) return cmp;
            } else {
                const cmp = (valA - valB) * sortOrder;
                if (cmp !== 0) return cmp;
            }
            
            // Secondary sort by TOTAL TARGET (descending) if there's a tie (e.g. all 0.0% capaian)
            if (a.total !== b.total) {
                return b.total - a.total;
            }
            
            // Tertiary sort alphabetically
            return a.name.localeCompare(b.name);
        });

        // Add global tab switcher
        window.setPetugasTab = function(tabName) {
            window.currentPetugasTab = tabName;
            renderPetugasSummaryTable(window.lastBaseFiltered || []);
        };

        window.lastPetugasSummaryArr = arr;

        if (arr.length === 0) {
            if (!data || data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 2rem; color: var(--text-secondary);">Silakan muat data atau pilih wilayah terlebih dahulu...</td></tr>';
            } else {
                tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 2rem; color: var(--text-secondary);">Tidak ada petugas yang cocok dengan pencarian...</td></tr>';
            }
            return;
        }

        
        const totalPetugas = arr.length;
        const totalPetugasPages = Math.ceil(totalPetugas / window.petugasSummaryPerPage) || 1;
        if (window.petugasSummaryCurrentPage > totalPetugasPages) window.petugasSummaryCurrentPage = totalPetugasPages;
        if (window.petugasSummaryCurrentPage < 1) window.petugasSummaryCurrentPage = 1;
        
        const startPIdx = (window.petugasSummaryCurrentPage - 1) * window.petugasSummaryPerPage;
        const endPIdx = Math.min(startPIdx + window.petugasSummaryPerPage, totalPetugas);
        const paginatedArr = arr.slice(startPIdx, endPIdx);
        
        const petugasInfo = document.getElementById('petugas-summary-pagination-info');
        if (petugasInfo) {
            petugasInfo.textContent = `Menampilkan ${startPIdx + 1} - ${endPIdx} dari ${totalPetugas} Petugas`;
        }
        
        const petugasBtns = document.getElementById('petugas-summary-pagination-buttons');
        if (petugasBtns) {
            let btnsHtml = '';
            btnsHtml += `<button class="page-btn" ${window.petugasSummaryCurrentPage === 1 ? 'disabled' : ''} onclick="window.changePetugasSummaryPage(1)">Awal</button>`;
            btnsHtml += `<button class="page-btn" ${window.petugasSummaryCurrentPage === 1 ? 'disabled' : ''} onclick="window.changePetugasSummaryPage(${window.petugasSummaryCurrentPage - 1})">Sebelumnya</button>`;

            let startPage = Math.max(1, window.petugasSummaryCurrentPage - 2);
            let endPage = Math.min(totalPetugasPages, startPage + 4);
            if (endPage - startPage < 4) {
                startPage = Math.max(1, endPage - 4);
            }

            for (let p = startPage; p <= endPage; p++) {
                btnsHtml += `<button class="page-btn ${p === window.petugasSummaryCurrentPage ? 'active' : ''}" onclick="window.changePetugasSummaryPage(${p})">${p}</button>`;
            }

            btnsHtml += `<button class="page-btn" ${window.petugasSummaryCurrentPage === totalPetugasPages ? 'disabled' : ''} onclick="window.changePetugasSummaryPage(${window.petugasSummaryCurrentPage + 1})">Berikutnya</button>`;
            btnsHtml += `<button class="page-btn" ${window.petugasSummaryCurrentPage === totalPetugasPages ? 'disabled' : ''} onclick="window.changePetugasSummaryPage(${totalPetugasPages})">Akhir</button>`;
            petugasBtns.innerHTML = btnsHtml;
        }

        let html = '';
        paginatedArr.forEach((p, i) => {
            const idxReal = startPIdx + i;

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

            let waHtml = "";
            const emailClean = (p.email || '').toLowerCase().trim();
            if (window.PETUGAS_PHONES && window.PETUGAS_PHONES[emailClean]) {
                const phoneData = window.PETUGAS_PHONES[emailClean];
                if (phoneData.phone) {
                    const waLink = `https://wa.me/${phoneData.phone}`;
                    waHtml = `<a href="${waLink}" target="_blank" onclick="event.stopPropagation();" style="display: inline-flex; align-items: center; color: #25D366; transition: opacity 0.2s;" onmouseover="this.style.opacity='0.7'" onmouseout="this.style.opacity='1'" title="Chat WhatsApp">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" stroke="none"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
                    </a>`;
                }
            }

            let roleBadge = "";
            if (p.role === 'Pengawas') {
                roleBadge = `<span style="font-size: 0.6rem; padding: 2px 6px; background: rgba(249, 115, 22, 0.1); color: var(--primary); border: 1px solid rgba(249, 115, 22, 0.2); border-radius: 4px; font-weight: 700;">PML</span>`;
            } else if (p.role === 'Pencacah') {
                roleBadge = `<span style="font-size: 0.6rem; padding: 2px 6px; background: rgba(59, 130, 246, 0.1); color: #3b82f6; border: 1px solid rgba(59, 130, 246, 0.2); border-radius: 4px; font-weight: 700;">PPL</span>`;
            }

            let deltaHtml = "";
            if (window._showPetugasHistory && window.PETUGAS_HISTORY_MAP) {
                const allDates = Object.keys(window.PETUGAS_HISTORY_MAP).sort();
                allDates.forEach((d, dIdx) => {
                    if (d === "2026-07-09") return; // Hide July 9th
                    
                    let dVal = undefined;
                    let dPct = undefined;
                    let dHtmlDetails = "";
                    
                    if (window.PETUGAS_HISTORY_MAP[d] && window.PETUGAS_HISTORY_MAP[d][p.role] && window.PETUGAS_HISTORY_MAP[d][p.role][p.email]) {
                        const hSnap = window.PETUGAS_HISTORY_MAP[d][p.role][p.email];
                        
                        if (dIdx > 0) {
                            const prevDate = allDates[dIdx-1];
                            if (window.PETUGAS_HISTORY_MAP[prevDate] && window.PETUGAS_HISTORY_MAP[prevDate][p.role] && window.PETUGAS_HISTORY_MAP[prevDate][p.role][p.email]) {
                                const pSnap = window.PETUGAS_HISTORY_MAP[prevDate][p.role][p.email];
                                
                                const getD = (k) => (hSnap[k] || 0) - (pSnap[k] || 0);
                                
                                const dSubPPL = getD('submitted_pencacah');
                                const dSubResp = getD('submitted_respondent');
                                const dAppr = getD('approved');
                                const dRej = getD('rejected');
                                const dRev = getD('revoked');
                                const dEdPml = getD('edited_pengawas');
                                const dEdAdm = getD('edited_admin');
                                const dCompAdm = getD('completed_admin');
                                
                                let target = hSnap.target || p.total || 1;
                                let pTarget = pSnap.target || p.total || 1;
                                let currCum = 0, prevCum = 0;
                                
                                if (p.role === 'Pengawas') {
                                    currCum = (hSnap.approved || 0) + (hSnap.rejected || 0) + (hSnap.revoked || 0);
                                    prevCum = (pSnap.approved || 0) + (pSnap.rejected || 0) + (pSnap.revoked || 0);
                                } else {
                                    // Pencacah: Selain Open dan Draft
                                    currCum = (hSnap.submitted_pencacah || 0) + (hSnap.approved || 0) + (hSnap.rejected || 0) + 
                                              (hSnap.edited_admin || 0) + (hSnap.completed_admin || 0) + (hSnap.submitted_respondent || 0) + 
                                              (hSnap.revoked || 0) + (hSnap.edited_pengawas || 0);
                                    prevCum = (pSnap.submitted_pencacah || 0) + (pSnap.approved || 0) + (pSnap.rejected || 0) + 
                                              (pSnap.edited_admin || 0) + (pSnap.completed_admin || 0) + (pSnap.submitted_respondent || 0) + 
                                              (pSnap.revoked || 0) + (pSnap.edited_pengawas || 0);
                                }
                                
                                dVal = currCum - prevCum;
                                
                                dPct = (currCum / target * 100) - (prevCum / pTarget * 100);
                                
                                if (dSubPPL > 0) dHtmlDetails += `<span style="color:#3b82f6">Submit PPL: +${dSubPPL}</span>`;
                                if (dAppr > 0) dHtmlDetails += `<span style="color:#10b981">Approved: +${dAppr}</span>`;
                                if (dCompAdm > 0) dHtmlDetails += `<span style="color:#8b5cf6">Completed: +${dCompAdm}</span>`;
                                if (dRej > 0) dHtmlDetails += `<span style="color:#ef4444">Rejected: +${dRej}</span>`;
                                if (dRev > 0) dHtmlDetails += `<span style="color:#f43f5e">Revoked: +${dRev}</span>`;
                                if (dEdPml > 0) dHtmlDetails += `<span style="color:#8b5cf6">Edited PML: +${dEdPml}</span>`;
                                if (dEdAdm > 0) dHtmlDetails += `<span style="color:#d946ef">Edited Admin: +${dEdAdm}</span>`;
                                if (dSubResp > 0) dHtmlDetails += `<span style="color:#0ea5e9">Submit Resp: +${dSubResp}</span>`;
                            }
                        }
                    }
                    if (dVal === undefined) {
                        deltaHtml += `<td style="text-align: center; color: var(--text-secondary);">—</td>`;
                    } else {
                        const dColor = dVal > 0 ? '#16a34a' : (dVal === 0 ? '#d97706' : '#dc2626');
                        deltaHtml += `<td style="text-align: center; background: ${dIdx === allDates.length-1 ? 'rgba(99,102,241,0.04)' : 'transparent'};">
                            <div style="font-weight: 700; color: ${dColor}; font-size: 1.05em;">
                                ${dVal > 0 ? '+' : ''}${dVal.toLocaleString('id-ID')}
                                <span style="font-size: 0.75em; opacity: 0.85; margin-left: 2px;">(${dPct > 0 ? '+' : ''}${dPct.toFixed(1).replace('.', ',')}%)</span>
                            </div>
                            <div style="font-size: 0.65rem; color: #94a3b8; margin-top: 4px; display: flex; flex-direction: column; gap: 2px;">
                                ${dHtmlDetails}
                            </div>
                        </td>`;
                    }
                });
            }

            html += `
                <tr style="border-bottom: 1px solid var(--border-light); transition: all 0.2s;">
                    <td style="text-align: center; font-weight: 600; color: var(--text-secondary);">${idxReal + 1}</td>
                    <td style="font-weight: 600; color: var(--text-primary);">
                        <div style="display: flex; align-items: center; gap: 0.5rem;">
                            <div style="width: 24px; height: 24px; border-radius: 50%; background: rgba(249, 115, 22, 0.1); color: var(--primary); display: flex; align-items: center; justify-content: center; font-size: 0.65rem; font-weight: 700;">
                                ${p.name.substring(0, 2).toUpperCase()}
                            </div>
                            <div style="display: flex; flex-direction: column; gap: 2px;">
                                <div style="display: flex; align-items: center; gap: 6px;">
                                    ${p.name} ${roleBadge}
                                </div>
                            </div>
                        </div>
                    </td>
                    <td style="font-size: 0.85rem; font-family: monospace; color: var(--text-secondary);">
                        <div style="display: flex; align-items: center; gap: 0.5rem;">
                            ${p.email}
                            ${waHtml}
                        </div>
                    </td>
                    <td style="text-align: center; font-family: monospace; font-weight: 700;">${p.total.toLocaleString('id-ID')}</td>
                    <td style="text-align: center; font-family: monospace; color: #ef4444;">
                        <div style="font-size: 1.05em; font-weight: 700;">${p.belum.toLocaleString('id-ID')}</div>
                        <div style="font-size: 0.65rem; color: #94a3b8; margin-top: 4px; display: flex; flex-direction: column; gap: 2px;">
                            ${p.open > 0 ? `<span style="color:#64748b">Open: ${p.open}</span>` : ''}
                            ${p.draft > 0 ? `<span style="color:#f59e0b">Draft: ${p.draft}</span>` : ''}
                        </div>
                    </td>
                    <td style="text-align: center; font-family: monospace; color: var(--color-delivered);">
                        <div style="font-size: 1.05em; font-weight: 700;">${p.selesai.toLocaleString('id-ID')}</div>
                        <div style="font-size: 0.65rem; color: #94a3b8; margin-top: 4px; display: flex; flex-direction: column; gap: 2px;">
                            ${p.submitted_pencacah > 0 ? `<span style="color:#3b82f6">Submit PPL: ${p.submitted_pencacah}</span>` : ''}
                            ${p.submitted_respondent > 0 ? `<span style="color:#0ea5e9">Submit Resp: ${p.submitted_respondent}</span>` : ''}
                            ${p.approved > 0 ? `<span style="color:#10b981">Approved: ${p.approved}</span>` : ''}
                            ${p.completed_admin > 0 ? `<span style="color:#8b5cf6">Completed: ${p.completed_admin}</span>` : ''}
                            ${p.rejected > 0 ? `<span style="color:#ef4444">Rejected: ${p.rejected}</span>` : ''}
                            ${p.revoked > 0 ? `<span style="color:#f43f5e">Revoked: ${p.revoked}</span>` : ''}
                            ${p.edited_pengawas > 0 ? `<span style="color:#8b5cf6">Edited PML: ${p.edited_pengawas}</span>` : ''}
                            ${p.edited_admin > 0 ? `<span style="color:#d946ef">Edited Admin: ${p.edited_admin}</span>` : ''}
                        </div>
                    </td>
                    ${deltaHtml}
                    <td style="text-align: center;">${badgeHtml}</td>
                </tr>
            `;
        });
        tbody.innerHTML = html;

        // Render Head
        const thead = document.getElementById('petugas-summary-table-head');
        if (thead) {
            let thHistory = "";
            if (window._showPetugasHistory && window.PETUGAS_HISTORY_MAP) {
                const dates = Object.keys(window.PETUGAS_HISTORY_MAP).sort();
                dates.forEach((d, idx) => {
                    if (d === "2026-07-09") return; // Hide July 9th
                    const isLast = idx === dates.length - 1;
                    const dObj = new Date(d + 'T00:00:00');
                    const label = dObj.toLocaleDateString('id-ID', { day: 'numeric', month: 'short' });
                    const sublabel = isLast ? '<br><span style="font-size:0.6rem;font-weight:400;opacity:0.8;">terakhir</span>' : '<br><span style="font-size:0.6rem;font-weight:400;opacity:0.7;">delta</span>';
                    thHistory += `<th style="text-align: center; width: 75px; ${isLast ? 'background:rgba(99,102,241,0.1);' : ''}">${label}${sublabel}</th>`;
                });
            }
            
            thead.innerHTML = `
                <tr>
                    <th style="width: 60px; text-align: center;">No</th>
                    <th style="text-align: left; cursor: pointer;" onclick="window.sortPetugasSummary('name')">Nama Petugas <span class="sort-icon"></span></th>
                    <th style="text-align: left; cursor: pointer;" onclick="window.sortPetugasSummary('email')">Email / Username <span class="sort-icon"></span></th>
                    <th style="text-align: center; cursor: pointer;" onclick="window.sortPetugasSummary('total')">Total Target <span class="sort-icon"></span></th>
                    <th style="text-align: center; cursor: pointer;" onclick="window.sortPetugasSummary('belum')">Belum Selesai <span class="sort-icon"></span></th>
                    <th style="text-align: center; cursor: pointer;" onclick="window.sortPetugasSummary('selesai')">Selesai <span class="sort-icon"></span></th>
                    ${thHistory}
                    <th style="text-align: center; width: 120px; cursor: pointer;" onclick="window.sortPetugasSummary('pct')">% Capaian <span class="sort-icon"></span></th>
                </tr>
            `;
        }

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
        window.lastPetugasSummaryArr = arr;
    };

    window.downloadPetugasSummaryExcel = function () {
        if (!window.lastPetugasSummaryArr || window.lastPetugasSummaryArr.length === 0) {
            alert("Tidak ada data untuk diunduh.");
            return;
        }
        
        const headers = ["Nama Petugas", "Email / Username", "Role", "Total Target", "Belum Selesai (Total)", "Open", "Draft", "Selesai (Total)", "Submit PPL", "Submit Respondent", "Approved", "Completed Admin", "Rejected", "Revoked", "Edited PML", "Edited Admin"];
        
        let dates = [];
        if (window._showPetugasHistory && window.PETUGAS_HISTORY_MAP) {
            dates = Object.keys(window.PETUGAS_HISTORY_MAP).sort().filter(d => d !== "2026-07-09");
            dates.forEach(d => {
                const dObj = new Date(d + 'T00:00:00');
                headers.push(dObj.toLocaleDateString('id-ID', { day: 'numeric', month: 'short' }) + " (Delta)");
                headers.push(dObj.toLocaleDateString('id-ID', { day: 'numeric', month: 'short' }) + " (%)");
            });
        }
        headers.push("% Capaian");

        const rows = window.lastPetugasSummaryArr.map(p => {
            const row = [
                p.name, p.email, p.role, p.total, p.belum, 
                p.open || 0, p.draft || 0, 
                p.selesai, 
                p.submitted_pencacah || 0, p.submitted_respondent || 0, p.approved || 0, p.completed_admin || 0,
                p.rejected || 0, p.revoked || 0, p.edited_pengawas || 0, p.edited_admin || 0
            ];
            
            if (window._showPetugasHistory && window.PETUGAS_HISTORY_MAP) {
                dates.forEach((d, dIdx) => {
                    let dVal = "";
                    let dPct = "";
                    
                    if (window.PETUGAS_HISTORY_MAP[d] && window.PETUGAS_HISTORY_MAP[d][p.role] && window.PETUGAS_HISTORY_MAP[d][p.role][p.email]) {
                        if (dIdx > 0) {
                            const prevDate = dates[dIdx-1];
                            const hSnap = window.PETUGAS_HISTORY_MAP[d][p.role][p.email];
                            if (window.PETUGAS_HISTORY_MAP[prevDate] && window.PETUGAS_HISTORY_MAP[prevDate][p.role] && window.PETUGAS_HISTORY_MAP[prevDate][p.role][p.email]) {
                                const pSnap = window.PETUGAS_HISTORY_MAP[prevDate][p.role][p.email];
                                
                                const getD = (k) => (hSnap[k] || 0) - (pSnap[k] || 0);
                                if (p.role === 'Pengawas') {
                                    dVal = getD('completed_admin');
                                } else {
                                    dVal = getD('submitted_pencacah') + getD('approved');
                                }
                                
                                let target = hSnap.target || p.total || 1;
                                let pTarget = pSnap.target || p.total || 1;
                                let currCum = p.role === 'Pengawas' ? (hSnap.completed_admin || 0) : ((hSnap.submitted_pencacah || 0) + (hSnap.approved || 0));
                                let prevCum = p.role === 'Pengawas' ? (pSnap.completed_admin || 0) : ((pSnap.submitted_pencacah || 0) + (pSnap.approved || 0));
                                
                                dPct = ((currCum / target * 100) - (prevCum / pTarget * 100)).toFixed(1).replace('.', ',');
                                dVal = dVal > 0 ? "+" + dVal : dVal.toString();
                                dPct = parseFloat(dPct.replace(',','.')) > 0 ? "+" + dPct + "%" : dPct + "%";
                            }
                        }
                    }
                    row.push(dVal);
                    row.push(dPct);
                });
            }
            
            const pct = p.total > 0 ? (p.selesai / p.total * 100).toFixed(1).replace('.', ',') + '%' : '0%';
            row.push(pct);
            
            return row;
        });
        
        exportToCSV(`rekap_progres_petugas_${new Date().toISOString().slice(0,10)}.csv`, headers, rows);
    };

    window.renderGranularAssignmentsTable = function (resetPage = true) {
        const tbody = document.getElementById('assign-sls-table-body');
        if (!tbody) return;

        if (!window.GRANULAR_ASSIGNMENTS_DATA) {
            tbody.innerHTML = `<tr><td colspan="12" style="text-align: center; padding: 2rem; color: var(--text-secondary);">Rincian data target assignment belum dimuat. Silakan ubah filter Kabupaten/Kota.</td></tr>`;
            return;
        }

        if (resetPage) {
            window.granularCurrentPage = 1;
        }

        const kabVal = document.getElementById('assign-sls-kab-filter')?.value || 'all';
        const cleanKabVal = kabVal.replace(/^\[\d+\]\s*/, '').trim().toUpperCase();
        const kecVal = document.getElementById('assign-sls-kec-filter')?.value || 'all';
        const desaVal = document.getElementById('assign-sls-desa-filter')?.value || 'all';
        const slsVal = document.getElementById('assign-sls-sls-filter')?.value || 'all';
        const statusVal = document.getElementById('assign-sls-status-filter')?.value || 'all';
        const searchVal = document.getElementById('assign-sls-search-input')?.value.toLowerCase().trim() || '';

        const surveyFilterEl = document.getElementById('assign-sls-survey-filter');
        const surveyTypeFilter = surveyFilterEl ? surveyFilterEl.value : (localStorage.getItem('active_assign_subtab') === 'se2026' ? 'se_umum' : 'se_ub');

        let baseFiltered = window.GRANULAR_ASSIGNMENTS_DATA.filter(r => {
            if (r.survey_type !== surveyTypeFilter) return false;
            if (kabVal !== 'all' && (r.kab_name || '').toUpperCase() !== cleanKabVal) return false;
            if (kecVal !== 'all' && r.kec_name !== kecVal) return false;
            if (desaVal !== 'all' && r.desa_name !== desaVal) return false;
            if (slsVal !== 'all' && r.sls_code !== slsVal) return false;
            return true;
        });

        if (window.renderPetugasSummaryTable) {
            window.lastBaseFiltered = baseFiltered;
            window.renderPetugasSummaryTable(baseFiltered);
        }

        let filtered = baseFiltered.filter(r => {
            if (statusVal !== 'all' && r.status !== statusVal) return false;

            if (searchVal) {
                const matchText = (
                    (r.data1 || '') + ' ' +
                    (r.petugas_username || '') + ' ' +
                    (r.petugas_fullname || '') + ' ' +
                    (r.pengawas_username || '') + ' ' +
                    (r.pengawas_fullname || '') + ' ' +
                    (r.sls_name || '') + ' ' +
                    (r.sls_code || '') + ' ' +
                    (r.status || '')
                ).toLowerCase();
                if (!matchText.includes(searchVal)) return false;
            }
            return true;
        });

        if (window.granularSortField === 'date_modified') {
            filtered.sort((a, b) => {
                const diff = (a.dateModifiedEpoch || 0) - (b.dateModifiedEpoch || 0);
                return window.granularSortAsc ? diff : -diff;
            });
        } else {
            filtered.sort((a, b) => {
                let valA = '', valB = '';
                switch (window.granularSortField) {
                    case 'kab': valA = a.kab_name || ''; valB = b.kab_name || ''; break;
                    case 'kec': valA = a.kec_name || ''; valB = b.kec_name || ''; break;
                    case 'desa': valA = a.desa_name || ''; valB = b.desa_name || ''; break;
                    case 'sls': valA = a.sls_name || ''; valB = b.sls_name || ''; break;
                    case 'petugas': valA = a.petugas_fullname || ''; valB = b.petugas_fullname || ''; break;
                    case 'pengawas': valA = a.pengawas_fullname || ''; valB = b.pengawas_fullname || ''; break;
                    case 'target_code': valA = a.codeIdentity || ''; valB = b.codeIdentity || ''; break;
                    case 'target_name': valA = a.data1 || ''; valB = b.data1 || ''; break;
                    case 'status': valA = a.status || ''; valB = b.status || ''; break;
                }

                let compare = valA.localeCompare(valB, 'id', { sensitivity: 'base' });
                return window.granularSortAsc ? compare : -compare;
            });
        }

        const totalItems = filtered.length;
        const totalPages = Math.ceil(totalItems / window.granularPageLimit);

        const startIndex = (window.granularCurrentPage - 1) * window.granularPageLimit;
        const endIndex = Math.min(startIndex + window.granularPageLimit, totalItems);
        const paginated = filtered.slice(startIndex, endIndex);

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
            const statusUpper = (r.status || '').toUpperCase();
            let statusBadgeClass = 'table-badge-open';
            if (statusUpper.includes('APPROVED')) {
                statusBadgeClass = 'table-badge-approved';
            } else if (statusUpper.includes('REJECTED')) {
                statusBadgeClass = 'table-badge-rejected';
            } else if (statusUpper.includes('SUBMITTED')) {
                statusBadgeClass = 'table-badge-submitted';
            } else if (statusUpper.includes('REVOKED')) {
                statusBadgeClass = 'table-badge-revoked';
                statusDisplayText = 'Ditarik';
            } else if (statusUpper === 'DRAFT') {
                statusBadgeClass = 'table-badge-submitted';
            }

            const isCompleted = statusUpper !== 'OPEN' && statusUpper !== 'DRAFT';
            const petugasLabel = r.petugas_fullname && r.petugas_fullname !== '-' ?
                `${r.petugas_fullname} <span style="font-size:0.75rem; color:var(--text-secondary); display:block; font-family:monospace;">@${r.petugas_username}</span>` :
                (isCompleted ? '<span style="color:var(--text-secondary); font-weight:700;">CAWI / Mandiri (Tanpa Petugas)</span>' : '<span style="color:var(--text-muted); font-style:italic;">Belum Ditugaskan</span>');

            const pengawasLabel = r.pengawas_fullname && r.pengawas_fullname !== '-' ?
                `${r.pengawas_fullname} <span style="font-size:0.75rem; color:var(--text-secondary); display:block; font-family:monospace;">@${r.pengawas_username}</span>` :
                '<span style="color:var(--text-muted); font-style:italic;">-</span>';

            let formattedDate = '-';
            if (r.dateModifiedEpoch && r.dateModifiedEpoch > 0) {
                try {
                    const dt = new Date(r.dateModifiedEpoch * 1000);
                    const pad = (n) => String(n).padStart(2, '0');
                    formattedDate = `${dt.getFullYear()}-${pad(dt.getMonth() + 1)}-${pad(dt.getDate())} ${pad(dt.getHours())}:${pad(dt.getMinutes())}`;
                } catch (e) { }
            }

            html += `
                <tr style="border-bottom: 1px solid var(--card-border); transition: background-color 0.15s;">
                    <td style="padding: 0.65rem 0.75rem; text-align: center; vertical-align: middle; font-weight: 600; color: var(--text-secondary);">${no}</td>
                    <td style="padding: 0.65rem 0.75rem; text-align: left; vertical-align: middle; font-weight: 600; color: var(--text-primary); font-size: 0.8rem;">${r.kab_name}</td>
                    <td style="padding: 0.65rem 0.75rem; text-align: left; vertical-align: middle; font-size: 0.8rem; color: var(--text-primary);">${r.kec_name}</td>
                    <td style="padding: 0.65rem 0.75rem; text-align: left; vertical-align: middle; font-size: 0.8rem; color: var(--text-primary);">${r.desa_name}</td>
                    <td style="padding: 0.65rem 0.75rem; text-align: left; vertical-align: middle; font-size: 0.8rem; color: var(--text-primary);">${r.sls_name} <span style="font-size:0.7rem; color:var(--text-secondary); display:block; font-family:monospace;">${r.sls_code}</span></td>
                    <td style="padding: 0.65rem 0.75rem; text-align: left; vertical-align: middle; font-size: 0.85rem; color: var(--text-primary);">${petugasLabel}</td>
                    <td style="padding: 0.65rem 0.75rem; text-align: left; vertical-align: middle; font-size: 0.85rem; color: var(--text-primary);">${pengawasLabel}</td>
                    <td style="padding: 0.65rem 0.75rem; text-align: left; vertical-align: middle; font-weight: 600; font-family: monospace; font-size: 0.8rem; color: var(--text-primary);">${r.codeIdentity || '-'}</td>
                    <td style="padding: 0.65rem 0.75rem; text-align: left; vertical-align: middle; font-weight: 700; color: var(--text-primary); font-size: 0.85rem;">${r.data1}</td>
                    <td style="padding: 0.65rem 0.75rem; text-align: center; vertical-align: middle;">
                        <span class="table-badge ${statusBadgeClass}">${r.status}</span>
                    </td>
                    <td style="padding: 0.65rem 0.75rem; text-align: center; vertical-align: middle; font-size: 0.8rem; color: var(--text-primary); white-space: nowrap;">${formattedDate}</td>
                    <td style="padding: 0.65rem 0.75rem; text-align: left; vertical-align: middle; font-size: 0.75rem; color: var(--text-primary); max-width: 250px; word-wrap: break-word; line-height: 1.3;">
                        ${r.remark || '-'}
                    </td>
                </tr>
            `;
        });
        tbody.innerHTML = html;

        const pagInfo = document.getElementById('assign-sls-pagination-info');
        if (pagInfo) {
            pagInfo.innerText = `Menampilkan ${startIndex + 1} - ${endIndex} dari ${totalItems} Target`;
        }

        const pagBtns = document.getElementById('assign-sls-pagination-buttons');
        if (pagBtns) {
            let btnsHtml = '';
            btnsHtml += `<button class="page-btn" ${window.granularCurrentPage === 1 ? 'disabled' : ''} onclick="window.setGranularPage(1)">Awal</button>`;
            btnsHtml += `<button class="page-btn" ${window.granularCurrentPage === 1 ? 'disabled' : ''} onclick="window.setGranularPage(${window.granularCurrentPage - 1})">Sebelumnya</button>`;

            let startPage = Math.max(1, window.granularCurrentPage - 2);
            let endPage = Math.min(totalPages, startPage + 4);
            if (endPage - startPage < 4) {
                startPage = Math.max(1, endPage - 4);
            }

            for (let p = startPage; p <= endPage; p++) {
                btnsHtml += `<button class="page-btn ${p === window.granularCurrentPage ? 'active' : ''}" onclick="window.setGranularPage(${p})">${p}</button>`;
            }

            btnsHtml += `<button class="page-btn" ${window.granularCurrentPage === totalPages ? 'disabled' : ''} onclick="window.setGranularPage(${window.granularCurrentPage + 1})">Berikutnya</button>`;
            btnsHtml += `<button class="page-btn" ${window.granularCurrentPage === totalPages ? 'disabled' : ''} onclick="window.setGranularPage(${totalPages})">Akhir</button>`;
            pagBtns.innerHTML = btnsHtml;
        }

        // Auto-refresh rekap panel if open
        const rekapModal = document.getElementById('rekap-belum-modal');
        const rekapBelumOpen = rekapModal && rekapModal.style.display === 'flex';
        if (rekapBelumOpen && window.renderRekapBelum) {
            window.renderRekapBelum();
        }
    };

    window.setGranularPage = function (page) {
        window.granularCurrentPage = page;
        window.renderGranularAssignmentsTable(false);
    };

    window.downloadGranularAssignCSV = function () {
        if (!window.GRANULAR_ASSIGNMENTS_DATA) return;

        const kabVal = document.getElementById('assign-sls-kab-filter')?.value || 'all';
        const cleanKabVal = kabVal.replace(/^\[\d+\]\s*/, '').trim().toUpperCase();
        const kecVal = document.getElementById('assign-sls-kec-filter')?.value || 'all';
        const desaVal = document.getElementById('assign-sls-desa-filter')?.value || 'all';
        const slsVal = document.getElementById('assign-sls-sls-filter')?.value || 'all';
        const statusVal = document.getElementById('assign-sls-status-filter')?.value || 'all';
        const searchVal = document.getElementById('assign-sls-search-input')?.value.toLowerCase().trim() || '';
        const surveyFilterEl = document.getElementById('assign-sls-survey-filter');
        const surveyTypeFilter = surveyFilterEl ? surveyFilterEl.value : (localStorage.getItem('active_assign_subtab') === 'se2026' ? 'se_umum' : 'se_ub');

        let filtered = window.GRANULAR_ASSIGNMENTS_DATA.filter(r => {
            if (r.survey_type !== surveyTypeFilter) return false;
            if (kabVal !== 'all' && (r.kab_name || '').toUpperCase() !== cleanKabVal) return false;
            if (kecVal !== 'all' && r.kec_name !== kecVal) return false;
            if (desaVal !== 'all' && r.desa_name !== desaVal) return false;
            if (slsVal !== 'all' && r.sls_code !== slsVal) return false;
            if (statusVal !== 'all' && r.status !== statusVal) return false;
            if (searchVal) {
                const matchText = (
                    (r.data1 || '') + ' ' +
                    (r.petugas_username || '') + ' ' +
                    (r.petugas_fullname || '') + ' ' +
                    (r.pengawas_username || '') + ' ' +
                    (r.pengawas_fullname || '') + ' ' +
                    (r.sls_name || '') + ' ' +
                    (r.sls_code || '')
                ).toLowerCase();
                if (!matchText.includes(searchVal)) return false;
            }
            return true;
        });

        if (filtered.length === 0) {
            alert('Tidak ada data untuk diunduh.');
            return;
        }

        let csvContent = '\uFEFFNo;Kabupaten;Kecamatan;Desa;Kode SLS;Nama SLS;Username Petugas;Nama Petugas;Username Pengawas;Nama Pengawas;ID Target;Nama Assignment;Status;Tanggal Update;Jenis Sensus\r\n';
        filtered.forEach((r, idx) => {
            const no = idx + 1;
            const kab = (r.kab_name || '-').replace(/"/g, '""');
            const kec = (r.kec_name || '-').replace(/"/g, '""');
            const desa = (r.desa_name || '-').replace(/"/g, '""');
            const slsCode = r.sls_code || '-';
            const slsName = (r.sls_name || '-').replace(/"/g, '""');
            const petUser = r.petugas_username || '-';
            const petName = (r.petugas_fullname || '-').replace(/"/g, '""');
            const pengawasUser = r.pengawas_username || '-';
            const pengawasName = (r.pengawas_fullname || '-').replace(/"/g, '""');
            const targetId = r.codeIdentity || '-';
            const targetName = (r.data1 || '-').replace(/"/g, '""');
            const status = r.status || 'OPEN';

            let formattedDate = '-';
            if (r.dateModifiedEpoch && r.dateModifiedEpoch > 0) {
                try {
                    const dt = new Date(r.dateModifiedEpoch * 1000);
                    const pad = (n) => String(n).padStart(2, '0');
                    formattedDate = `${dt.getFullYear()}-${pad(dt.getMonth() + 1)}-${pad(dt.getDate())} ${pad(dt.getHours())}:${pad(dt.getMinutes())}`;
                } catch (e) { }
            }

            const type = r.survey_type === 'se_umum' ? 'SE Umum' : 'SE UB';

            csvContent += `"${no}";"${kab}";"${kec}";"${desa}";"${slsCode}";"${slsName}";"${petUser}";"${petName}";"${pengawasUser}";"${pengawasName}";"${targetId}";"${targetName}";"${status}";"${formattedDate}";"${type}"\r\n`;
        });

        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.setAttribute('href', url);
        const fileName = `granular_assignments_${surveyTypeFilter}_${kabVal.replace(/\s+/g, '_')}_${new Date().toISOString().split('T')[0]}.csv`;
        link.setAttribute('download', fileName);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    };

    window.loadGranularAssignmentsData = loadGranularAssignmentsData;
    window.toggleStatsDetail = function (section) {
        const container = document.getElementById(`${section}-stats-expanded`);
        const btn = document.getElementById(`${section}-toggle-detail`);
        if (!container || !btn) return;

        if (container.style.display === 'none') {
            container.style.display = 'flex';
            btn.classList.add('expanded');
            btn.innerHTML = 'Sembunyikan Detail ▲';
        } else {
            container.style.display = 'none';
            btn.classList.remove('expanded');
            btn.innerHTML = section === 'email' ? 'Lihat Kegagalan Email ▼' : 'Lihat Detail Lainnya ▼';
        }
    };

    // ========== ANOMALI FEATURE ==========

    // State untuk data anomali (cache)
    let anomaliDataCache = [];

    // Tampilkan section data (setelah login)
    window.showAnomaliDataSection = function () {
        const userJson = sessionStorage.getItem('anomali_user');
        if (!userJson) return;
        const user = JSON.parse(userJson);

        const loginSec = document.getElementById('anomali-login-section');
        const dataSec = document.getElementById('anomali-data-section');
        const headerActions = document.getElementById('anomali-header-actions');
        if (loginSec) loginSec.style.display = 'none';
        if (dataSec) dataSec.style.display = 'block';
        if (headerActions) headerActions.style.display = 'flex';

        const nameEl = document.getElementById('anomali-user-name');
        const kabEl = document.getElementById('anomali-user-kab');
        if (nameEl) nameEl.textContent = user.nama || user.username;
        if (kabEl) kabEl.textContent = user.kab_code ? `Kode Wilayah: ${user.kab_code}` : '';

        loadAnomaliData();
    };

    // Load data anomali dari Supabase
    async function loadAnomaliData() {
        if (!supabaseClient) {
            renderAnomaliTable([]);
            return;
        }
        const loadingEl = document.getElementById('anomali-loading');
        const tableCard = document.querySelector('#anomali-table')?.closest('.card');
        if (loadingEl) loadingEl.style.display = 'block';
        if (tableCard) tableCard.style.display = 'none';

        try {
            const { data, error } = await supabaseClient
                .from('anomali_data')
                .select('*')
                .order('id', { ascending: true });

            if (error) throw error;

            anomaliDataCache = data || [];
            populateAnomaliKabDropdown(anomaliDataCache);
            populateAnomaliDateDropdown(anomaliDataCache);
            populateAnomaliJenisDropdown(anomaliDataCache);
            updateAnomalInfoBar();
            renderAnomaliTable(anomaliDataCache);
        } catch (e) {
            console.error('Gagal load anomali:', e);
            anomaliDataCache = [];
            renderAnomaliTable([]);
        } finally {
            if (loadingEl) loadingEl.style.display = 'none';
            if (tableCard) tableCard.style.display = 'block';
        }
    }

    // Sort state
    let anomaliSortField = 'pct_biaya';
    let anomaliSortDir = 'desc'; // 'asc' | 'desc'
    let anomaliCurrentPage = 1;
    const ANOMALI_PAGE_SIZE = 50;
    let anomaliFilteredCache = []; // current filtered+sorted dataset for pagination

    // Buffer: perubahan belum disimpan, keyed by row.id
    let anomaliBuf = {};

    window.setAnomaliBuf = function (id, field, value) {
        if (!anomaliBuf[id]) anomaliBuf[id] = {};
        anomaliBuf[id][field] = value;
        // Mark row as dirty
        const row = document.getElementById('anomali-row-' + id);
        if (row) row.style.outline = '2px solid rgba(249,115,22,0.5)';
    };

    // Format rupiah singkat
    function fmtRp(val) {
        if (!val) return '-';
        if (val >= 1e9) return `Rp ${(val / 1e9).toFixed(1)}M`;
        if (val >= 1e6) return `Rp ${(val / 1e6).toFixed(1)}jt`;
        return `Rp ${val.toLocaleString('id-ID')}`;
    }

    // Populate kab dropdown
    function populateAnomaliKabDropdown(data) {
        const sel = document.getElementById('anomali-filter-kab');
        if (!sel) return;
        const kabs = [...new Set(data.map(r => r.kab_code).filter(Boolean))].sort();
        sel.innerHTML = '<option value="">Semua Kab/Kota</option>' +
            kabs.map(k => `<option value="${k}">${k}</option>`).join('');
    }

    // Populate date dropdown dynamically from created_at
    function populateAnomaliDateDropdown(data) {
        const sel = document.getElementById('anomali-filter-date');
        if (!sel) return;
        const dates = [...new Set(data.map(r => {
            if (!r.created_at) return null;
            return r.created_at.substring(0, 10);
        }).filter(Boolean))].sort().reverse();
        
        const fmtDate = (dStr) => {
            try {
                const parts = dStr.split('-');
                const months = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des'];
                return `${parts[2]} ${months[parseInt(parts[1])-1]} ${parts[0]}`;
            } catch(e) {
                return dStr;
            }
        };
        
        sel.innerHTML = '<option value="">Semua Tanggal</option>' +
            dates.map(d => `<option value="${d}">${fmtDate(d)}</option>`).join('');
    }

    // Populate jenis dropdown dynamically from jenis_anomali
    function populateAnomaliJenisDropdown(data) {
        const sel = document.getElementById('anomali-filter-jenis');
        if (!sel) return;
        const jenisList = [...new Set(data.map(r => r.jenis_anomali).filter(Boolean))].sort();
        sel.innerHTML = '<option value="">Semua Jenis</option>' +
            jenisList.map(j => `<option value="${j}">${j.replace('Biaya Produksi ', '')}</option>`).join('');
    }

    // Info bar
    function updateAnomalInfoBar() {
        const el = document.getElementById('anomali-info-bar');
        if (!el || !anomaliDataCache.length) return;
        const total = anomaliDataCache.length;
        const kabs = new Set(anomaliDataCache.map(r => r.kab_code)).size;
        const totalBiaya = anomaliDataCache.reduce((s, r) => s + (r.biaya_produksi || 0), 0);
        el.textContent = `${total} anomali · ${kabs} kab/kota · Total biaya produksi: ${fmtRp(totalBiaya)}`;
    }

    // Render tabel anomali (full rewrite)
    function renderAnomaliTable(data) {
        const tbody = document.getElementById('anomali-tbody');
        const thead = document.getElementById('anomali-thead');
        const emptyEl = document.getElementById('anomali-empty');
        const countTotal = document.getElementById('anomali-count-total');
        const countPending = document.getElementById('anomali-count-pending');
        const countProcess = document.getElementById('anomali-count-process');
        const countDone = document.getElementById('anomali-count-done');
        const showingEl = document.getElementById('anomali-showing');
        const jenisFilter = document.getElementById('anomali-filter-jenis');
        const selectedJenis = jenisFilter ? jenisFilter.value : '';

        if (!tbody || !thead) return;

        // Summary always from full cache
        const allData = anomaliDataCache;
        if (countTotal) countTotal.textContent = allData.length;
        if (countPending) countPending.textContent = allData.filter(r => r.status_anomali == 1).length;
        if (countProcess) countProcess.textContent = allData.filter(r => r.status_anomali == 2).length;
        if (countDone) countDone.textContent = allData.filter(r => r.status_anomali == 3).length;

        // Sort
        const sorted = [...data].sort((a, b) => {
            let av = a[anomaliSortField] ?? '';
            let bv = b[anomaliSortField] ?? '';
            if (anomaliSortField === 'waktu_anomali') {
                av = a.created_at || '';
                bv = b.created_at || '';
            }
            if (anomaliSortField === 'no') { av = a._rowIdx || 0; bv = b._rowIdx || 0; }
            const cmp = typeof av === 'number' ? av - bv : String(av).localeCompare(String(bv), 'id');
            return anomaliSortDir === 'asc' ? cmp : -cmp;
        });

        // Store for pagination
        anomaliFilteredCache = sorted;

        // Build dynamic thead based on selectedJenis
        let dynamicColumnsHTML = '';
        if (selectedJenis && selectedJenis.includes('Missing')) {
            // A3
            dynamicColumnsHTML = `
                <th onclick="sortAnomali('nama_krt')" style="padding: 0.7rem 0.8rem; text-align: left; cursor: pointer; user-select: none; min-width: 160px;">Nama Usaha <span id="sort-icon-nama_krt"></span></th>
                <th style="padding: 0.7rem 0.8rem; text-align: left; min-width: 250px;">Catatan</th>`;
        } else if (selectedJenis && selectedJenis.includes('Biaya Produksi')) {
            // A5
            dynamicColumnsHTML = `
                <th onclick="sortAnomali('nama_krt')" style="padding: 0.7rem 0.8rem; text-align: left; cursor: pointer; user-select: none; min-width: 160px;">Nama Usaha <span id="sort-icon-nama_krt"></span></th>
                <th style="padding: 0.7rem 0.8rem; text-align: left; min-width: 150px;">Catatan</th>
                <th onclick="sortAnomali('pct_biaya')" style="padding: 0.7rem 0.8rem; text-align: center; cursor: pointer; user-select: none; white-space: nowrap; min-width: 90px;">% Biaya <span id="sort-icon-pct_biaya"></span></th>
                <th onclick="sortAnomali('biaya_produksi')" style="padding: 0.7rem 0.8rem; text-align: right; cursor: pointer; user-select: none; white-space: nowrap; min-width: 110px;">Biaya Produksi <span id="sort-icon-biaya_produksi"></span></th>
                <th onclick="sortAnomali('total_pengeluaran')" style="padding: 0.7rem 0.8rem; text-align: right; cursor: pointer; user-select: none; white-space: nowrap; min-width: 130px;">Total Pengeluaran <span id="sort-icon-total_pengeluaran"></span></th>`;
        } else if (selectedJenis && selectedJenis.includes('Keuntungan Usaha')) {
            // A6
            dynamicColumnsHTML = `
                <th onclick="sortAnomali('nama_krt')" style="padding: 0.7rem 0.8rem; text-align: left; cursor: pointer; user-select: none; min-width: 160px;">Nama Usaha <span id="sort-icon-nama_krt"></span></th>
                <th style="padding: 0.7rem 0.8rem; text-align: left; min-width: 200px;">Catatan</th>
                <th onclick="sortAnomali('total_pengeluaran')" style="padding: 0.7rem 0.8rem; text-align: right; cursor: pointer; user-select: none; white-space: nowrap; min-width: 130px;">Total Pengeluaran <span id="sort-icon-total_pengeluaran"></span></th>`;
        } else if (selectedJenis && selectedJenis.includes('Penyertaan Modal')) {
            // A7
            dynamicColumnsHTML = `
                <th onclick="sortAnomali('nama_krt')" style="padding: 0.7rem 0.8rem; text-align: left; cursor: pointer; user-select: none; min-width: 160px;">Nama Usaha <span id="sort-icon-nama_krt"></span></th>
                <th style="padding: 0.7rem 0.8rem; text-align: left; min-width: 250px;">Catatan</th>`;
        } else {
            // Generic / Semua
            dynamicColumnsHTML = `
                <th onclick="sortAnomali('nama_krt')" style="padding: 0.7rem 0.8rem; text-align: left; cursor: pointer; user-select: none; min-width: 160px;">Nama Usaha <span id="sort-icon-nama_krt"></span></th>
                <th style="padding: 0.7rem 0.8rem; text-align: left; min-width: 180px;">Catatan</th>
                <th onclick="sortAnomali('pct_biaya')" style="padding: 0.7rem 0.8rem; text-align: center; cursor: pointer; user-select: none; white-space: nowrap; min-width: 90px;">% Biaya <span id="sort-icon-pct_biaya"></span></th>
                <th onclick="sortAnomali('biaya_produksi')" style="padding: 0.7rem 0.8rem; text-align: right; cursor: pointer; user-select: none; white-space: nowrap; min-width: 110px;">Biaya Produksi <span id="sort-icon-biaya_produksi"></span></th>
                <th onclick="sortAnomali('total_pengeluaran')" style="padding: 0.7rem 0.8rem; text-align: right; cursor: pointer; user-select: none; white-space: nowrap; min-width: 130px;">Total Pengeluaran <span id="sort-icon-total_pengeluaran"></span></th>`;
        }

        thead.innerHTML = `
            <tr style="background: var(--card-bg); border-bottom: 2px solid var(--card-border);">
                <th onclick="sortAnomali('no')" style="padding: 0.7rem 0.8rem; text-align: center; width: 42px; cursor: pointer; user-select: none; white-space: nowrap;">No <span id="sort-icon-no"></span></th>
                <th onclick="sortAnomali('kab_code')" style="padding: 0.7rem 0.8rem; text-align: left; cursor: pointer; user-select: none; white-space: nowrap; min-width: 120px;">Kab/Kota <span id="sort-icon-kab_code"></span></th>
                <th onclick="sortAnomali('jenis_anomali')" style="padding: 0.7rem 0.8rem; text-align: left; cursor: pointer; user-select: none; white-space: nowrap; min-width: 140px;">Jenis Anomali <span id="sort-icon-jenis_anomali"></span></th>
                <th onclick="sortAnomali('waktu_anomali')" style="padding: 0.7rem 0.8rem; text-align: left; cursor: pointer; user-select: none; white-space: nowrap; min-width: 120px;">Tanggal <span id="sort-icon-waktu_anomali"></span></th>
                ${dynamicColumnsHTML}
                <th onclick="sortAnomali('nama_petugas')" style="padding: 0.7rem 0.8rem; text-align: left; cursor: pointer; user-select: none; white-space: nowrap; min-width: 130px;">Nama Petugas <span id="sort-icon-nama_petugas"></span></th>
                <th style="padding: 0.7rem 0.8rem; text-align: left; min-width: 180px;">Tindak Lanjut</th>
                <th onclick="sortAnomali('status_anomali')" style="padding: 0.7rem 0.8rem; text-align: center; cursor: pointer; user-select: none; min-width: 110px;">Status <span id="sort-icon-status_anomali"></span></th>
                <th style="padding: 0.7rem 0.8rem; text-align: center; min-width: 90px; color: var(--text-secondary); font-size: 0.75rem;">Simpan</th>
            </tr>
        `;

        // Update sort icons
        ['no', 'kab_code', 'jenis_anomali', 'waktu_anomali', 'nama_krt', 'pct_biaya', 'biaya_produksi', 'total_pengeluaran', 'status_anomali'].forEach(f => {
            const el = document.getElementById('sort-icon-' + f);
            if (el) el.textContent = f === anomaliSortField ? (anomaliSortDir === 'asc' ? ' ↑' : ' ↓') : '';
        });

        const total = sorted.length;
        const totalAll = allData.length;
        if (showingEl) showingEl.textContent = total < totalAll ? `Tampil ${total} dari ${totalAll}` : `${totalAll} data`;

        if (sorted.length === 0) {
            tbody.innerHTML = '';
            if (emptyEl) emptyEl.style.display = 'block';
            renderAnomaliPagination(0);
            return;
        }
        if (emptyEl) emptyEl.style.display = 'none';

        // Pagination slice
        const totalPages = Math.ceil(sorted.length / ANOMALI_PAGE_SIZE);
        if (anomaliCurrentPage > totalPages) anomaliCurrentPage = totalPages;
        if (anomaliCurrentPage < 1) anomaliCurrentPage = 1;
        const start = (anomaliCurrentPage - 1) * ANOMALI_PAGE_SIZE;
        const pageData = sorted.slice(start, start + ANOMALI_PAGE_SIZE);

        const statusBadge = {
            1: `<span style="display:inline-block;padding:0.2rem 0.6rem;background:rgba(239,68,68,0.1);color:#ef4444;border-radius:99px;font-size:0.75rem;font-weight:700;">Belum</span>`,
            2: `<span style="display:inline-block;padding:0.2rem 0.6rem;background:rgba(245,158,11,0.1);color:#f59e0b;border-radius:99px;font-size:0.75rem;font-weight:700;">Diproses</span>`,
            3: `<span style="display:inline-block;padding:0.2rem 0.6rem;background:rgba(34,197,94,0.1);color:#22c55e;border-radius:99px;font-size:0.75rem;font-weight:700;">Selesai</span>`,
        };

        const fmtDate = (dStr) => {
            if (!dStr) return '-';
            try {
                const parts = dStr.substring(0, 10).split('-');
                const months = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des'];
                return `${parts[2]} ${months[parseInt(parts[1])-1]} ${parts[0]}`;
            } catch(e) {
                return dStr;
            }
        };

        tbody.innerHTML = pageData.map((row, idx) => {
            const pct = row.pct_biaya || 0;
            const pctColor = pct >= 100 ? '#ef4444' : pct >= 80 ? '#f97316' : '#f59e0b';
            const pctBg = pct >= 100 ? 'rgba(239,68,68,0.1)' : pct >= 80 ? 'rgba(249,115,22,0.1)' : 'rgba(245,158,11,0.1)';
            const jenisIcon = (row.jenis_anomali || '').includes('Melebihi') ? '⛔' :
                (row.jenis_anomali || '').includes('Sama') ? '⚠️' :
                (row.jenis_anomali || '').includes('Sangat') ? '🔴' : '🟡';
            const namaUsaha = row.nama_krt || '<span style="color:var(--text-secondary);font-style:italic;">-</span>';
            const globalIdx = start + idx + 1;
            const savedInfo = row.updated_by ? `<div style="font-size:0.68rem;color:var(--text-secondary);margin-top:0.15rem;">✓ ${row.updated_by}</div>` : '';
            
            // Map email/username to real name
            let rawPetugas = row.nama_petugas || '';
            let namaPetugas = rawPetugas;
            
            // Hapus suffix role seperti ' (Pengawas)' atau ' (Pencacah)' untuk lookup
            let cleanUsername = rawPetugas.replace(/\s*\([^)]*\)$/, '').trim();
            
            if (window.userMap) {
                if (window.userMap[cleanUsername]) {
                    namaPetugas = window.userMap[cleanUsername];
                } else if (window.userMap[cleanUsername.toLowerCase()]) {
                    namaPetugas = window.userMap[cleanUsername.toLowerCase()];
                } else if (cleanUsername.includes('@') && window.userMap[cleanUsername.split('@')[0]]) {
                    namaPetugas = window.userMap[cleanUsername.split('@')[0]];
                }
            }
            
            // Jika tidak ketemu di map dan string asli masih berupa email, tetap tampilkan email tapi bersihkan
            if (namaPetugas === rawPetugas && !namaPetugas) {
                namaPetugas = '';
            }

            let dynamicCells = '';
            const cellNamaUsaha = `
                <td style="padding:0.6rem 0.8rem;max-width:180px;">
                    <div style="font-weight:600;font-size:0.82rem;line-height:1.3;">${namaUsaha}</div>
                    ${row.sls_code ? `<div style="font-size:0.72rem;color:var(--text-secondary);margin-top:0.15rem;font-family:monospace;">${row.sls_code}</div>` : ''}
                    ${savedInfo}
                </td>
            `;
            const cellCatatan = `
                <td style="padding:0.6rem 0.8rem;max-width:250px;">
                    ${row.catatan ? `<div style="font-size:0.75rem;color:#d97706;line-height:1.4;font-weight:500;">💡 ${row.catatan}</div>` : '<span style="color:var(--text-secondary);font-size:0.78rem;font-style:italic;">-</span>'}
                </td>
            `;
            const cellPct = `
                <td style="padding:0.6rem 0.8rem;text-align:center;">
                    ${pct > 0 ? `<span style="display:inline-block;padding:0.25rem 0.65rem;background:${pctBg};color:${pctColor};border-radius:99px;font-weight:800;font-size:0.82rem;white-space:nowrap;">${pct}%</span>` : '-'}
                </td>
            `;
            const cellBiaya = `
                <td style="padding:0.6rem 0.8rem;text-align:right;font-weight:600;font-size:0.82rem;white-space:nowrap;">${row.biaya_produksi ? fmtRp(row.biaya_produksi) : '-'}</td>
            `;
            const cellPengeluaran = `
                <td style="padding:0.6rem 0.8rem;text-align:right;font-size:0.82rem;white-space:nowrap;color:var(--text-secondary);">${row.total_pengeluaran ? fmtRp(row.total_pengeluaran) : '-'}</td>
            `;


            if (selectedJenis && selectedJenis.includes('Missing')) {
                dynamicCells = `${cellNamaUsaha}${cellCatatan}`;
            } else if (selectedJenis && selectedJenis.includes('Biaya Produksi')) {
                dynamicCells = `${cellNamaUsaha}${cellCatatan}${cellPct}${cellBiaya}${cellPengeluaran}`;
            } else if (selectedJenis && selectedJenis.includes('Keuntungan Usaha')) {
                dynamicCells = `${cellNamaUsaha}${cellCatatan}${cellPengeluaran}`;
            } else if (selectedJenis && selectedJenis.includes('Penyertaan Modal')) {
                dynamicCells = `${cellNamaUsaha}${cellCatatan}`;
            } else {
                dynamicCells = `${cellNamaUsaha}${cellCatatan}${cellPct}${cellBiaya}${cellPengeluaran}`;
            }

            return `<tr id="anomali-row-${row.id}" style="border-bottom:1px solid var(--card-border);">
                <td style="padding:0.6rem 0.8rem;text-align:center;color:var(--text-secondary);font-size:0.78rem;">${globalIdx}</td>
                <td style="padding:0.6rem 0.8rem;font-weight:600;font-size:0.82rem;white-space:nowrap;">${row.kab_code || '-'}</td>
                <td style="padding:0.6rem 0.8rem;">
                    <span style="font-size:0.78rem;">${jenisIcon} ${(row.jenis_anomali || '-').replace('Biaya Produksi ', '')}</span>
                </td>
                <td style="padding:0.6rem 0.8rem;white-space:nowrap;">${fmtDate(row.created_at)}</td>
                ${dynamicCells}
                <td style="padding:0.6rem 0.8rem;min-width:130px;">
                    ${namaPetugas ? `<div style="font-size:0.8rem;font-weight:600;color:var(--text-primary);">${namaPetugas}</div><div style="font-size:0.7rem;color:var(--text-secondary);">${row.nama_petugas}</div>` : `<span style="color:var(--text-secondary);font-size:0.78rem;font-style:italic;">-</span>`}
                </td>
                <td style="padding:0.6rem 0.8rem;">
                    <textarea rows="2"
                        style="width:100%;min-width:160px;padding:0.3rem 0.5rem;border:1px solid var(--card-border);border-radius:0.4rem;background:var(--input-bg);color:var(--text-primary);font-family:'Plus Jakarta Sans',sans-serif;font-size:0.8rem;resize:vertical;line-height:1.4;"
                        onchange="window.setAnomaliBuf(${row.id},'tindak_lanjut',this.value)"
                        placeholder="Isi tindak lanjut...">${row.tindak_lanjut || ''}</textarea>
                </td>
                <td style="padding:0.6rem 0.8rem;text-align:center;">
                    <select onchange="window.setAnomaliBuf(${row.id},'status_anomali',parseInt(this.value))"
                        style="padding:0.3rem 0.4rem;border:1px solid var(--card-border);border-radius:0.4rem;background:var(--input-bg);color:var(--text-primary);font-family:'Plus Jakarta Sans',sans-serif;font-size:0.78rem;font-weight:600;cursor:pointer;">
                        <option value="1" ${row.status_anomali == 1 ? 'selected' : ''}>Belum</option>
                        <option value="2" ${row.status_anomali == 2 ? 'selected' : ''}>Diproses</option>
                        <option value="3" ${row.status_anomali == 3 ? 'selected' : ''}>Selesai</option>
                    </select>
                </td>
                <td style="padding:0.6rem 0.8rem;text-align:center;">
                    <button onclick="window.saveAnomaliRow(${row.id})"
                        id="save-btn-${row.id}"
                        title="Simpan perubahan baris ini"
                        style="display:inline-flex;align-items:center;gap:0.3rem;padding:0.35rem 0.65rem;background:var(--primary);color:white;border:none;border-radius:0.4rem;cursor:pointer;font-size:0.75rem;font-weight:600;font-family:'Plus Jakarta Sans',sans-serif;white-space:nowrap;">
                        <svg width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/></svg>
                        Simpan
                    </button>
                </td>
            </tr>`;
        }).join('');

        renderAnomaliPagination(sorted.length);
    }

    function renderAnomaliPagination(totalItems) {
        const infoEl = document.getElementById('anomali-pagination-info');
        const btnsEl = document.getElementById('anomali-pagination-buttons');
        const paginationEl = document.getElementById('anomali-pagination');
        if (!infoEl || !btnsEl) return;

        const totalPages = Math.ceil(totalItems / ANOMALI_PAGE_SIZE);
        const start = totalItems === 0 ? 0 : (anomaliCurrentPage - 1) * ANOMALI_PAGE_SIZE + 1;
        const end = Math.min(anomaliCurrentPage * ANOMALI_PAGE_SIZE, totalItems);
        infoEl.textContent = `Menampilkan ${start}–${end} dari ${totalItems} data`;

        if (paginationEl) paginationEl.style.display = totalItems === 0 ? 'none' : 'flex';

        if (totalPages <= 1) { btnsEl.innerHTML = ''; return; }

        const btnStyle = (active) => `padding:0.3rem 0.6rem;border-radius:0.35rem;border:1px solid var(--card-border);background:${active ? 'var(--primary)' : 'var(--card-bg)'};color:${active ? 'white' : 'var(--text-primary)'};font-size:0.78rem;font-weight:600;cursor:pointer;font-family:'Plus Jakarta Sans',sans-serif;`;

        let html = `<button style="${btnStyle(false)}" onclick="window.goAnomaliPage(${anomaliCurrentPage - 1})" ${anomaliCurrentPage === 1 ? 'disabled' : ''}>‹</button>`;

        // Show limited page buttons
        const pages = [];
        for (let p = 1; p <= totalPages; p++) {
            if (p === 1 || p === totalPages || (p >= anomaliCurrentPage - 2 && p <= anomaliCurrentPage + 2)) {
                pages.push(p);
            } else if (pages[pages.length - 1] !== '...') {
                pages.push('...');
            }
        }
        pages.forEach(p => {
            if (p === '...') {
                html += `<span style="padding:0.3rem 0.4rem;color:var(--text-secondary);">…</span>`;
            } else {
                html += `<button style="${btnStyle(p === anomaliCurrentPage)}" onclick="window.goAnomaliPage(${p})">${p}</button>`;
            }
        });

        html += `<button style="${btnStyle(false)}" onclick="window.goAnomaliPage(${anomaliCurrentPage + 1})" ${anomaliCurrentPage === totalPages ? 'disabled' : ''}>›</button>`;
        btnsEl.innerHTML = html;
    }

    window.goAnomaliPage = function (page) {
        const totalPages = Math.ceil(anomaliFilteredCache.length / ANOMALI_PAGE_SIZE);
        if (page < 1 || page > totalPages) return;
        anomaliCurrentPage = page;
        renderAnomaliTable(anomaliFilteredCache);
        // Scroll to top of table
        const tbl = document.getElementById('anomali-table');
        if (tbl) tbl.scrollIntoView({ behavior: 'smooth', block: 'start' });
    };

    // Sort handler
    window.sortAnomali = function (field) {
        if (anomaliSortField === field) {
            anomaliSortDir = anomaliSortDir === 'asc' ? 'desc' : 'asc';
        } else {
            anomaliSortField = field;
            anomaliSortDir = field === 'pct_biaya' || field === 'biaya_produksi' || field === 'total_pengeluaran' ? 'desc' : 'asc';
        }
        anomaliCurrentPage = 1; // reset ke halaman 1 saat sort berubah
        window.filterAnomaliTable();
    };

    // Filter by status via card click
    window.filterByStatus = function (statusVal) {
        const sel = document.getElementById('anomali-filter-status');
        if (sel) sel.value = statusVal;
        window.filterAnomaliTable();
    };

    // Filter tabel anomali
    function applyAnomaliFilter(data, searchVal, statusVal, kabVal, jenisVal, dateVal) {
        const q = (searchVal || '').toLowerCase();
        const s = statusVal || '';
        const k = kabVal || '';
        const j = jenisVal || '';
        const d = dateVal || '';
        return data.filter(row => {
            const matchSearch = !q ||
                (row.nama_krt || '').toLowerCase().includes(q) ||
                (row.kab_code || '').toLowerCase().includes(q) ||
                (row.jenis_anomali || '').toLowerCase().includes(q) ||
                (row.sls_code || '').includes(q);
            const matchStatus = !s || String(row.status_anomali) === s;
            const matchKab = !k || (row.kab_code || '') === k;
            const matchDate = !d || (row.created_at && row.created_at.substring(0, 10) === d);
            const matchJenis = !j || (row.jenis_anomali || '') === j;
            return matchSearch && matchStatus && matchKab && matchJenis && matchDate;
        });
    }

    window.filterAnomaliTable = function () {
        const searchVal = (document.getElementById('anomali-search') || {}).value || '';
        const statusVal = (document.getElementById('anomali-filter-status') || {}).value || '';
        const kabVal = (document.getElementById('anomali-filter-kab') || {}).value || '';
        const jenisVal = (document.getElementById('anomali-filter-jenis') || {}).value || '';
        const dateVal = (document.getElementById('anomali-filter-date') || {}).value || '';
        const filtered = applyAnomaliFilter(anomaliDataCache, searchVal, statusVal, kabVal, jenisVal, dateVal);
        anomaliCurrentPage = 1; // reset ke halaman 1 saat filter berubah
        renderAnomaliTable(filtered);
    };

    // Save single row
    window.saveAnomaliRow = async function (id) {
        if (!supabaseClient) { alert('Supabase tidak tersedia.'); return; }
        const changes = anomaliBuf[id];
        if (!changes || Object.keys(changes).length === 0) {
            alert('Tidak ada perubahan untuk disimpan.');
            return;
        }
        const btn = document.getElementById('save-btn-' + id);
        const row = document.getElementById('anomali-row-' + id);
        const logEl = document.getElementById('anomali-upload-log');

        // Get current user info
        let userInfo = {};
        try { userInfo = JSON.parse(sessionStorage.getItem('anomali_user') || '{}'); } catch (e) { }
        const updatedBy = userInfo.nama || userInfo.username || 'Unknown';
        const updatedAt = new Date().toISOString();

        if (btn) { btn.textContent = '...'; btn.disabled = true; }

        try {
            const payload = { ...changes, updated_by: updatedBy, updated_at: updatedAt };
            const { error } = await supabaseClient
                .from('anomali_data')
                .update(payload)
                .eq('id', id);

            if (error) throw error;

            // Clear buffer for this row
            delete anomaliBuf[id];

            // Update local cache
            const cacheIdx = anomaliDataCache.findIndex(r => r.id === id);
            if (cacheIdx !== -1) {
                Object.assign(anomaliDataCache[cacheIdx], payload);
            }

            // Visual feedback
            if (row) {
                row.style.outline = 'none';
                row.style.background = 'rgba(34,197,94,0.06)';
                setTimeout(() => { if (row) row.style.background = ''; }, 2000);
            }
            if (btn) {
                btn.innerHTML = '<svg width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/></svg> Tersimpan';
                btn.style.background = '#22c55e';
                setTimeout(() => {
                    if (btn) {
                        btn.innerHTML = '<svg width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/></svg> Simpan';
                        btn.style.background = '';
                        btn.disabled = false;
                    }
                }, 2000);
            }

            // Audit log
            if (logEl) {
                const timeStr = new Date().toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' });
                logEl.textContent = `✅ Disimpan oleh ${updatedBy}${userInfo.kab_code ? ' · Kab ' + userInfo.kab_code : ''} · ${timeStr}`;
                logEl.style.display = 'block';
                logEl.style.color = '#16a34a';
                logEl.style.background = 'rgba(34,197,94,0.08)';
                logEl.style.borderColor = 'rgba(34,197,94,0.25)';
            }
        } catch (e) {
            console.error('Save anomali row error:', e);
            if (btn) { btn.textContent = 'Gagal!'; btn.style.background = '#ef4444'; setTimeout(() => { if (btn) { btn.innerHTML = '<svg width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/></svg> Simpan'; btn.style.background = ''; btn.disabled = false; } }, 2000); }
            if (logEl) {
                logEl.textContent = `❌ Gagal menyimpan: ${e.message}`;
                logEl.style.display = 'block';
                logEl.style.color = '#ef4444';
                logEl.style.background = 'rgba(239,68,68,0.08)';
                logEl.style.borderColor = 'rgba(239,68,68,0.25)';
            }
        }
    };

    // Login anomali via Supabase RPC
    window.loginAnomali = async function () {
        const usernameEl = document.getElementById('anomali-username');
        const passwordEl = document.getElementById('anomali-password');
        const errorEl = document.getElementById('anomali-login-error');
        const loginBtn = document.querySelector('#anomali-login-section button');

        const username = (usernameEl?.value || '').trim();
        const password = (passwordEl?.value || '').trim();

        if (!username || !password) {
            if (errorEl) { errorEl.textContent = 'Username dan password wajib diisi!'; errorEl.style.display = 'block'; }
            return;
        }

        if (loginBtn) { loginBtn.textContent = 'Memeriksa...'; loginBtn.disabled = true; }
        if (errorEl) errorEl.style.display = 'none';

        try {
            if (!supabaseClient) throw new Error('Koneksi database tidak tersedia.');

            const { data, error } = await supabaseClient
                .rpc('check_login', { p_username: username, p_password: password });

            if (error) throw error;

            if (data) {
                sessionStorage.setItem('anomali_user', JSON.stringify(data));
                window.showAnomaliDataSection();
            } else {
                if (errorEl) { errorEl.textContent = 'Username atau password salah!'; errorEl.style.display = 'block'; }
            }
        } catch (e) {
            console.error('Login error:', e);
            if (errorEl) { errorEl.textContent = 'Terjadi kesalahan: ' + e.message; errorEl.style.display = 'block'; }
        } finally {
            if (loginBtn) { loginBtn.textContent = 'Masuk'; loginBtn.disabled = false; }
        }
    };

    // Enter key support for login
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') {
            const anomaliSection = document.getElementById('anomali-login-section');
            if (anomaliSection && anomaliSection.style.display !== 'none' &&
                document.getElementById('tab-content-anomali') && document.getElementById('tab-content-anomali').style.display !== 'none') {
                window.loginAnomali();
            }
        }
    });

    // Logout anomali
    window.logoutAnomali = function () {
        sessionStorage.removeItem('anomali_user');
        const loginSec = document.getElementById('anomali-login-section');
        const dataSec = document.getElementById('anomali-data-section');
        const headerActions = document.getElementById('anomali-header-actions');
        if (loginSec) { loginSec.style.display = 'block'; }
        if (dataSec) dataSec.style.display = 'none';
        if (headerActions) headerActions.style.display = 'none';
        const usernameEl = document.getElementById('anomali-username');
        const passwordEl = document.getElementById('anomali-password');
        if (usernameEl) usernameEl.value = '';
        if (passwordEl) passwordEl.value = '';
        anomaliDataCache = [];
    };

    // Download template tindak lanjut (CSV proper format)
    window.downloadAnomalTemplate = function () {
        const data = anomaliDataCache;
        if (!data || data.length === 0) {
            alert('Data anomali belum dimuat. Silakan login terlebih dahulu.');
            return;
        }
        const esc = v => `"${String(v || '').replace(/"/g, '""')}"`;
        // Header: ID(A), Kab(B), Jenis(C), Nama Usaha(D), Nama Petugas(E), Kode SLS(F), % Biaya(G), Biaya Produksi(H), Total Pengeluaran(I), Tindak Lanjut(J), Status(K)
        let csv = 'ID,Kab/Kota,Jenis Anomali,Nama Usaha,Nama Petugas,Kode SLS,% Biaya,Biaya Produksi (Rp),Total Pengeluaran (Rp),Tindak Lanjut,Status (1=Belum/2=Proses/3=Selesai)\r\n';
        data.forEach(row => {
            csv += [
                row.id,
                esc(row.kab_code),
                esc(row.jenis_anomali),
                esc(row.nama_krt),
                esc(row.nama_petugas),
                esc(row.sls_code),
                row.pct_biaya || 0,
                row.biaya_produksi || 0,
                row.total_pengeluaran || 0,
                esc(row.tindak_lanjut),
                row.status_anomali || 1
            ].join(',') + '\r\n';
        });
        const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `anomali_tindaklanjut_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    };


    // Upload hasil tindak lanjut dari CSV
    window.uploadAnomaliTindakLanjut = async function (event) {
        const file = event.target.files[0];
        if (!file) return;
        if (!supabaseClient) { alert('Supabase tidak terhubung!'); return; }

        // Get current user info for audit
        let userInfo = {};
        try { userInfo = JSON.parse(sessionStorage.getItem('anomali_user') || '{}'); } catch (e) { }
        const updatedBy = userInfo.nama || userInfo.username || 'Unknown';
        const updatedAt = new Date().toISOString();
        const logEl = document.getElementById('anomali-upload-log');

        const reader = new FileReader();
        reader.onload = async function (e) {
            try {
                const text = e.target.result;
                // Parse CSV: support both comma and semicolon delimiters
                const rawLines = text.replace(/\r/g, '').split('\n').filter(l => l.trim());
                if (rawLines.length < 2) { alert('File kosong atau tidak valid.'); return; }

                // Detect delimiter from header row
                const delimiter = rawLines[0].includes(';') ? ';' : ',';

                // Simple CSV row parser (handles quoted fields)
                function parseCSVRow(line, delim) {
                    const parts = [];
                    let cur = '', inQuote = false;
                    for (let ci = 0; ci < line.length; ci++) {
                        const ch = line[ci];
                        if (ch === '"') {
                            if (inQuote && line[ci + 1] === '"') { cur += '"'; ci++; }
                            else inQuote = !inQuote;
                        } else if (ch === delim && !inQuote) {
                            parts.push(cur); cur = '';
                        } else { cur += ch; }
                    }
                    parts.push(cur);
                    return parts;
                }

                const allParsed = [];
                const skipped = [];

                for (let i = 1; i < rawLines.length; i++) {
                    const parts = parseCSVRow(rawLines[i], delimiter);
                    // New format: ID(0),Kab(1),Jenis(2),Nama(3),Petugas(4),SLS(5),%Biaya(6),BiayaProd(7),TotalPeng(8),TindakLanjut(9),Status(10)
                    const isNewFormat = parts.length >= 11;
                    const id = parseInt(parts[0]);
                    if (isNaN(id)) continue;

                    // Fallback to old format if less than 11 columns
                    const tindak_lanjut = (isNewFormat ? parts[9] : parts.length >= 9 ? parts[7] : parts[5] || parts[6] || '').replace(/^"|"$/g, '').replace(/""/g, '"').trim();
                    const status_anomali = parseInt(isNewFormat ? parts[10] : parts.length >= 9 ? parts[8] : parts[6]) || 1;

                    // SMART MERGE: skip baris yang tidak diubah
                    if (!tindak_lanjut && status_anomali === 1) {
                        skipped.push(id);
                        continue;
                    }

                    allParsed.push({ id, tindak_lanjut, status_anomali });
                }

                if (allParsed.length === 0) {
                    alert(`Tidak ada baris yang diisi.\n\nPastikan kolom "Tindak Lanjut" sudah diisi atau status sudah diubah dari 1.\n\n(${skipped.length} baris kosong dilewati otomatis)`);
                    return;
                }

                // Konfirmasi sebelum upload
                const confirmed = confirm(
                    `📤 Akan mengupload ${allParsed.length} baris yang sudah diisi.\n` +
                    `⏭️ ${skipped.length} baris kosong akan DILEWATI (tidak mengubah data orang lain).\n\n` +
                    `Upload sebagai: ${updatedBy}${userInfo.kab_code ? ' (Kab ' + userInfo.kab_code + ')' : ''}\n\n` +
                    `Lanjutkan?`
                );
                if (!confirmed) return;

                let successCount = 0;
                for (const upd of allParsed) {
                    const { id, ...fields } = upd;
                    // Tambahkan audit trail ke setiap baris yang diupdate
                    const { error } = await supabaseClient.from('anomali_data').update({
                        ...fields,
                        updated_by: updatedBy,
                        updated_at: updatedAt
                    }).eq('id', id);
                    if (!error) successCount++;
                }

                // Show audit log
                if (logEl) {
                    const timeStr = new Date().toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' });
                    logEl.textContent = `✅ Upload berhasil: ${successCount}/${allParsed.length} baris diupdate oleh ${updatedBy}${userInfo.kab_code ? ' · Kab ' + userInfo.kab_code : ''} · ${timeStr}`;
                    logEl.style.display = 'block';
                    logEl.style.color = '#16a34a';
                    logEl.style.background = 'rgba(34,197,94,0.08)';
                    logEl.style.borderColor = 'rgba(34,197,94,0.25)';
                }

                alert(`✅ Berhasil: ${successCount} baris diupdate.\n⏭️ ${skipped.length} baris kosong dilewati (aman, tidak menimpa data lain).`);
                await loadAnomaliData();
            } catch (err) {
                if (logEl) {
                    logEl.textContent = `❌ Upload gagal: ${err.message}`;
                    logEl.style.display = 'block';
                    logEl.style.color = '#ef4444';
                    logEl.style.background = 'rgba(239,68,68,0.08)';
                    logEl.style.borderColor = 'rgba(239,68,68,0.25)';
                }
                alert('Gagal memproses file: ' + err.message);
            }
        };
        reader.readAsText(file, 'UTF-8');
        event.target.value = '';
    };

    // ========== TABULASI ==========
    let tabulasiOpen = false;

    window.toggleTabulasi = function () {
        tabulasiOpen = !tabulasiOpen;
        const sec = document.getElementById('tabulasi-section');
        const icon = document.getElementById('tabulasi-toggle-icon');
        if (sec) sec.style.display = tabulasiOpen ? 'block' : 'none';
        if (icon) icon.textContent = tabulasiOpen ? '▼' : '▶';
        if (tabulasiOpen && anomaliDataCache.length > 0) renderTabulasi();
    };

    function renderTabulasi() {
        const container = document.getElementById('tabulasi-container');
        if (!container || anomaliDataCache.length === 0) return;

        const data = anomaliDataCache;

        // Build pivot: kab → { sama, sangat, dominan, total, biaya, belum, diproses, selesai }
        const pivot = {};
        data.forEach(row => {
            const kab = row.kab_code || 'Lainnya';
            if (!pivot[kab]) pivot[kab] = { melebihi: 0, sama: 0, sangat: 0, dominan: 0, total: 0, biaya: 0, belum: 0, diproses: 0, selesai: 0 };
            const p = pivot[kab];
            p.total++;
            p.biaya += row.biaya_produksi || 0;
            if ((row.jenis_anomali || '').includes('Melebihi')) p.melebihi++;
            else if ((row.jenis_anomali || '').includes('Sama')) p.sama++;
            else if ((row.jenis_anomali || '').includes('Sangat')) p.sangat++;
            else p.dominan++;
            if (row.status_anomali == 3) p.selesai++;
            else if (row.status_anomali == 2) p.diproses++;
            else p.belum++;
        });

        const kabs = Object.keys(pivot).sort();
        const totals = { melebihi: 0, sama: 0, sangat: 0, dominan: 0, total: 0, biaya: 0, belum: 0, diproses: 0, selesai: 0 };
        kabs.forEach(k => {
            Object.keys(totals).forEach(f => totals[f] += pivot[k][f]);
        });

        const thStyle = 'padding: 0.55rem 0.75rem; font-size: 0.75rem; font-weight: 700; text-align: center; white-space: nowrap; letter-spacing: 0.04em; text-transform: uppercase; background: var(--card-bg); color: var(--text-secondary); border-bottom: 2px solid var(--card-border);';
        const thLeftStyle = thStyle.replace('text-align: center', 'text-align: left');
        const tdStyle = (align = 'center') => `padding: 0.5rem 0.75rem; font-size: 0.82rem; text-align: ${align}; border-bottom: 1px solid var(--card-border); vertical-align: middle;`;

        const badge = (n, color, bg) => n > 0 ? `<span style="display:inline-block;padding:0.15rem 0.55rem;background:${bg};color:${color};border-radius:99px;font-weight:700;font-size:0.78rem;">${n}</span>` : `<span style="color:var(--text-secondary);font-size:0.78rem;">-</span>`;

        const rows = kabs.map(kab => {
            const p = pivot[kab];
            const pct = p.total > 0 ? Math.round((p.selesai / p.total) * 100) : 0;
            const pctColor = pct >= 80 ? '#22c55e' : pct >= 40 ? '#f59e0b' : '#ef4444';
            const barW = pct;
            return `<tr onmouseenter="this.style.background='var(--hover-bg)'" onmouseleave="this.style.background=''">
                <td style="${tdStyle('left')} font-weight: 600;">${kab}</td>
                <td style="${tdStyle()}">${badge(p.melebihi, '#ef4444', 'rgba(239,68,68,0.1)')}</td>
                <td style="${tdStyle()}">${badge(p.sama, '#ef4444', 'rgba(239,68,68,0.1)')}</td>
                <td style="${tdStyle()}">${badge(p.sangat, '#f97316', 'rgba(249,115,22,0.1)')}</td>
                <td style="${tdStyle()}">${badge(p.dominan, '#f59e0b', 'rgba(245,158,11,0.1)')}</td>
                <td style="${tdStyle()} font-weight: 700;">${p.total}</td>
                <td style="${tdStyle('right')} font-size: 0.78rem; color: var(--text-secondary);">${fmtRp(p.biaya)}</td>
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
        }).join('');

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
            <td style="${tdStyle('right')} font-weight: 700; font-size: 0.78rem;">${fmtRp(totals.biaya)}</td>
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
                        <th style="${thLeftStyle} min-width:140px;">Kab/Kota</th>
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
                * Klik header tabel di bawah untuk sort. TL = Tindak Lanjut. Klik baris kab/kota untuk filter tabel.
            </div>`;

        // Make rows clickable to filter
        const trs = container.querySelectorAll('tbody tr');
        trs.forEach((tr, i) => {
            tr.style.cursor = 'pointer';
            tr.title = 'Klik untuk filter ke ' + kabs[i];
            tr.addEventListener('click', () => {
                const sel = document.getElementById('anomali-filter-kab');
                if (sel) {
                    sel.value = kabs[i];
                    window.filterAnomaliTable();
                    // Scroll to table
                    const tbl = document.getElementById('anomali-table');
                    if (tbl) tbl.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            });
        });
    }

    // ========== END ANOMALI FEATURE ==========

    // Initial Execution
    fetchDataAndRender().then(() => {
        // Restore active tab from localStorage, default to 'se_umum'
        let activeTab = localStorage.getItem('active_tab') || 'se_umum';
        if (activeTab === 'target') {
            activeTab = 'se_umum';
        }
        window.switchTab(activeTab);
    });
});

// ========== EXCEL DOWNLOAD FEATURE ==========

window.openExcelDownloadModal = function () {
    const modal = document.getElementById('excel-download-modal');
    if (!modal) return;

    // Populate kabkot checklist from IPAS_DATA
    const checklist = document.getElementById('excel-kab-checklist');
    const surveyType = document.getElementById('assign-sls-survey-filter')?.value || 'se_umum';
    document.getElementById('excel-survey-type').value = surveyType;

    const ipasData = window.IPAS_DATA || {};
    const seData = ipasData[surveyType] || ipasData['se_umum'] || [];
    const kabList = seData.map(k => k.kabupaten).filter(Boolean);

    if (checklist) {
        checklist.innerHTML = kabList.length === 0
            ? '<span style="color:var(--text-secondary);font-size:0.82rem;">Data kabupaten belum tersedia.</span>'
            : kabList.map(kab => {
                const val = kab.replace(/"/g, '&quot;');
                return `<label style="display:flex;align-items:center;gap:0.5rem;cursor:pointer;padding:0.4rem 0.6rem;border-radius:0.5rem;background:var(--card-bg);border:1px solid var(--card-border);font-size:0.82rem;font-weight:500;color:var(--text);">
                    <input type="checkbox" class="excel-kab-check" value="${val}" checked style="accent-color:var(--primary);width:14px;height:14px;">
                    ${kab}
                </label>`;
            }).join('');
    }

    modal.style.display = 'flex';
};

window.onExcelTypeChange = function () {
    const tipe = document.querySelector('input[name="excel-type"]:checked')?.value || 'summary';
    const summaryInfo = document.getElementById('excel-summary-info');
    const kabSection = document.getElementById('excel-kab-section');
    const subtitle = document.getElementById('excel-modal-subtitle');
    const lblSummary = document.getElementById('lbl-type-summary');
    const lblRaw = document.getElementById('lbl-type-raw');
    if (tipe === 'summary') {
        if (summaryInfo) summaryInfo.style.display = 'flex';
        if (kabSection) kabSection.style.display = 'none';
        if (subtitle) subtitle.textContent = 'Export tabel rekap petugas yang sedang tampil';
        if (lblSummary) { lblSummary.style.borderColor = 'var(--primary)'; lblSummary.style.color = 'var(--primary)'; lblSummary.style.background = 'rgba(249,115,22,0.06)'; }
        if (lblRaw) { lblRaw.style.borderColor = 'var(--card-border)'; lblRaw.style.color = 'var(--text)'; lblRaw.style.background = 'var(--card-bg)'; }
    } else {
        if (summaryInfo) summaryInfo.style.display = 'none';
        if (kabSection) kabSection.style.display = 'block';
        if (subtitle) subtitle.textContent = 'Pilih kabupaten yang ingin diunduh datanya';
        if (lblRaw) { lblRaw.style.borderColor = 'var(--primary)'; lblRaw.style.color = 'var(--primary)'; lblRaw.style.background = 'rgba(249,115,22,0.06)'; }
        if (lblSummary) { lblSummary.style.borderColor = 'var(--card-border)'; lblSummary.style.color = 'var(--text)'; lblSummary.style.background = 'var(--card-bg)'; }
    }
};

window.executeExcelDownload = async function () {
    const statusEl = document.getElementById('excel-download-status');
    const btn = document.getElementById('btn-excel-execute');

    const tipeEl = document.querySelector('input[name="excel-type"]:checked');
    const tipe = tipeEl ? tipeEl.value : 'summary';
    const surveyType = document.getElementById('excel-survey-type')?.value || 'se_umum';
    const surveyLabel = surveyType === 'se_umum' ? 'SE_Umum' : 'SE_UB';
    const today = new Date().toISOString().slice(0, 10);

    // Get current kab from filter for filename
    const kabFilterEl = document.getElementById('assign-sls-kab-filter');
    const kabFilterVal = kabFilterEl ? kabFilterEl.value : 'all';
    const kabLabel = kabFilterVal === 'all' ? 'Semua_Kab'
        : kabFilterVal.replace(/^\[\d+\]\s*/, '').trim().replace(/\s+/g, '_').toUpperCase();

    if (btn) { btn.disabled = true; btn.style.opacity = '0.6'; }
    if (statusEl) statusEl.textContent = '⏳ Menyiapkan data...';

    try {
        if (tipe === 'summary') {
            if (window.granularSummaryView === 'desa') {
                const arr = window.lastDesaSummaryArr;
                if (!arr || arr.length === 0) {
                    if (statusEl) statusEl.textContent = '⚠️ Belum ada data rekap desa yang tampil. Pilih kabupaten terlebih dahulu.';
                    if (btn) { btn.disabled = false; btn.style.opacity = '1'; }
                    return;
                }
                const rows = arr.map((d, i) => ({
                    'No': i + 1,
                    'Kecamatan': d.kec || '-',
                    'Desa / Kelurahan': d.desa || '-',
                    'Total Target': d.total,
                    'Belum Selesai': d.belum,
                    'Selesai': d.selesai,
                    '% Capaian': d.total > 0 ? ((d.selesai / d.total) * 100).toFixed(1) + '%' : '0.0%'
                }));
                exportToCSV(rows, `Rekap_Desa_${surveyLabel}_${kabLabel}_${today}.csv`);
                if (statusEl) statusEl.textContent = `✅ ${rows.length} baris rekap desa berhasil diunduh!`;
            } else {
                // Export directly from the table already rendered on screen
                const arr = window.lastPetugasSummaryArr;
                if (!arr || arr.length === 0) {
                    if (statusEl) statusEl.textContent = '⚠️ Belum ada data tabel rekap yang tampil. Pilih kabupaten terlebih dahulu di halaman Detail.';
                    if (btn) { btn.disabled = false; btn.style.opacity = '1'; }
                    return;
                }
                const rows = arr.map((p, i) => ({
                    'No': i + 1,
                    'Nama Petugas': p.name || '-',
                    'Email / Username': p.email || '-',
                    'Total Target': p.total,
                    'Belum Selesai': p.belum,
                    'Selesai': p.selesai,
                    '% Capaian': p.total > 0 ? ((p.selesai / p.total) * 100).toFixed(1) + '%' : '0.0%'
                }));
                exportToCSV(rows, `Rekap_Petugas_${surveyLabel}_${kabLabel}_${today}.csv`);
                if (statusEl) statusEl.textContent = `✅ ${rows.length} baris berhasil diunduh!`;
            }
        } else {
            const selectedKabs = [...document.querySelectorAll('.excel-kab-check:checked')].map(c => c.value);
            if (selectedKabs.length === 0) {
                if (statusEl) statusEl.textContent = '⚠️ Pilih minimal satu kabupaten/kota.';
                return;
            }
            const kabsLabel = selectedKabs.length === 1
                ? selectedKabs[0].replace(/^\[\d+\]\s*/, '').trim().replace(/\s+/g, '_').toUpperCase()
                : `${selectedKabs.length}_Kab`;
            await downloadRawExcel(selectedKabs, surveyType, statusEl, `Raw_${surveyLabel}_${kabsLabel}_${today}.csv`);
        }
    } catch (e) {
        console.error('Download error:', e);
        if (statusEl) statusEl.textContent = '❌ Gagal: ' + e.message;
    } finally {
        if (btn) { btn.disabled = false; btn.style.opacity = '1'; }
    }
};

async function downloadSummaryExcel(selectedKabs, surveyType, statusEl) {
    if (!window.supabaseClient) {
        if (statusEl) statusEl.textContent = '❌ Koneksi Supabase tidak tersedia.';
        return;
    }

    const fetchGranularDataForKab = async (kabCode, sType, kabCleanName) => {
        const dbKey = `granular_assignments_${sType}_${kabCode}`;
        
        const parsePayload = async (payload, keyForChunks) => {
            if (typeof payload === 'string') {
                try { payload = JSON.parse(payload); } catch(e) { return []; }
            }
            let compressedData = '';
            if (payload && payload.is_chunked) {
                const totalChunks = payload.total_chunks;
                const chunkKeys = [];
                for (let i = 0; i < totalChunks; i++) {
                    chunkKeys.push(`${keyForChunks}__chunk_${i}`);
                }
                const chunkResults = await Promise.all(
                    chunkKeys.map(async (chunkKey) => {
                        const { data, error: chunkErr } = await window.supabaseClient
                            .from('dashboard_store')
                            .select('value')
                            .eq('key', chunkKey)
                            .single();
                        if (chunkErr || !data || !data.value) return '';
                        let cp = data.value;
                        if (typeof cp === 'string') {
                            try { cp = JSON.parse(cp); } catch(e) { return ''; }
                        }
                        return cp.compressed_data || '';
                    })
                );
                compressedData = chunkResults.join('');
            } else if (payload && payload.compressed_data) {
                compressedData = payload.compressed_data;
            }
            if (!compressedData) return [];
            try {
                return window.decompressAndParseGranular ? window.decompressAndParseGranular(compressedData) : [];
            } catch(decompErr) {
                console.error('decompressAndParseGranular error:', decompErr);
                return [];
            }
        };
        
        const { data: dbData, error } = await window.supabaseClient
            .from('dashboard_store')
            .select('value')
            .eq('key', dbKey)
            .single();
        
        if (!error && dbData && dbData.value) {
            return await parsePayload(dbData.value, dbKey);
        }
        
        // Fallback: try combined key (e.g. granular_assignments_se_ub) and filter by kab
        const fallbackKey = `granular_assignments_${sType}`;
        const { data: fbData, error: fbError } = await window.supabaseClient
            .from('dashboard_store')
            .select('value')
            .eq('key', fallbackKey)
            .single();
        if (!fbError && fbData && fbData.value) {
            const allRecords = await parsePayload(fbData.value, fallbackKey);
            if (allRecords && allRecords.length > 0 && kabCleanName) {
                const filtered = allRecords.filter(r => {
                    const rKab = (r.kab_name || '').replace(/^\[\d+\]\s*/, '').trim().toUpperCase();
                    return rKab === kabCleanName.toUpperCase();
                });
                return filtered.length > 0 ? filtered : allRecords;
            }
            return allRecords;
        }
        return [];
    };

    const cleanKabs = selectedKabs.map(k => k.replace(/^\[\d+\]\s*/, '').trim().toUpperCase());
    let allGranularRecords = [];

    // Load data from memory or fetch from Supabase
    for (const kab of selectedKabs) {
        const match = kab.match(/\[(\d+)\]/);
        if (!match) continue;
        const fullCode = `72${match[1]}`;
        const kabClean = kab.replace(/^\[\d+\]\s*/, '').trim().toUpperCase();

        if (statusEl) statusEl.textContent = `⏳ Memuat data ${kab}...`;

        // Check if currently loaded in memory — filter by BOTH kab AND survey_type
        let isMatchMemory = false;
        if (window.GRANULAR_ASSIGNMENTS_DATA && window.GRANULAR_ASSIGNMENTS_DATA.length > 0) {
            const memFiltered = window.GRANULAR_ASSIGNMENTS_DATA.filter(r => {
                const rKab = (r.kab_name || '').replace(/^\[\d+\]\s*/, '').trim().toUpperCase();
                return rKab === kabClean && r.survey_type === surveyType;
            });
            if (memFiltered.length > 0) {
                isMatchMemory = true;
                allGranularRecords.push(...memFiltered);
            }
        }

        if (!isMatchMemory) {
            try {
                // Fetch then filter by survey_type
                const records = await fetchGranularDataForKab(fullCode, surveyType, kabClean);
                const filtered = records.filter(r => !r.survey_type || r.survey_type === surveyType);
                allGranularRecords.push(...filtered);
            } catch (e) {
                console.warn(`Gagal memuat data granular untuk ${kab}:`, e);
            }
        }
    }

    if (allGranularRecords.length === 0) {
        if (statusEl) statusEl.textContent = '⚠️ Tidak ada data untuk diekspor.';
        return;
    }

    if (statusEl) statusEl.textContent = '⏳ Menyusun rekapitulasi petugas...';

    const petMap = {};
    allGranularRecords.forEach(r => {
        // Use username as unique key (matches dashboard logic), display fullname
        const username = r.petugas_username && r.petugas_username !== '-' ? r.petugas_username : null;
        let displayName = r.petugas_fullname && r.petugas_fullname !== '-' ? r.petugas_fullname : (username || null);
        
        // Apply userMap to convert username to real name (same as dashboard table)
        if (username && window.userMap) {
            const mapped = window.userMap[username] || window.userMap[username.split('@')[0]];
            if (mapped) displayName = mapped;
        }
        
        if (!displayName || !displayName.trim()) {
            const isCompleted = r.status !== 'OPEN' && r.status !== 'DRAFT';
            displayName = isCompleted ? 'CAWI / Mandiri (Tanpa Petugas)' : 'Belum Ada Petugas';
        }
        
        const pengawas = r.pengawas_fullname && r.pengawas_fullname !== '-' ? r.pengawas_fullname : (r.pengawas_username || '-');
        const email = username || '-';
        const kab = r.kab_name || '-';
        // Key by kab + username to match dashboard grouping
        const key = `${kab}|||${username || displayName}`;
        
        if (!petMap[key]) {
            petMap[key] = { kab, name: displayName, pengawas, email, total: 0, selesai: 0, belum: 0, open: 0, draft: 0, submitted: 0, rejected: 0, approved: 0 };
        }
        // Update display name (in case earlier record had only username)
        if (displayName && displayName !== 'Belum Ada Petugas' && displayName !== 'CAWI / Mandiri (Tanpa Petugas)') {
            petMap[key].name = displayName;
        }
        petMap[key].total++;
        const st = (r.status || '').toUpperCase();
        if (st === 'OPEN') petMap[key].open++;
        else if (st === 'DRAFT') petMap[key].draft++;
        else if (st === 'SUBMITTED') petMap[key].submitted++;
        else if (st === 'REJECTED') petMap[key].rejected++;
        else if (st === 'APPROVED') petMap[key].approved++;

        if (st !== 'OPEN' && st !== 'DRAFT') petMap[key].selesai++;
        else petMap[key].belum++;
    });

    const rows = Object.values(petMap).map(p => ({
        'Kabupaten/Kota': p.kab,
        'Nama Petugas': p.name,
        'Pengawas/Pencacah': p.pengawas,
        'Email/Username': p.email,
        'Total Target': p.total,
        'Belum Selesai': p.belum,
        'Selesai': p.selesai,
        '% Capaian': p.total > 0 ? ((p.selesai / p.total) * 100).toFixed(1) + '%' : '0.0%',
        'OPEN': p.open,
        'DRAFT': p.draft,
        'SUBMITTED': p.submitted,
        'REJECTED': p.rejected,
        'APPROVED': p.approved
    }));

    exportToCSV(rows, `rekap_petugas_${surveyType}_${new Date().toISOString().slice(0,10)}.csv`);
    if (statusEl) statusEl.textContent = `✅ ${rows.length} baris berhasil diunduh!`;
}

async function downloadRawExcel(selectedKabs, surveyType, statusEl, filename) {
    if (!window.supabaseClient) {
        if (statusEl) statusEl.textContent = '❌ Koneksi Supabase tidak tersedia.';
        return;
    }

    const allRows = [];

    for (const kab of selectedKabs) {
        const match = kab.match(/\[(\d+)\]/);
        if (!match) continue;
        const fullCode = `72${match[1]}`;
        const dbKey = `granular_assignments_${surveyType}_${fullCode}`;

        if (statusEl) statusEl.textContent = `⏳ Memuat ${kab}...`;

        try {
            const { data: dbData, error } = await window.supabaseClient
                .from('dashboard_store')
                .select('value')
                .eq('key', dbKey)
                .single();

            if (error || !dbData) {
                console.warn(`Gagal muat ${dbKey}:`, error);
                continue;
            }

            let payload = dbData.value;
            if (typeof payload === 'string') payload = JSON.parse(payload);

            let records = [];
            if (payload && payload.is_chunked) {
                const totalChunks = payload.total_chunks;
                const chunkKeys = [];
                for (let i = 0; i < totalChunks; i++) {
                    chunkKeys.push(`${dbKey}__chunk_${i}`);
                }
                const chunkResults = await Promise.all(
                    chunkKeys.map(async (chunkKey) => {
                        const { data, error } = await window.supabaseClient
                            .from('dashboard_store')
                            .select('value')
                            .eq('key', chunkKey)
                            .single();
                        if (error || !data) return '';
                        let chunkPayload = data.value;
                        if (typeof chunkPayload === 'string') chunkPayload = JSON.parse(chunkPayload);
                        return chunkPayload.compressed_data || '';
                    })
                );
                const assembled = chunkResults.join('');
                records = window.decompressAndParseGranular ? window.decompressAndParseGranular(assembled) : [];
            } else if (payload && payload.compressed_data) {
                records = window.decompressAndParseGranular ? window.decompressAndParseGranular(payload.compressed_data) : [];
            } else if (Array.isArray(payload)) {
                records = payload;
            }

            records.forEach(r => {
                allRows.push({
                    'Kabupaten/Kota': r.kab_name || kab,
                    'Kecamatan': r.kec_name || '-',
                    'Desa/Kelurahan': r.desa_name || '-',
                    'SLS': r.sls_name || '-',
                    'Kode Target': r.codeIdentity || '-',
                    'Nama Target': r.data1 || '-',
                    'Status': r.status || '-',
                    'Nama Petugas': r.petugas_fullname || r.petugas_username || '-',
                    'Email Petugas': r.petugas_username || '-',
                    'Nama Pengawas': r.pengawas_fullname || r.pengawas_username || '-',
                    'Email Pengawas': r.pengawas_username || '-',
                    'Tanggal Modifikasi': r.dateModified || '-'
                });
            });
        } catch (e) {
            console.error('Error loading raw data for', kab, e);
        }
    }

    if (allRows.length === 0) {
        if (statusEl) statusEl.textContent = '⚠️ Tidak ada data untuk diekspor. Pastikan data granular sudah dimuat.';
        return;
    }

    const outFilename = filename || `Raw_Target_${surveyType === 'se_umum' ? 'SE_Umum' : 'SE_UB'}_${new Date().toISOString().slice(0,10)}.csv`;
    exportToCSV(allRows, outFilename);
    if (statusEl) statusEl.textContent = `✅ ${allRows.length} baris berhasil diunduh!`;
}

// ================== TREN PROGRES CHART ==================

window._trenChartInstance = null;

window.initTrenFilters = function () {
    const data = window.DAILY_SUBMISSION_STATS;
    if (!Array.isArray(data) || data.length === 0) return;
    const kabSet = new Set();
    data.forEach(d => { if (d.kab_name) kabSet.add(d.kab_name); });
    const kabFilter = document.getElementById('tren-kab-filter');
    if (kabFilter && kabFilter.options.length <= 1) {
        Array.from(kabSet).sort().forEach(kab => {
            const opt = document.createElement('option');
            opt.value = kab;
            opt.textContent = kab.replace(/^\[\d+\]\s*/, '');
            kabFilter.appendChild(opt);
        });
    }
};

window.renderTrenChart = function () {
    const data = window.DAILY_SUBMISSION_STATS;
    if (!Array.isArray(data) || data.length === 0) {
        const tbody = document.getElementById('tren-kab-table-body');
        if (tbody) tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;padding:2rem;color:var(--text-secondary);">Data harian belum tersedia. Jalankan scraper untuk mengisi data.</td></tr>';
        return;
    }

    const kabVal = document.getElementById('tren-kab-filter')?.value || 'all';
    const surveyVal = document.getElementById('tren-survey-filter')?.value || 'all';
    const modeVal = document.getElementById('tren-mode-filter')?.value || 'daily';
    const rangeVal = parseInt(document.getElementById('tren-range-filter')?.value) || 0;

    // Filter data
    let filtered = data.filter(d => {
        if (kabVal !== 'all' && d.kab_name !== kabVal) return false;
        if (surveyVal !== 'all' && d.survey_type !== surveyVal) return false;
        return true;
    });

    // Classify status
    const classify = (status) => {
        const s = (status || '').toUpperCase();
        if (s.includes('SUBMITTED')) return 'submitted';
        if (s.includes('APPROVED')) return 'approved';
        if (s.includes('REJECTED') || s.includes('REVOKED')) return 'rejected';
        return 'other';
    };

    // Aggregate by date
    const dateMap = {};
    filtered.forEach(d => {
        if (!dateMap[d.date]) dateMap[d.date] = { submitted: 0, approved: 0, rejected: 0 };
        const cls = classify(d.status);
        if (cls !== 'other') dateMap[d.date][cls] += (d.count || 0);
    });

    const dates = Object.keys(dateMap).sort();
    if (dates.length === 0) return;

    // 1. Overall Arrays for summary cards & breakdown table
    const overallSubmittedArr = dates.map(d => dateMap[d]?.submitted || 0);
    const overallApprovedArr = dates.map(d => dateMap[d]?.approved || 0);
    const overallRejectedArr = dates.map(d => dateMap[d]?.rejected || 0);

    // Summary cards (Overall)
    const totalSub = overallSubmittedArr.reduce((a, b) => a + b, 0);
    const totalAppr = overallApprovedArr.reduce((a, b) => a + b, 0);
    const totalRej = overallRejectedArr.reduce((a, b) => a + b, 0);
    const combined = dates.map((d, i) => overallSubmittedArr[i] + overallApprovedArr[i] + overallRejectedArr[i]);
    const peakVal = Math.max(...combined, 0);
    const peakIdx = combined.indexOf(peakVal);

    const el = id => document.getElementById(id);
    if (el('tren-stat-submitted')) el('tren-stat-submitted').textContent = totalSub.toLocaleString('id-ID');
    if (el('tren-stat-approved')) el('tren-stat-approved').textContent = totalAppr.toLocaleString('id-ID');
    if (el('tren-stat-rejected')) el('tren-stat-rejected').textContent = totalRej.toLocaleString('id-ID');
    if (el('tren-stat-peak')) el('tren-stat-peak').textContent = peakVal.toLocaleString('id-ID');
    if (el('tren-stat-peak-date')) el('tren-stat-peak-date').textContent = peakIdx >= 0 ? dates[peakIdx] : '-';
    if (el('tren-chart-subtitle')) el('tren-chart-subtitle').textContent = modeVal === 'cumulative'
        ? 'Jumlah kumulatif assignment per status'
        : 'Jumlah assignment yang dikirim per hari';

    // 2. Prepare sliced data specifically for Chart.js
    let chartLabels = [...dates];
    let sub = [];
    let appr = [];
    let rej = [];

    const toCumulative = (arr) => arr.reduce((acc, v, i) => { acc.push((acc[i-1] || 0) + v); return acc; }, []);

    if (modeVal === 'cumulative') {
        const cumSub = toCumulative(overallSubmittedArr);
        const cumAppr = toCumulative(overallApprovedArr);
        const cumRej = toCumulative(overallRejectedArr);

        if (rangeVal > 0) {
            chartLabels = dates.slice(-rangeVal);
            sub = cumSub.slice(-rangeVal);
            appr = cumAppr.slice(-rangeVal);
            rej = cumRej.slice(-rangeVal);
        } else {
            sub = cumSub;
            appr = cumAppr;
            rej = cumRej;
        }
    } else {
        if (rangeVal > 0) {
            chartLabels = dates.slice(-rangeVal);
            sub = overallSubmittedArr.slice(-rangeVal);
            appr = overallApprovedArr.slice(-rangeVal);
            rej = overallRejectedArr.slice(-rangeVal);
        } else {
            sub = overallSubmittedArr;
            appr = overallApprovedArr;
            rej = overallRejectedArr;
        }
    }

    // Render Chart.js
    const canvas = document.getElementById('tren-chart-canvas');
    if (!canvas) return;
    if (window._trenChartInstance) {
        window._trenChartInstance.destroy();
        window._trenChartInstance = null;
    }
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const gridColor = isDark ? 'rgba(255,255,255,0.07)' : 'rgba(0,0,0,0.06)';
    const textColor = isDark ? '#94a3b8' : '#64748b';

    window._trenChartInstance = new Chart(canvas.getContext('2d'), {
        type: 'line',
        data: {
            labels: chartLabels,
            datasets: [
                {
                    label: 'Submitted',
                    data: sub,
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59,130,246,0.08)',
                    borderWidth: 2.5,
                    pointRadius: chartLabels.length > 30 ? 1 : 3,
                    pointHoverRadius: 5,
                    tension: 0.35,
                    fill: modeVal === 'daily',
                },
                {
                    label: 'Approved',
                    data: appr,
                    borderColor: '#22c55e',
                    backgroundColor: 'rgba(34,197,94,0.08)',
                    borderWidth: 2.5,
                    pointRadius: chartLabels.length > 30 ? 1 : 3,
                    pointHoverRadius: 5,
                    tension: 0.35,
                    fill: false,
                },
                {
                    label: 'Rejected',
                    data: rej,
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239,68,68,0.08)',
                    borderWidth: 2,
                    pointRadius: chartLabels.length > 30 ? 1 : 3,
                    pointHoverRadius: 5,
                    tension: 0.35,
                    fill: false,
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: {
                    position: 'top',
                    labels: { color: textColor, font: { family: 'Outfit', size: 12, weight: '600' }, padding: 16, usePointStyle: true }
                },
                tooltip: {
                    backgroundColor: isDark ? '#1e293b' : '#ffffff',
                    titleColor: isDark ? '#f1f5f9' : '#0f172a',
                    bodyColor: textColor,
                    borderColor: isDark ? '#334155' : '#e2e8f0',
                    borderWidth: 1,
                    padding: 12,
                    callbacks: {
                        label: ctx => ` ${ctx.dataset.label}: ${ctx.parsed.y.toLocaleString('id-ID')}`
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: gridColor },
                    ticks: { color: textColor, font: { family: 'Outfit', size: 11 }, maxTicksLimit: 12, maxRotation: 45 }
                },
                y: {
                    beginAtZero: true,
                    grid: { color: gridColor },
                    ticks: { color: textColor, font: { family: 'Outfit', size: 11 }, callback: v => v.toLocaleString('id-ID') }
                }
            }
        }
    });

    // Per-kab breakdown table (Overall - not affected by rentang filter)
    const kabMap = {};
    filtered.forEach(d => {
        const kab = d.kab_name || 'Tidak Diketahui';
        if (!kabMap[kab]) kabMap[kab] = { submitted: 0, approved: 0, rejected: 0 };
        const cls = classify(d.status);
        if (cls !== 'other') kabMap[kab][cls] += (d.count || 0);
    });
    const tbody = document.getElementById('tren-kab-table-body');
    if (tbody) {
        const kabArr = Object.entries(kabMap).sort((a,b) => (b[1].submitted+b[1].approved+b[1].rejected) - (a[1].submitted+a[1].approved+a[1].rejected));
        tbody.innerHTML = kabArr.map(([kab, v]) => {
            const total = v.submitted + v.approved + v.rejected;
            return `<tr style="border-bottom:1px solid var(--card-border);">
                <td style="padding:0.6rem 0.75rem;font-weight:600;color:var(--text);">${kab.replace(/^\[\d+\]\s*/, '')}</td>
                <td style="text-align:right;padding:0.6rem 0.75rem;color:#3b82f6;font-weight:600;">${v.submitted.toLocaleString('id-ID')}</td>
                <td style="text-align:right;padding:0.6rem 0.75rem;color:#22c55e;font-weight:600;">${v.approved.toLocaleString('id-ID')}</td>
                <td style="text-align:right;padding:0.6rem 0.75rem;color:#ef4444;font-weight:600;">${v.rejected.toLocaleString('id-ID')}</td>
                <td style="text-align:right;padding:0.6rem 0.75rem;color:var(--text);font-weight:700;">${total.toLocaleString('id-ID')}</td>
            </tr>`;
        }).join('');
    }
};

// Hook into updateTimelineView to also render tren chart
const _origUpdateTimeline = window.updateTimelineView;
window.updateTimelineView = function (...args) {
    if (_origUpdateTimeline) _origUpdateTimeline.apply(this, args);

    const doRender = () => {
        window.initTrenFilters();
        window.renderTrenChart();
    };

    const data = window.DAILY_SUBMISSION_STATS;
    if (!Array.isArray(data) || data.length === 0) {
        // Try loading from local JS file as fallback
        const existing = document.querySelector('script[src*="daily_submission_stats.js"]');
        const src = (typeof getScriptUrl === 'function' ? getScriptUrl('daily_submission_stats.js') : 'daily_submission_stats.js')
            + '?t=' + Date.now();
        // Remove old if exists to force reload
        if (existing) existing.remove();
        const script = document.createElement('script');
        script.src = src;
        script.onload = () => {
            // After loading, DAILY_SUBMISSION_STATS should be set by the JS file
            if (!Array.isArray(window.DAILY_SUBMISSION_STATS)) window.DAILY_SUBMISSION_STATS = [];
            doRender();
        };
        script.onerror = () => doRender();
        document.head.appendChild(script);
    } else {
        doRender();
    }
};

// ================== END TREN PROGRES CHART ==================

function exportToCSV(rows, filename) {
    if (!rows || rows.length === 0) return;
    const headers = Object.keys(rows[0]);
    const csvLines = [
        'sep=,',
        headers.join(','),
        ...rows.map(row => headers.map(h => {
            let val = row[h] == null ? '' : String(row[h]);
            if (val.includes(',') || val.includes('"') || val.includes('\n')) {
                val = '"' + val.replace(/"/g, '""') + '"';
            }
            return val;
        }).join(','))
    ];
    const bom = '\uFEFF';
    const csvText = bom + csvLines.join('\n');

    if (window.location.protocol === 'file:') {
        // Fallback for file:// protocol: Chrome blocks custom filenames via Blob URL download attribute
        const encodedUri = 'data:text/csv;charset=utf-8,' + encodeURIComponent(csvText);
        const a = document.createElement('a');
        a.href = encodedUri;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    } else {
        const blob = new Blob([csvText], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
}

window.downloadCurrentSeTable = function(surveyType) {
    const viewLevel = document.getElementById(`${surveyType}-view-level`)?.value || 'kabupaten';
    const searchVal = (document.getElementById(`${surveyType}-search-input`)?.value || '').toLowerCase().trim();
    const ipasDataObj = window.IPAS_DATA || { se_umum: [], se_ub: [] };
    const surveyData = ipasDataObj[surveyType] || [];
    const dateToday = new Date().toISOString().slice(0, 10);
    const labelUpper = surveyType.toUpperCase();

    let exportRows = [];
    let outFilename = `Rekap_${labelUpper}_${viewLevel}_${dateToday}.csv`;

    if (viewLevel === 'kabupaten') {
        const capaianFilterVal = document.getElementById(`${surveyType}-capaian-filter`)?.value || 'all';
        const selectedKab = document.getElementById(`${surveyType}-kab-filter`)?.value || 'all';

        let filtered = surveyData.filter(item => {
            if (selectedKab !== 'all' && item.kabupaten !== selectedKab) return false;

            const kabMatch = item.kabupaten.toLowerCase().includes(searchVal);
            const matchingKecs = (item.kecamatan_list || []).filter(kec =>
                kec.kec_name.toLowerCase().includes(searchVal)
            );
            return kabMatch || matchingKecs.length > 0;
        });

        if (capaianFilterVal !== 'all') {
            filtered = filtered.filter(item => {
                const pct = parseFloat(item.persentase) || 0;
                if (capaianFilterVal === 'high') return pct >= 80;
                if (capaianFilterVal === 'med') return pct >= 50 && pct < 80;
                if (capaianFilterVal === 'low') return pct < 50;
                return true;
            });
        }

        let totalPrelist = 0, totalDraft = 0, totalOpen = 0, totalSubmitted = 0;

        exportRows = filtered.map(item => {
            const prelist = item.total_prelist || 0;
            const draft = item.total_draft || 0;
            const open = item.total_open || 0;
            const submitted = item.total_submitted || 0;
            const sisaUsaha = Math.max(0, prelist - submitted);
            const pctCapaian = `${item.persentase || 0}%`;
            const delta = item.delta_persen !== undefined && item.delta_persen !== null
                ? `+${parseFloat(item.delta_persen).toFixed(2)}%`
                : '';

            totalPrelist += prelist;
            totalDraft += draft;
            totalOpen += open;
            totalSubmitted += submitted;

            return {
                'Kabupaten/Kota': item.kabupaten,
                'Total Target': prelist,
                'Draft': draft,
                'Open': open,
                'Submitted (Selesai)': submitted,
                '% Capaian': pctCapaian,
                'Sisa Usaha': sisaUsaha,
                'Delta (%)': delta
            };
        });

        // Calculate province delta using weighted average (same logic as dashboard)
        let sumSelesaiYesterday = 0, sumTargetYesterday = 0;
        filtered.forEach(item => {
            const pctNow = parseFloat(item.persentase) || 0;
            const itemDelta = parseFloat(item.delta_persen) || 0;
            const pctYesterday = pctNow - itemDelta;
            sumSelesaiYesterday += (pctYesterday / 100) * (item.total_prelist || 0);
            sumTargetYesterday += (item.total_prelist || 0);
        });
        const provPctNow = totalPrelist > 0 ? (totalSubmitted / totalPrelist) * 100 : 0;
        const provPctYesterday = sumTargetYesterday > 0 ? (sumSelesaiYesterday / sumTargetYesterday) * 100 : 0;
        let provDelta = provPctNow - provPctYesterday;
        if (Math.abs(provDelta) < 0.01) provDelta = 0;
        const provDeltaStr = provDelta !== 0 ? (provDelta >= 0 ? '+' : '') + provDelta.toFixed(2) + '%' : '';

        // Add cumulative SULAWESI TENGAH total row
        const totalSisaUsaha = Math.max(0, totalPrelist - totalSubmitted);
        const totalPct = totalPrelist > 0 ? ((totalSubmitted / totalPrelist) * 100).toFixed(2) + '%' : '0.00%';
        exportRows.push({
            'Kabupaten/Kota': 'SULAWESI TENGAH',
            'Total Target': totalPrelist,
            'Draft': totalDraft,
            'Open': totalOpen,
            'Submitted (Selesai)': totalSubmitted,
            '% Capaian': totalPct,
            'Sisa Usaha': totalSisaUsaha,
            'Delta (%)': provDeltaStr
        });
    } else if (viewLevel === 'kecamatan') {
        const selectedKab = document.getElementById(`${surveyType}-kab-filter`)?.value || 'all';
        const isFiltered = selectedKab !== 'all';
        const capaianFilterVal = document.getElementById(`${surveyType}-capaian-filter`)?.value || 'all';

        const allKecs = [];
        surveyData.forEach(kab => {
            if (isFiltered && kab.kabupaten !== selectedKab) return;
            (kab.kecamatan_list || []).forEach(kec => {
                if (!kec.kec_name || kec.kec_name === '-') return;
                if (searchVal && !kec.kec_name.toLowerCase().includes(searchVal) && !kab.kabupaten.toLowerCase().includes(searchVal)) return;

                const pct = parseFloat(kec.persentase) || 0;
                if (capaianFilterVal === 'high' && pct < 80) return;
                if (capaianFilterVal === 'med' && (pct < 50 || pct >= 80)) return;
                if (capaianFilterVal === 'low' && pct >= 50) return;

                allKecs.push({ ...kec, kab_name: kab.kabupaten });
            });
        });

        allKecs.sort((a, b) => {
            const pctA = parseFloat(a.persentase) || 0;
            const pctB = parseFloat(b.persentase) || 0;
            if (pctA !== pctB) return pctB - pctA;
            return (b.total_prelist || 0) - (a.total_prelist || 0);
        });

        if (isFiltered) {
            const kabLabel = selectedKab.replace(/\[\d+\]\s*/, '').trim().replace(/\s+/g, '_');
            outFilename = `Ranking_Kecamatan_${labelUpper}_${kabLabel}_${dateToday}.csv`;
        } else {
            outFilename = `Ranking_Kecamatan_Semua_Kab_${labelUpper}_${dateToday}.csv`;
        }

        exportRows = allKecs.map((kec, idx) => {
            const rowData = {
                'Rank': idx + 1,
                'Kecamatan': kec.kec_name,
                'Total Target': kec.total_prelist,
                'Draft': kec.total_draft,
                'Open': kec.total_open,
                'Submitted (Total)': kec.total_submitted,
                'Submitted Pencacah': kec.total_submitted_pencacah,
                'Submitted Respondent': kec.total_submitted_respondent,
                'Approved': kec.total_approved,
                'Rejected': kec.total_rejected,
                '% Capaian': `${kec.persentase}%`
            };
            if (!isFiltered) {
                // Add Kabupaten column at start of object
                return Object.assign({ 'Kabupaten/Kota': kec.kab_name.replace(/\[\d+\] /, '') }, rowData);
            }
            return rowData;
        });
    }

    if (exportRows.length === 0) {
        alert('Tidak ada data yang bisa diexport dengan filter aktif.');
        return;
    }

    exportToCSV(exportRows, outFilename);
};