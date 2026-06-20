document.addEventListener('DOMContentLoaded', () => {
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

    // Initialize Supabase Client if credentials are provided
    let supabaseClient = null;
    if (typeof supabase !== 'undefined' && window.SUPABASE_URL && window.SUPABASE_KEY && window.SUPABASE_URL !== 'URL_PLACEHOLDER') {
        try {
            supabaseClient = supabase.createClient(window.SUPABASE_URL, window.SUPABASE_KEY);
            console.log("Supabase Client initialized successfully.");
        } catch (e) {
            console.error("Failed to initialize Supabase client:", e);
        }
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

                    return `
                        <tr>
                            <td>${highlightText(comp.code, searchQuery)}</td>
                            <td style="font-weight: 700;">${highlightText(comp.company_name, searchQuery)}</td>
                            <td>${highlightText(comp.email, searchQuery)}</td>
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
                <th colspan="4" style="font-family: 'Outfit', sans-serif; text-align: center; color: var(--color-delivered); border-bottom: 1px solid var(--card-border);">
                    Submitted (Selesai)
                </th>
                <th rowspan="2" class="sortable" onclick="sortSeTable('${surveyType}', 'persentase')" style="font-family: 'Outfit', sans-serif; text-align: center; vertical-align: middle;">
                    % Capaian${getIcon('persentase')}
                </th>
                <th rowspan="2" class="sortable" onclick="sortSeTable('${surveyType}', 'new_usaha_overall')" style="font-family: 'Outfit', sans-serif; text-align: center; vertical-align: middle;">
                    Tambahan (Non-Target)${getIcon('new_usaha_overall')}
                </th>
            </tr>
            <tr>
                <th class="sortable" onclick="sortSeTable('${surveyType}', 'total_submitted')" style="font-family: 'Outfit', sans-serif; text-align: right; color: var(--color-delivered); font-size: 0.8rem; padding: 0.4rem 0.75rem;">
                    Total${getIcon('total_submitted')}
                </th>
                <th class="sortable" onclick="sortSeTable('${surveyType}', 'today_completed')" style="font-family: 'Outfit', sans-serif; text-align: right; color: var(--color-opened); font-size: 0.8rem; padding: 0.4rem 0.75rem;">
                    Hari Ini${getIcon('today_completed')}
                </th>
                <th class="sortable" onclick="sortSeTable('${surveyType}', 'yesterday_completed')" style="font-family: 'Outfit', sans-serif; text-align: right; color: #f59e0b; font-size: 0.8rem; padding: 0.4rem 0.75rem;">
                    Kemarin${getIcon('yesterday_completed')}
                </th>
                <th class="sortable" onclick="sortSeTable('${surveyType}', 'two_days_ago_completed')" style="font-family: 'Outfit', sans-serif; text-align: right; color: var(--color-clicked); font-size: 0.8rem; padding: 0.4rem 0.75rem;">
                    H-2${getIcon('two_days_ago_completed')}
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
        if (key.includes('REJECTED')) return statusStyles['REJECTED'];
        if (key.includes('APPROVED')) return statusStyles['APPROVED'];
        if (key.includes('SUBMITTED')) return statusStyles['SUBMITTED'];
        return 'background: rgba(156, 163, 175, 0.1); color: #4b5563; border: 1px solid rgba(156, 163, 175, 0.2);';
    }

    // Sensus Ekonomi Dashboard Render Engine (Umum or UB)
    window.renderSeDashboard = function (surveyType) {
        const ipasDataObj = window.IPAS_DATA || { se_umum: [], se_ub: [] };
        const surveyData = ipasDataObj[surveyType] || [];

        // Calculate Summary
        let prelist = 0, draft = 0, openVal = 0, submitted = 0, rejected = 0, today = 0, yesterday = 0, twoDaysAgo = 0, newToday = 0, newRumahToday = 0;

        let todayBreakdown = {};
        let yesterdayBreakdown = {};
        let twoDaysAgoBreakdown = {};

        surveyData.forEach(item => {
            prelist += item.total_prelist || 0;
            draft += item.total_draft || 0;
            openVal += item.total_open || 0;
            submitted += item.total_submitted || 0;
            rejected += item.total_rejected || 0;
            today += item.today_completed || 0;
            yesterday += item.yesterday_completed || 0;
            twoDaysAgo += item.two_days_ago_completed || 0;
            newToday += item.new_usaha_today || 0;
            newRumahToday += item.new_rumah_today || 0;
            item.sisa_usaha = Math.max(0, (item.total_prelist || 0) - (item.total_submitted || 0));

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

        const persentase = floorPct(submitted, prelist);
        const sisa = prelist - submitted;

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
        const prelistEl = document.getElementById(`${surveyType}-stat-total-prelist`);
        if(prelistEl) prelistEl.textContent = formatNum(prelist);
        
        const newTodayEl = document.getElementById(`${surveyType}-stat-new-today`);
        if(newTodayEl) newTodayEl.textContent = `+${formatNum(newToday)}`;
        
        const newRumahTodayEl = document.getElementById(`${surveyType}-stat-new-rumah-today`);
        if(newRumahTodayEl) newRumahTodayEl.textContent = `+${formatNum(newRumahToday)}`;
        
        const draftEl = document.getElementById(`${surveyType}-stat-draft`);
        if(draftEl) draftEl.textContent = formatNum(draft);
        
        const openEl = document.getElementById(`${surveyType}-stat-open`);
        if(openEl) openEl.textContent = formatNum(openVal);
        
        const submittedEl = document.getElementById(`${surveyType}-stat-submitted`);
        if(submittedEl) submittedEl.textContent = formatNum(submitted);
        
        const percentEl = document.getElementById(`${surveyType}-stat-percentage`);
        if(percentEl) percentEl.textContent = `(${persentase}%)`;

        const rejectedEl = document.getElementById(`${surveyType}-stat-rejected`);
        if(rejectedEl) rejectedEl.textContent = formatNum(rejected);

        // Build rejected breakdown by aggregating status breakdowns across all days/all data
        const allRejectedBreakdown = {};
        surveyData.forEach(item => {
            // Collect from all breakdown objects to reconstruct rejected-type statuses
            [item.today_completed_breakdown, item.yesterday_completed_breakdown, item.two_days_ago_completed_breakdown].forEach(bd => {
                if (!bd) return;
                Object.entries(bd).forEach(([st, val]) => {
                    if (st.toUpperCase().includes('REJECTED')) {
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
                    .map(([status, val]) => `
                        <div class="popover-item">
                            <span class="popover-badge" style="background: rgba(239,68,68,0.15); color: #ef4444; border-color: rgba(239,68,68,0.3);">${status.replace('REJECTED BY ', 'Oleh ')}</span>
                            <span class="popover-count">${formatNum(val)}</span>
                        </div>
                    `).join('');
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

        const todayEl = document.getElementById(`${surveyType}-stat-today`);
        if(todayEl) todayEl.innerHTML = getDailyProgressCellHTML(today, todayBreakdown, 'SUBMIT HARI INI');

        const yesterdayEl = document.getElementById(`${surveyType}-stat-yesterday`);
        if(yesterdayEl) yesterdayEl.innerHTML = getDailyProgressCellHTML(yesterday, yesterdayBreakdown, 'SUBMIT KEMARIN');

        const twoDaysEl = document.getElementById(`${surveyType}-stat-2days`);
        if(twoDaysEl) twoDaysEl.innerHTML = getDailyProgressCellHTML(twoDaysAgo, twoDaysAgoBreakdown, 'SUBMIT 2 HARI LALU');

        // Calculate and set card percentages with dynamic precision for small numbers
        const formatPctVal = (v, tot) => {
            if (tot <= 0) return '0.00';
            const pct = (v / tot) * 100;
            if (pct > 0 && pct < 0.01) return pct.toFixed(4);
            return pct.toFixed(2);
        };
        const pctToday = formatPctVal(today, prelist);
        const pctYesterday = formatPctVal(yesterday, prelist);
        const pctTwoDays = formatPctVal(twoDaysAgo, prelist);

        const todayPctEl = document.getElementById(`${surveyType}-stat-today-pct`);
        if(todayPctEl) todayPctEl.textContent = `(${pctToday}%)`;

        const yesterdayPctEl = document.getElementById(`${surveyType}-stat-yesterday-pct`);
        if(yesterdayPctEl) yesterdayPctEl.textContent = `(${pctYesterday}%)`;

        const twoDaysPctEl = document.getElementById(`${surveyType}-stat-2days-pct`);
        if(twoDaysPctEl) twoDaysPctEl.textContent = `(${pctTwoDays}%)`;

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
        // Render Table with Filtering & Sorting
        if (!window.expandedSeKabs) {
            window.expandedSeKabs = { se_umum: {}, se_ub: {} };
        }
        if (!window.expandedSeKabs[surveyType]) {
            window.expandedSeKabs[surveyType] = {};
        }

        const searchVal = (document.getElementById(`${surveyType}-search-input`).value || '').toLowerCase().trim();
        const capaianFilterVal = document.getElementById(`${surveyType}-capaian-filter`)?.value || 'all';
        const tbody = document.getElementById(`${surveyType}-table-body`);
        tbody.innerHTML = '';

        let filtered = surveyData.map(item => {
            const kabMatch = item.kabupaten.toLowerCase().includes(searchVal);
            const matchingKecs = (item.kecamatan_list || []).filter(kec => 
                kec.kec_name.toLowerCase().includes(searchVal)
            );
            
            if (kabMatch || matchingKecs.length > 0) {
                if (!kabMatch && matchingKecs.length > 0 && searchVal !== "") {
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

        // Update title and toggle expand/collapse visibility
        const tableTitleEl = document.getElementById(`${surveyType}-table-title`);
        const expandCollapseEl = document.getElementById(`${surveyType}-expand-collapse-btns`);
        if (tableTitleEl) {
            const titles = { kabupaten: 'Rincian per Kabupaten/Kota', kecamatan: 'Rincian per Kecamatan', petugas: 'Rincian per Petugas' };
            tableTitleEl.textContent = titles[viewLevel] || titles.kabupaten;
        }
        if (expandCollapseEl) {
            expandCollapseEl.style.display = viewLevel === 'kabupaten' ? '' : 'none';
        }
        const roleFilterEl = document.getElementById(`${surveyType}-role-filter`);
        if (roleFilterEl) {
            roleFilterEl.style.display = viewLevel === 'petugas' ? '' : 'none';
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

        // ===== KECAMATAN FLAT LIST RENDERER =====
        function renderKecamatanFlatList() {
            // Build flat list of all kecamatan from all kabupaten
            const allKecs = [];
            surveyData.forEach(kab => {
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

            // Render kecamatan-specific headers
            const table = document.querySelector(`#tab-content-${surveyType} .ipas-table`);
            const thead = table?.querySelector('thead');
            if (thead) {
                thead.innerHTML = `
                    <tr>
                        <th style="font-family:'Outfit',sans-serif;">Kabupaten/Kota</th>
                        <th style="font-family:'Outfit',sans-serif;">Kecamatan</th>
                        <th style="font-family:'Outfit',sans-serif;text-align:right;color:var(--text-secondary);">Total Target</th>
                        <th style="font-family:'Outfit',sans-serif;text-align:right;color:#f59e0b;">Draft</th>
                        <th style="font-family:'Outfit',sans-serif;text-align:right;color:#3b82f6;">Open</th>
                        <th colspan="4" style="font-family:'Outfit',sans-serif;text-align:center;color:var(--color-delivered);border-bottom:2px solid rgba(16,185,129,0.3);">Submitted (Selesai)</th>
                        <th style="font-family:'Outfit',sans-serif;text-align:center;">% Capaian</th>
                    </tr>
                    <tr>
                        <th style="padding:0.3rem 0;"></th>
                        <th style="padding:0.3rem 0;"></th>
                        <th style="padding:0.3rem 0;"></th>
                        <th style="padding:0.3rem 0;"></th>
                        <th style="padding:0.3rem 0;"></th>
                        <th style="font-family:'Outfit',sans-serif;text-align:right;color:var(--color-delivered);font-size:0.8rem;padding:0.3rem 0.75rem;">Total</th>
                        <th style="font-family:'Outfit',sans-serif;text-align:right;color:var(--color-opened);font-size:0.8rem;padding:0.3rem 0.75rem;">Hari Ini</th>
                        <th style="font-family:'Outfit',sans-serif;text-align:right;color:#f59e0b;font-size:0.8rem;padding:0.3rem 0.75rem;">Kemarin</th>
                        <th style="font-family:'Outfit',sans-serif;text-align:right;color:var(--color-clicked);font-size:0.8rem;padding:0.3rem 0.75rem;">H-2</th>
                        <th style="padding:0.3rem 0;"></th>
                    </tr>
                `;
            }

            tbody.innerHTML = '';
            if (allKecs.length === 0) {
                tbody.innerHTML = `<tr><td colspan="11" style="text-align:center;padding:3rem 1rem;color:var(--text-secondary);">Tidak ada kecamatan yang cocok dengan pencarian.</td></tr>`;
                return;
            }

            // Sort by persentase desc, then total_prelist desc
            allKecs.sort((a, b) => {
                const pctA = parseFloat(a.persentase) || 0;
                const pctB = parseFloat(b.persentase) || 0;
                if (pctA !== pctB) return pctB - pctA;
                return (b.total_prelist || 0) - (a.total_prelist || 0);
            });

            allKecs.forEach(kec => {
                const pct = parseFloat(kec.persentase) || 0;
                const pctClass = pct >= 80 ? 'background-color:rgba(16,185,129,0.1);color:#10b981;border:1px solid rgba(16,185,129,0.2);' :
                                 pct >= 50 ? 'background-color:rgba(245,158,11,0.1);color:#f59e0b;border:1px solid rgba(245,158,11,0.2);' :
                                             'background-color:rgba(239,68,68,0.1);color:#ef4444;border:1px solid rgba(239,68,68,0.2);';

                const tdToday = getDailyProgressCellHTML(kec.today_completed, kec.today_completed_breakdown, 'HARI INI: KEC. ' + kec.kec_name);
                const tdYesterday = getDailyProgressCellHTML(kec.yesterday_completed, kec.yesterday_completed_breakdown, 'KEMARIN: KEC. ' + kec.kec_name);
                const isEstimate = kec.two_days_ago_is_estimate;
                const tdTwoDays = getDailyProgressCellHTML(kec.two_days_ago_completed, kec.two_days_ago_completed_breakdown, 'H-2: KEC. ' + kec.kec_name, isEstimate);

                const row = document.createElement('tr');
                row.innerHTML = `
                    <td style="font-size:0.8rem;color:var(--text-secondary);font-weight:600;">${kec.kab_name.replace(/\[\d+\] /, '')}</td>
                    <td style="font-weight:600;color:var(--text-primary);">${kec.kec_name}</td>
                    <td style="text-align:right;font-family:monospace;color:var(--text-secondary);">${formatNum(kec.total_prelist)}</td>
                    <td style="text-align:right;font-family:monospace;color:#f59e0b;">${formatNum(kec.total_draft)}</td>
                    <td style="text-align:right;font-family:monospace;color:#3b82f6;">${formatNum(kec.total_open)}</td>
                    <td style="text-align:right;font-family:monospace;font-weight:700;color:var(--color-delivered);">${formatNum(kec.total_submitted)}</td>
                    <td style="text-align:right;font-family:monospace;">${tdToday}</td>
                    <td style="text-align:right;font-family:monospace;">${tdYesterday}</td>
                    <td style="text-align:right;font-family:monospace;">${tdTwoDays}</td>
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
                        <th class="sortable" onclick="sortPetugasTable('${surveyType}', 'role')" style="font-family:'Outfit',sans-serif;">Role${getIcon('role')}</th>
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
                tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;padding:3rem 1rem;color:var(--text-secondary);">Tidak ada petugas yang cocok dengan pencarian / filter.</td></tr>`;
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
                        ${officer.username || officer.email || '-'}
                        <div style="font-size:0.7rem;color:var(--text-muted);">${officer.email || ''}</div>
                    </td>
                    <td><span style="font-size:0.75rem;padding:0.15rem 0.5rem;border-radius:0.35rem;background:${roleBgColor};color:${roleTextColor};font-weight:700;">${officer.roleName || '-'}</span></td>
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
                    <td colspan="11" style="text-align: center; padding: 3rem 1rem; color: var(--text-secondary);">
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

            const tdToday = getDailyProgressCellHTML(item.today_completed, item.today_completed_breakdown, 'HARI INI: KAB. ' + item.kabupaten.replace(/\[\d+\] /, ''));
            const tdYesterday = getDailyProgressCellHTML(item.yesterday_completed, item.yesterday_completed_breakdown, 'KEMARIN: KAB. ' + item.kabupaten.replace(/\[\d+\] /, ''));
            const tdTwoDays = getDailyProgressCellHTML(item.two_days_ago_completed, item.two_days_ago_completed_breakdown, 'H-2: KAB. ' + item.kabupaten.replace(/\[\d+\] /, ''), item.two_days_ago_is_estimate);

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
                <td style="text-align: right; font-family: monospace;">${tdToday}</td>
                <td style="text-align: right; font-family: monospace;">${tdYesterday}</td>
                <td style="text-align: right; font-family: monospace;">${tdTwoDays}</td>
                
                <td style="text-align: center;">
                    <span style="display: inline-block; padding: 0.25rem 0.5rem; border-radius: 0.5rem; font-size: 0.75rem; font-weight: 800; ${pctClass}">
                        ${item.persentase}%
                    </span>
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

                    const kecPenambahanBadge = `<div onclick="openNewBusinessesModal('${kecEscaped}', '${encodedKecBusinessesJSON}', 'all')" style="cursor: pointer; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 0.1rem;" onmouseover="this.style.opacity='0.8';" onmouseout="this.style.opacity='1';">
                            <span style="font-weight: 800; color: var(--primary); font-size: 0.85rem;">${formatNum(kec.new_usaha_overall + kec.new_rumah_overall)}</span>
                            <span style="font-size: 0.65rem; font-weight: 600; color: var(--text-secondary);">${kec.new_usaha_overall} usaha | ${kec.new_rumah_overall} rumah</span>
                            <span style="font-size: 0.6rem; color: var(--text-muted);">+${kec.new_usaha_today + kec.new_rumah_today} hari ini</span>
                        </div>`;

                    kecRow.innerHTML = `
                        <td style="font-weight: 600;">↳ ${highlightText(kec.kec_name, searchVal)}</td>
                        <td style="text-align: right; font-family: monospace; font-weight: 500; color: var(--text-secondary);">${formatNum(kec.total_prelist)}</td>
                        <td style="text-align: right; font-family: monospace; font-weight: 500; color: #f59e0b;">${formatNum(kec.total_draft)}</td>
                        <td style="text-align: right; font-family: monospace; font-weight: 500; color: #3b82f6;">${formatNum(kec.total_open)}</td>
                        
                        <td style="text-align: right; font-family: monospace; font-weight: 700; color: var(--color-delivered);">${formatNum(kec.total_submitted)}</td>
                        <td style="text-align: right; font-family: monospace;">${kecToday}</td>
                        <td style="text-align: right; font-family: monospace;">${kecYesterday}</td>
                        <td style="text-align: right; font-family: monospace;">${kecTwoDays}</td>
                        
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
            <td style="font-weight: 800; color: var(--text-primary);">[72] PROVINSI SULAWESI TENGAH</td>
            <td style="text-align: right; font-family: monospace; font-weight: 700; color: var(--text-secondary);">${formatNum(prelist)}</td>
            <td style="text-align: right; font-family: monospace; font-weight: 700; color: #f59e0b;">${formatNum(draft)}</td>
            <td style="text-align: right; font-family: monospace; font-weight: 700; color: #3b82f6;">${formatNum(openVal)}</td>
            
            <td style="text-align: right; font-family: monospace; font-weight: 800; color: var(--color-delivered);">${formatNum(submitted)}</td>
            <td style="text-align: right; font-family: monospace;">${provTodayHTML}</td>
            <td style="text-align: right; font-family: monospace;">${provYesterdayHTML}</td>
            <td style="text-align: right; font-family: monospace;">${provTwoDaysHTML}</td>
            
            <td style="text-align: center;">
                <span style="display: inline-block; padding: 0.25rem 0.5rem; border-radius: 0.5rem; font-size: 0.75rem; font-weight: 800; ${provPctClass}">
                    ${persentase}%
                </span>
            </td>
            <td style="text-align: center;">
                ${provPenambahanBadge}
            </td>
        `;
        tbody.appendChild(provRow);

        // Render Chart
        if (!window.currentChartType) window.currentChartType = { se_umum: 'bar', se_ub: 'bar' };

        window.toggleChartType = function (type) {
            const current = window.currentChartType[type] || 'bar';
            let next = 'line';
            if (current === 'bar') {
                next = 'line';
            } else if (current === 'line') {
                next = 'line_daily';
            } else if (current === 'line_daily') {
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
                let labels = ['H-2', 'Kemarin', 'Hari Ini'];
                let dataPoints = (cType === 'line')
                    ? [submitted - today - yesterday, submitted - today, submitted]
                    : [twoDaysAgo, yesterday, today];
                
                const stats = window.DAILY_SUBMISSION_STATS;
                if (stats && Array.isArray(stats) && stats.length > 0) {
                    const filtered = stats.filter(r => r.survey_type === surveyType);
                    const dateMap = {};
                    filtered.forEach(r => {
                        const d = r.date;
                        if (d) {
                            dateMap[d] = (dateMap[d] || 0) + (r.count || 0);
                        }
                    });
                    
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
                            } catch(e) {}
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
                            label: 'Total Target',
                            data: sortedForBar.map(i => i.total_prelist || 0),
                            backgroundColor: 'rgba(239, 68, 68, 0.85)', // Red
                            borderRadius: 4,
                            grouped: false,
                            order: 2
                        },
                        {
                            label: 'Submitted (Selesai)',
                            data: sortedForBar.map(i => i.total_submitted || 0),
                            backgroundColor: 'rgba(16, 185, 129, 0.85)', // Green
                            borderRadius: 4,
                            minBarLength: 6,
                            grouped: false,
                            order: 1
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
                            stacked: false,
                            grid: { color: gridColor },
                            ticks: { color: textColor }
                        },
                        x: {
                            stacked: false,
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
    };

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

    window.switchAssignSubtab = function(tabName) {
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
    window.changeSlsLimit = function(val) {
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
            <th onclick="sortSlsTable('unsynced')" style="font-family: 'Outfit', sans-serif; text-align: center; color: #f59e0b; cursor: pointer; user-select: none;">Belum Sync${getIcon('unsynced')}</th>
            <th style="font-family: 'Outfit', sans-serif; user-select: none;">Status & Petugas</th>
        `;
    }

    function renderSlsTable() {
        const tbody = document.getElementById('sls-table-body');
        if (!tbody) return;

        if (!window.ASSIGN_SLS_DATA || window.ASSIGN_SLS_DATA.length === 0) {
            tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; padding: 2rem; color: var(--text-secondary);">Data SLS belum tersedia. Pastikan sinkronisasi data sedang berjalan.</td></tr>`;
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
            tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; padding: 3rem 1rem; color: var(--text-secondary);">Tidak ada data SLS yang cocok dengan filter pencarian.</td></tr>`;
            document.getElementById('sls-pagination-info').textContent = 'Menampilkan 0 - 0 dari 0 SLS';
            document.getElementById('sls-pagination-buttons').innerHTML = '';
            return;
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
                <tr style="border-bottom: 1px solid var(--card-border); transition: background-color 0.2s;">
                    <td style="padding: 1rem; color: var(--text-secondary); font-weight: 500;">${hl(item.kab_name)}</td>
                    <td style="padding: 1rem; color: var(--text-secondary);">${hl(item.kec_name)}</td>
                    <td style="padding: 1rem; color: var(--text-secondary);">${hl(item.desa_name)}</td>
                    <td style="padding: 1rem; font-weight: 600; color: var(--text);">${hl(item.sls_name)} <span style="font-size: 0.75rem; font-weight: 400; color: var(--text-secondary); display:block;">${hl(item.sls_code)}</span></td>
                    <td style="padding: 1rem; text-align: center; font-weight: 600;">${item.total}</td>
                    <td style="padding: 1rem; text-align: center; color: #10b981; font-weight: 600;">${item.assigned}</td>
                    <td style="padding: 1rem; text-align: center; color: #ef4444; font-weight: 600;">${item.unassigned}</td>
                    <td style="padding: 1rem; text-align: center; color: #f59e0b; font-weight: 600;">${unsynced}</td>
                    <td style="padding: 1rem;">
                        <div style="display: flex; flex-direction: column; gap: 0.25rem;">
                            <div>${badge}</div>
                            <span style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.25rem; display: block;">${hl(officers)}</span>
                        </div>
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
        
        // Build a lookup map of sync_count from active ASSIGN_SLS_DATA
        const localSyncMap = {};
        if (window.ASSIGN_SLS_DATA) {
            window.ASSIGN_SLS_DATA.forEach(sls => {
                const code = sls.sls_code || sls.sls_id;
                if (code) {
                    localSyncMap[code] = sls.sync_count || 0;
                }
            });
        }
        
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
        if (totalItems === 0) {
            tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; padding: 2rem; color: var(--text-secondary);">Tidak ada data petugas yang cocok.</td></tr>`;
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
            
            const regionBadges = (item.regions || []).map(r => {
                const badgeTxt = r.regionName && r.regionName !== '-' ? r.regionName : 'LAINNYA';
                const codeTxt = r.regionCode ? ` (${r.regionCode})` : '';
                return `<span style="display: inline-flex; align-items: center; background: rgba(99, 102, 241, 0.08); color: var(--text-primary); border: 1px solid rgba(99, 102, 241, 0.2); padding: 0.2rem 0.6rem; border-radius: 1rem; font-size: 0.75rem; white-space: nowrap; margin: 0.15rem;">
                    <svg fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" style="width: 12px; height: 12px; margin-right: 0.35rem; color: var(--primary);" viewBox="0 0 24 24"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
                    ${hl(badgeTxt + codeTxt)}
                </span>`;
            }).join('');
            
            const wilHtml = regionBadges || '<span style="color:var(--text-muted); font-size:0.8rem;">Tidak ada wilayah tugas</span>';

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
                            </div>
                        </div>
                    </td>
                    <td style="padding: 1rem;">
                        <span style="display: inline-block; padding: 0.25rem 0.6rem; border-radius: 0.5rem; background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.2); color: #f59e0b; font-size: 0.75rem; font-weight: 700;">
                            ${hl(item.roleName || '-')}
                        </span>
                    </td>
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
                    <td colspan="6" style="padding: 1.25rem 1.5rem;">
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
    
    window.changeSyncLimit = function(val) {
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

    window.renderSyncTable = function() {
        const tbody = document.getElementById('sync-table-body');
        const paginationInfo = document.getElementById('sync-pagination-info');
        if (!tbody || !paginationInfo) return;

        if (!window.ASSIGN_SLS_DATA || window.ASSIGN_SLS_DATA.length === 0) {
            tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; padding: 2rem; color: var(--text-secondary);">Data SLS belum tersedia. Pastikan sinkronisasi data sedang berjalan.</td></tr>`;
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
            tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; padding: 2rem; color: var(--text-secondary);">Tidak ada data SLS Sync yang cocok dengan filter.</td></tr>`;
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

    window.downloadSyncCSV = function() {
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
                        snapshotSelect.innerHTML = '<option value="live" style="background-color: var(--card-bg); color: var(--text-primary);">Terbaru (Live)</option>' +
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

        if (supabaseClient) {
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
            script.src = 'data.js?v=' + Date.now();
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

        if (snapshotDate !== 'live') {
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

        if (supabaseClient) {
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
                    const assignVal = assignDbData.value;
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
                    window.DAILY_SUBMISSION_STATS = timelineDbData.value;
                    timelineLoadedFromDb = true;
                    console.log(`Loaded DAILY_SUBMISSION_STATS (${timelineKey}) from Supabase.`);
                }
            } catch (e) {
                console.warn(`Failed to fetch DAILY_SUBMISSION_STATS (${timelineKey}) from Supabase:`, e);
            }
        }

        if (!ipasLoadedFromDb) {
            // Dynamically reload IPAS ipas_data.js
            await new Promise((resolve) => {
                const script = document.createElement('script');
                script.src = 'ipas_data.js?v=' + Date.now();
                script.onload = () => resolve();
                script.onerror = () => resolve();
                document.head.appendChild(script);
            });
        }

        if (!assignLoadedFromDb) {
            // Dynamically reload assign_data.js
            await new Promise((resolve) => {
                const script = document.createElement('script');
                script.src = 'assign_data.js?v=' + Date.now();
                script.onload = () => resolve();
                script.onerror = () => resolve();
                document.head.appendChild(script);
            });
        }

        if (!syncLoadedFromDb) {
            // Dynamically reload sync_data.js
            await new Promise((resolve) => {
                const script = document.createElement('script');
                script.src = 'sync_data.js?v=' + Date.now();
                script.onload = () => resolve();
                script.onerror = () => resolve();
                document.head.appendChild(script);
            });
        }

        if (!timelineLoadedFromDb) {
            // Dynamically reload daily_submission_stats.js
            await new Promise((resolve) => {
                const script = document.createElement('script');
                script.src = 'daily_submission_stats.js?v=' + Date.now();
                script.onload = () => resolve();
                script.onerror = () => resolve();
                document.head.appendChild(script);
            });
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
    window.filterAssignData = function(type) {
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

        if (typeof originalFilterAssignData === 'function') {
            originalFilterAssignData(type);
            
            const chartTitle = document.getElementById("assign-chart-title");
            const slsTitle = document.getElementById("assign-sls-title");
            if (type === 'se2026') {
                if(chartTitle) chartTitle.innerText = "Status Assign Petugas (Semua Usaha - SE Umum)";
                if(slsTitle) slsTitle.innerText = "Ringkasan Assignment per Kabupaten/Kota (SE Umum)";
            } else {
                if(chartTitle) chartTitle.innerText = "Status Assign Petugas (Usaha Besar - UB)";
                if(slsTitle) slsTitle.innerText = "Ringkasan Assignment per Kabupaten/Kota (UB)";
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

    window.toggleStatsDetail = function(section) {
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

    window.updateTimelineView = function() {
        const kabFilter = document.getElementById('timeline-kab-filter')?.value || 'all';
        const typeFilter = document.getElementById('timeline-type-filter')?.value || 'all';
        
        if (!window.DAILY_SUBMISSION_STATS || !Array.isArray(window.DAILY_SUBMISSION_STATS) || window.DAILY_SUBMISSION_STATS.length === 0) {
            // Show empty state in KPI and table
            const statTotal = document.getElementById('timeline-stat-total');
            const statAvg = document.getElementById('timeline-stat-avg');
            const statPeakDay = document.getElementById('timeline-stat-peak-day');
            const substatPeakVal = document.getElementById('timeline-substat-peak-val');
            if (statTotal) statTotal.innerText = '0';
            if (statAvg) statAvg.innerText = '0';
            if (statPeakDay) statPeakDay.innerText = '-';
            if (substatPeakVal) substatPeakVal.innerText = '0 submit';
            renderDailySubmissionChart([], []);
            const tbody = document.getElementById('timeline-table-body');
            if (tbody) tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;padding:2rem;color:var(--text-secondary);">Data progres harian belum tersedia. Jalankan scrape_granular_assignments.py terlebih dahulu.</td></tr>`;
            return;
        }
        
        const filtered = window.DAILY_SUBMISSION_STATS.filter(r => {
            if (kabFilter !== 'all') {
                // Dropdown values are like "[01] BANGGAI KEPULAUAN", data has "BANGGAI KEPULAUAN"
                const cleanFilter = kabFilter.replace(/^\[\d+\]\s*/, '').trim().toUpperCase();
                if ((r.kab_name || '').toUpperCase() !== cleanFilter) return false;
            }
            if (typeFilter !== 'all' && r.survey_type !== typeFilter) return false;
            return true;
        });
        
        const dateMap = {};
        filtered.forEach(r => {
            const d = r.date;
            if (!dateMap[d]) dateMap[d] = 0;
            dateMap[d] += (r.count || 0);
        });
        
        const sortedDates = Object.keys(dateMap).sort();
        const sortedCounts = sortedDates.map(d => dateMap[d]);
        
        let total = 0;
        let peakDay = '-';
        let peakVal = 0;
        
        sortedDates.forEach((d, idx) => {
            const val = sortedCounts[idx];
            total += val;
            if (val > peakVal) {
                peakVal = val;
                peakDay = d;
            }
        });
        
        const avg = sortedDates.length > 0 ? (total / sortedDates.length).toFixed(1) : 0;
        
        const statTotal = document.getElementById('timeline-stat-total');
        const statAvg = document.getElementById('timeline-stat-avg');
        const statPeakDay = document.getElementById('timeline-stat-peak-day');
        const substatPeakVal = document.getElementById('timeline-substat-peak-val');
        
        const fmt = (n) => new Intl.NumberFormat('id-ID').format(n || 0);
        
        if (statTotal) statTotal.innerText = fmt(total);
        if (statAvg) statAvg.innerText = fmt(avg);
        if (statPeakDay) statPeakDay.innerText = peakDay;
        if (substatPeakVal) substatPeakVal.innerText = `${fmt(peakVal)} submit`;
        
        renderDailySubmissionChart(sortedDates, sortedCounts);
        renderTimelineTable(sortedDates, dateMap, kabFilter, typeFilter);
    };

    // --- GRANULAR DATA UTILITIES ---

    window.decompressAndParseGranular = function(compressedBase64) {
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
            
            console.log(`Rebuilding ${targets.length} targets...`);
            const rebuilt = targets.map((t) => {
                const regIdx = t[5];
                const petIdx = t[4];
                const statIdx = t[3];
                
                const reg = regIdx >= 0 && regIdx < regions.length ? regions[regIdx] : ["-", "-", "-", "-", "-", "-", "-", "-"];
                const pet = petIdx >= 0 && petIdx < petugas.length ? petugas[petIdx] : ["-", "-"];
                const stat = statIdx >= 0 && statIdx < statuses.length ? statuses[statIdx] : "OPEN";
                
                return {
                    id: t[0],
                    codeIdentity: t[1],
                    data1: t[2],
                    status: stat,
                    petugas_username: pet[0],
                    petugas_fullname: pet[1],
                    kab_code: reg[0],
                    kab_name: reg[1],
                    kec_code: reg[2],
                    kec_name: reg[3],
                    desa_code: reg[4],
                    desa_name: reg[5],
                    sls_code: reg[6],
                    sls_name: reg[7],
                    dateModifiedEpoch: t[6],
                    survey_type: t[7] === 0 ? 'se_umum' : 'se_ub'
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

    async function loadGranularAssignmentsData() {
        const tbody = document.getElementById('assign-sls-table-body');
        if (window.GRANULAR_ASSIGNMENTS_DATA) {
            // Re-populate status filter in case it's empty (e.g. after tab switch)
            const statusSelect = document.getElementById('assign-sls-status-filter');
            if (statusSelect && statusSelect.options.length <= 1) {
                const uniqueStatuses = new Set();
                window.GRANULAR_ASSIGNMENTS_DATA.forEach(r => {
                    if (r.status) uniqueStatuses.add(r.status);
                });
                statusSelect.innerHTML = '<option value="all">Semua Status</option>' +
                    Array.from(uniqueStatuses).sort().map(s => `<option value="${s}">${s}</option>`).join('');
            }
            window.renderGranularAssignmentsTable();
            return;
        }
        
        if (isGranularLoading) return;
        isGranularLoading = true;
        
        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" style="text-align: center; padding: 3rem; color: var(--text-secondary);">
                        <svg style="animation: spin 1s linear infinite; margin: 0 auto 1rem; width: 24px; height: 24px; color: var(--primary);" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle style="opacity: 0.25;" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                            <path style="opacity: 0.75;" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Memuat rincian data target assignment...
                    </td>
                </tr>
            `;
        }

        const snapshotSelect = document.getElementById('select-snapshot-date');
        const snapshotDate = snapshotSelect ? snapshotSelect.value : 'live';
        const granularKey = snapshotDate === 'live' ? 'granular_assignments' : `granular_assignments:${snapshotDate}`;

        let compressedData = null;

        if (supabaseClient) {
            try {
                console.log(`Fetching granular data (${granularKey}) from Supabase...`);
                const { data, error } = await supabaseClient
                    .from('dashboard_store')
                    .select('value')
                    .eq('key', granularKey)
                    .single();
                    
                if (!error && data && data.value && data.value.compressed_data) {
                    compressedData = data.value.compressed_data;
                    console.log("Successfully fetched granular data from Supabase.");
                }
            } catch (e) {
                console.warn("Failed to fetch granular data from Supabase:", e);
            }
        }

        if (!compressedData) {
            if (typeof window.COMPRESSED_GRANULAR_ASSIGNMENTS !== 'undefined' && window.COMPRESSED_GRANULAR_ASSIGNMENTS) {
                compressedData = window.COMPRESSED_GRANULAR_ASSIGNMENTS;
                console.log("Using preloaded window.COMPRESSED_GRANULAR_ASSIGNMENTS.");
            } else {
                console.log("Loading granular_assignments.js fallback script...");
                await new Promise((resolve) => {
                    const script = document.createElement('script');
                    script.src = 'granular_assignments.js?v=' + Date.now();
                    script.onload = () => resolve();
                    script.onerror = () => resolve();
                    document.head.appendChild(script);
                });
                if (typeof window.COMPRESSED_GRANULAR_ASSIGNMENTS !== 'undefined' && window.COMPRESSED_GRANULAR_ASSIGNMENTS) {
                    compressedData = window.COMPRESSED_GRANULAR_ASSIGNMENTS;
                    console.log("Successfully loaded granular data from script fallback.");
                }
            }
        }

        if (compressedData) {
            window.GRANULAR_ASSIGNMENTS_DATA = window.decompressAndParseGranular(compressedData);
            isGranularLoading = false;
            // Trigger filters initialization for default "all"
            window.updateGranularFilters('kab');
        } else {
            isGranularLoading = false;
            if (tbody) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="8" style="text-align: center; padding: 2rem; color: var(--text-secondary);">
                            Gagal memuat rincian data assignment dari database maupun file lokal. Harap jalankan scrape_granular_assignments.py terlebih dahulu.
                        </td>
                    </tr>
                `;
            }
        }
    }

    // --- GRANULAR TABLE FILTERS, SORT & RENDER ---

    window.granularCurrentPage = 1;
    window.granularPageLimit = 50;
    window.granularSortField = 'kab';
    window.granularSortAsc = true;
    
    window.changeGranularLimit = function(limit) {
        window.granularPageLimit = parseInt(limit);
        window.renderGranularAssignmentsTable(true);
    };

    window.sortGranularTable = function(field) {
        if (window.granularSortField === field) {
            window.granularSortAsc = !window.granularSortAsc;
        } else {
            window.granularSortField = field;
            window.granularSortAsc = true;
        }
        
        const fields = ['kab', 'kec', 'desa', 'sls', 'petugas', 'target', 'status'];
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

    window.updateGranularFilters = function(changedLevel) {
        const kabVal = document.getElementById('assign-sls-kab-filter')?.value || 'all';
        const kecSelect = document.getElementById('assign-sls-kec-filter');
        const desaSelect = document.getElementById('assign-sls-desa-filter');
        const slsSelect = document.getElementById('assign-sls-sls-filter');
        const statusSelect = document.getElementById('assign-sls-status-filter');
        
        if (!window.GRANULAR_ASSIGNMENTS_DATA) return;
        
        if (changedLevel === 'kab') {
            if (kabVal === 'all') {
                if (kecSelect) { kecSelect.innerHTML = '<option value="all">Semua Kecamatan</option>'; kecSelect.disabled = true; }
                if (desaSelect) { desaSelect.innerHTML = '<option value="all">Semua Desa</option>'; desaSelect.disabled = true; }
                if (slsSelect) { slsSelect.innerHTML = '<option value="all">Semua SLS</option>'; slsSelect.disabled = true; }
            } else {
                const kecs = new Set();
                window.GRANULAR_ASSIGNMENTS_DATA.forEach(r => {
                    if (r.kab_name === kabVal && r.kec_name && r.kec_name !== '-') {
                        kecs.add(r.kec_name);
                    }
                });
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
                window.GRANULAR_ASSIGNMENTS_DATA.forEach(r => {
                    if (r.kab_name === kabVal && r.kec_name === kecVal && r.desa_name && r.desa_name !== '-') {
                        desas.add(r.desa_name);
                    }
                });
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
                window.GRANULAR_ASSIGNMENTS_DATA.forEach(r => {
                    if (r.kab_name === kabVal && r.kec_name === kecVal && r.desa_name === desaVal && r.sls_name && r.sls_name !== '-') {
                        slss.add(`${r.sls_code} - ${r.sls_name}`);
                    }
                });
                const sortedSlss = Array.from(slss).sort();
                if (slsSelect) {
                    slsSelect.innerHTML = '<option value="all">Semua SLS</option>' + 
                        sortedSlss.map(s => `<option value="${s.split(' - ')[0]}">${s}</option>`).join('');
                    slsSelect.disabled = false;
                }
            }
        }
        
        if (changedLevel === 'kab') {
            const uniqueStatuses = new Set();
            window.GRANULAR_ASSIGNMENTS_DATA.forEach(r => {
                if (r.status) uniqueStatuses.add(r.status);
            });
            if (statusSelect) {
                statusSelect.innerHTML = '<option value="all">Semua Status</option>' + 
                    Array.from(uniqueStatuses).sort().map(s => `<option value="${s}">${s}</option>`).join('');
            }
        }
        
        window.renderGranularAssignmentsTable(true);
    };

    window.renderGranularAssignmentsTable = function(resetPage = true) {
        const tbody = document.getElementById('assign-sls-table-body');
        if (!tbody) return;
        
        if (!window.GRANULAR_ASSIGNMENTS_DATA) {
            tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; padding: 2rem; color: var(--text-secondary);">Rincian data target assignment belum dimuat. Silakan ubah filter Kabupaten/Kota.</td></tr>`;
            return;
        }
        
        if (resetPage) {
            window.granularCurrentPage = 1;
        }
        
        const kabVal = document.getElementById('assign-sls-kab-filter')?.value || 'all';
        const kecVal = document.getElementById('assign-sls-kec-filter')?.value || 'all';
        const desaVal = document.getElementById('assign-sls-desa-filter')?.value || 'all';
        const slsVal = document.getElementById('assign-sls-sls-filter')?.value || 'all';
        const statusVal = document.getElementById('assign-sls-status-filter')?.value || 'all';
        const searchVal = document.getElementById('assign-sls-search-input')?.value.toLowerCase().trim() || '';
        
        const activeSubtab = localStorage.getItem('active_assign_subtab') || 'se2026';
        const surveyTypeFilter = activeSubtab === 'se2026' ? 'se_umum' : 'se_ub';

        let filtered = window.GRANULAR_ASSIGNMENTS_DATA.filter(r => {
            if (r.survey_type !== surveyTypeFilter) return false;
            
            if (kabVal !== 'all' && r.kab_name !== kabVal) return false;
            if (kecVal !== 'all' && r.kec_name !== kecVal) return false;
            if (desaVal !== 'all' && r.desa_name !== desaVal) return false;
            if (slsVal !== 'all' && r.sls_code !== slsVal) return false;
            if (statusVal !== 'all' && r.status !== statusVal) return false;
            
            if (searchVal) {
                const matchText = (
                    (r.data1 || '') + ' ' + 
                    (r.petugas_username || '') + ' ' + 
                    (r.petugas_fullname || '') + ' ' +
                    (r.sls_name || '') + ' ' +
                    (r.sls_code || '') + ' ' +
                    (r.status || '')
                ).toLowerCase();
                if (!matchText.includes(searchVal)) return false;
            }
            return true;
        });
        
        filtered.sort((a, b) => {
            let valA = '', valB = '';
            switch (window.granularSortField) {
                case 'kab': valA = a.kab_name || ''; valB = b.kab_name || ''; break;
                case 'kec': valA = a.kec_name || ''; valB = b.kec_name || ''; break;
                case 'desa': valA = a.desa_name || ''; valB = b.desa_name || ''; break;
                case 'sls': valA = a.sls_name || ''; valB = b.sls_name || ''; break;
                case 'petugas': valA = a.petugas_fullname || ''; valB = b.petugas_fullname || ''; break;
                case 'target': valA = a.data1 || ''; valB = b.data1 || ''; break;
                case 'status': valA = a.status || ''; valB = b.status || ''; break;
            }
            
            let compare = valA.localeCompare(valB, 'id', { sensitivity: 'base' });
            return window.granularSortAsc ? compare : -compare;
        });
        
        const totalItems = filtered.length;
        const totalPages = Math.ceil(totalItems / window.granularPageLimit);
        
        const startIndex = (window.granularCurrentPage - 1) * window.granularPageLimit;
        const endIndex = Math.min(startIndex + window.granularPageLimit, totalItems);
        const paginated = filtered.slice(startIndex, endIndex);
        
        if (paginated.length === 0) {
            tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; padding: 3rem; color: var(--text-secondary);">Tidak ada data assignment yang cocok dengan kriteria filter.</td></tr>`;
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
            } else if (statusUpper === 'DRAFT') {
                statusBadgeClass = 'table-badge-submitted';
            }
                
            const petugasLabel = r.petugas_fullname && r.petugas_fullname !== '-' ? 
                `${r.petugas_fullname} <span style="font-size:0.75rem; color:var(--text-secondary); display:block; font-family:monospace;">@${r.petugas_username}</span>` : 
                '<span style="color:var(--text-muted); font-style:italic;">Belum Ditugaskan</span>';
                
            html += `
                <tr style="border-bottom: 1px solid var(--card-border); transition: background-color 0.15s;">
                    <td style="padding: 0.65rem 0.75rem; text-align: center; vertical-align: middle; font-weight: 600; color: var(--text-secondary);">${no}</td>
                    <td style="padding: 0.65rem 0.75rem; text-align: left; vertical-align: middle; font-weight: 600; color: var(--text-primary); font-size: 0.8rem;">${r.kab_name}</td>
                    <td style="padding: 0.65rem 0.75rem; text-align: left; vertical-align: middle; font-size: 0.8rem; color: var(--text-primary);">${r.kec_name}</td>
                    <td style="padding: 0.65rem 0.75rem; text-align: left; vertical-align: middle; font-size: 0.8rem; color: var(--text-primary);">${r.desa_name}</td>
                    <td style="padding: 0.65rem 0.75rem; text-align: left; vertical-align: middle; font-size: 0.8rem; color: var(--text-primary);">${r.sls_name} <span style="font-size:0.7rem; color:var(--text-secondary); display:block; font-family:monospace;">${r.sls_code}</span></td>
                    <td style="padding: 0.65rem 0.75rem; text-align: left; vertical-align: middle; font-size: 0.85rem; color: var(--text-primary);">${petugasLabel}</td>
                    <td style="padding: 0.65rem 0.75rem; text-align: left; vertical-align: middle; font-weight: 700; color: var(--text-primary); font-size: 0.85rem;">${r.data1} <span style="font-size:0.7rem; color:var(--text-secondary); display:block; font-family:monospace; font-weight:500;">ID: ${r.codeIdentity || '-'}</span></td>
                    <td style="padding: 0.65rem 0.75rem; text-align: center; vertical-align: middle;">
                        <span class="table-badge ${statusBadgeClass}">${r.status}</span>
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
            pagBtns.innerHTML = btnsHtml;
        }
    };
    
    window.setGranularPage = function(page) {
        window.granularCurrentPage = page;
        window.renderGranularAssignmentsTable(false);
    };

    window.downloadGranularAssignCSV = function() {
        if (!window.GRANULAR_ASSIGNMENTS_DATA) return;
        
        const kabVal = document.getElementById('assign-sls-kab-filter')?.value || 'all';
        const kecVal = document.getElementById('assign-sls-kec-filter')?.value || 'all';
        const desaVal = document.getElementById('assign-sls-desa-filter')?.value || 'all';
        const slsVal = document.getElementById('assign-sls-sls-filter')?.value || 'all';
        const statusVal = document.getElementById('assign-sls-status-filter')?.value || 'all';
        const searchVal = document.getElementById('assign-sls-search-input')?.value.toLowerCase().trim() || '';
        const activeSubtab = localStorage.getItem('active_assign_subtab') || 'se2026';
        const surveyTypeFilter = activeSubtab === 'se2026' ? 'se_umum' : 'se_ub';

        let filtered = window.GRANULAR_ASSIGNMENTS_DATA.filter(r => {
            if (r.survey_type !== surveyTypeFilter) return false;
            if (kabVal !== 'all' && r.kab_name !== kabVal) return false;
            if (kecVal !== 'all' && r.kec_name !== kecVal) return false;
            if (desaVal !== 'all' && r.desa_name !== desaVal) return false;
            if (slsVal !== 'all' && r.sls_code !== slsVal) return false;
            if (statusVal !== 'all' && r.status !== statusVal) return false;
            if (searchVal) {
                const matchText = (
                    (r.data1 || '') + ' ' + 
                    (r.petugas_username || '') + ' ' + 
                    (r.petugas_fullname || '') + ' ' +
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

        let csvContent = '\uFEFFNo;Kabupaten;Kecamatan;Desa;Kode SLS;Nama SLS;Username Petugas;Nama Petugas;ID Target;Nama Assignment;Status;Jenis Sensus\r\n';
        filtered.forEach((r, idx) => {
            const no = idx + 1;
            const kab = (r.kab_name || '-').replace(/"/g, '""');
            const kec = (r.kec_name || '-').replace(/"/g, '""');
            const desa = (r.desa_name || '-').replace(/"/g, '""');
            const slsCode = r.sls_code || '-';
            const slsName = (r.sls_name || '-').replace(/"/g, '""');
            const petUser = r.petugas_username || '-';
            const petName = (r.petugas_fullname || '-').replace(/"/g, '""');
            const targetId = r.codeIdentity || '-';
            const targetName = (r.data1 || '-').replace(/"/g, '""');
            const status = r.status || 'OPEN';
            const type = r.survey_type === 'se_umum' ? 'SE Umum' : 'SE UB';
            
            csvContent += `"${no}";"${kab}";"${kec}";"${desa}";"${slsCode}";"${slsName}";"${petUser}";"${petName}";"${targetId}";"${targetName}";"${status}";"${type}"\r\n`;
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
    };

    window.toggleStatsDetail = function(section) {
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

    // Initial Execution
    fetchDataAndRender().then(() => {
        // Restore active tab from localStorage, default to 'se_umum'
        const activeTab = localStorage.getItem('active_tab') || 'se_umum';
        window.switchTab(activeTab);
    });
});