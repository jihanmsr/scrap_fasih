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
            viewModeToggleBtn.textContent = isTable ? '📇 Mode Kartu' : '📋 Mode Tabel';
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
    const savedTheme = localStorage.getItem('theme') || 'dark';
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
                    const kabkotName = (comp.code && typeof comp.code === 'string') ? (kabkotMapping[comp.code.substring(0, 4)] || 'Lainnya') : 'Lainnya';
                    const lastLog = comp.history.length ? comp.history[comp.history.length - 1] : { status: '-', timestamp: '-' };

                    return `
                        <tr>
                            <td>${highlightText(comp.code, searchQuery)}</td>
                            <td style="font-weight: 700;">${highlightText(comp.company_name, searchQuery)}</td>
                            <td>${highlightText(comp.email, searchQuery)}</td>
                            <td><span class="company-status-badge" style="--badge-bg: ${statusStyle.bg}; --badge-color: ${statusStyle.color}; --badge-border: ${statusStyle.border};">${comp.global_status}</span></td>
                            <td><span class="survey-status-badge" style="background-color: ${surveyStyle.bg}; color: ${surveyStyle.color}; border: 1px solid ${surveyStyle.border};">${comp.survey_status}</span></td>
                            <td>${kabkotName}</td>
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

                const surveyStyle = getSurveyStatusStyle(comp.survey_status);
                card.innerHTML = `
                    <div class="company-header">
                        <div class="company-info">
                            <div class="company-name-row">
                                <div class="company-name">${highlightText(comp.company_name, searchQuery)}</div>
                            </div>
                            <div class="company-meta">
                                <span class="code-badge">${highlightText(comp.code, searchQuery)}</span>
                                <span class="code-badge" style="background-color: rgba(99, 102, 241, 0.08); color: var(--primary); border: 1px solid rgba(99, 102, 241, 0.15); font-weight: 700;">
                                    ${(comp.code && typeof comp.code === 'string') ? (kabkotMapping[comp.code.substring(0, 4)] || 'Lainnya') : 'Lainnya'}
                                </span>
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
                <th rowspan="2" class="sortable" onclick="sortSeTable('${surveyType}', 'total_prelist')" style="font-family: 'Outfit', sans-serif; text-align: right; vertical-align: middle;">
                    Total Target${getIcon('total_prelist')}
                </th>
                <th rowspan="2" class="sortable" onclick="sortSeTable('${surveyType}', 'new_usaha_today')" style="font-family: 'Outfit', sans-serif; text-align: center; vertical-align: middle;">
                    Penambahan${getIcon('new_usaha_today')}
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

    // Sensus Ekonomi Dashboard Render Engine (Umum or UB)
    window.renderSeDashboard = function (surveyType) {
        const ipasDataObj = window.IPAS_DATA || { se_umum: [], se_ub: [] };
        const surveyData = ipasDataObj[surveyType] || [];

        // Calculate Summary
        let prelist = 0, draft = 0, openVal = 0, submitted = 0, today = 0, yesterday = 0, newToday = 0;

        surveyData.forEach(item => {
            prelist += item.total_prelist || 0;
            draft += item.total_draft || 0;
            openVal += item.total_open || 0;
            submitted += item.total_submitted || 0;
            today += item.today_completed || 0;
            yesterday += item.yesterday_completed || 0;
            newToday += item.new_usaha_today || 0;
        });

        // Override prelist with PROVINSI_TOTAL if available
        const provTotalKey = surveyType + "_prov_total";
        if (ipasDataObj[provTotalKey]) {
            prelist = ipasDataObj[provTotalKey];
        }

        const persentase = prelist > 0 ? ((submitted / prelist) * 100).toFixed(2) : '0.00';
        const sisa = prelist - submitted;

        // Format helper
        const formatNum = (num) => new Intl.NumberFormat('id-ID').format(num || 0);

        // Update stats elements
        document.getElementById(`${surveyType}-stat-total-prelist`).textContent = formatNum(prelist);
        document.getElementById(`${surveyType}-stat-new-today`).textContent = `+${formatNum(newToday)}`;
        document.getElementById(`${surveyType}-stat-draft`).textContent = formatNum(draft);
        document.getElementById(`${surveyType}-stat-open`).textContent = formatNum(openVal);
        document.getElementById(`${surveyType}-stat-submitted`).textContent = formatNum(submitted);
        document.getElementById(`${surveyType}-stat-percentage`).textContent = persentase + '%';

        // Kenaikan Persentase
        const pctToday = prelist > 0 ? ((today / prelist) * 100).toFixed(2) : '0.00';
        const pctYesterday = prelist > 0 ? ((yesterday / prelist) * 100).toFixed(2) : '0.00';
        const kenaikanEl = document.getElementById(`${surveyType}-stat-kenaikan`);
        if (kenaikanEl) {
            kenaikanEl.innerHTML = `<span style="color: var(--color-delivered);">+${pctToday}% hari ini</span> <span style="color: var(--card-border);">|</span> <span style="color: #f59e0b;">+${pctYesterday}% kemarin</span>`;
        }

        const progressBar = document.getElementById(`${surveyType}-progress-bar`);
        if (progressBar) {
            progressBar.style.width = persentase + '%';
        }

        document.getElementById(`${surveyType}-stat-sisa-usaha`).textContent = formatNum(sisa);
        document.getElementById(`${surveyType}-stat-today-completed`).textContent = formatNum(today);

        const vsYesterdayWrapper = document.getElementById(`${surveyType}-stat-vs-yesterday-wrapper`);
        if (vsYesterdayWrapper) {
            if (today >= yesterday) {
                vsYesterdayWrapper.innerHTML = `<span style="color: var(--color-delivered); background-color: rgba(16, 185, 129, 0.1); padding: 0.15rem 0.45rem; border-radius: 0.5rem; font-weight: 700; font-size: 0.75rem;">▲ vs ${formatNum(yesterday)} kemarin</span>`;
            } else {
                vsYesterdayWrapper.innerHTML = `<span style="color: var(--color-bounced); background-color: rgba(239, 68, 68, 0.1); padding: 0.15rem 0.45rem; border-radius: 0.5rem; font-weight: 700; font-size: 0.75rem;">▼ vs ${formatNum(yesterday)} kemarin</span>`;
            }
        }
        // Render Table with Filtering & Sorting
        const searchVal = (document.getElementById(`${surveyType}-search-input`).value || '').toLowerCase().trim();
        const tbody = document.getElementById(`${surveyType}-table-body`);
        tbody.innerHTML = '';

        const filtered = surveyData.filter(item => {
            return item.kabupaten.toLowerCase().includes(searchVal);
        });

        // Render dynamic sorting headers
        window.renderSeTableHeaders(surveyType);

        if (filtered.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="10" style="text-align: center; padding: 3rem 1rem; color: var(--text-secondary);">
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
                case 'new_usaha_today':
                    valA = a.new_usaha_today || 0;
                    valB = b.new_usaha_today || 0;
                    break;
                default:
                    return 0;
            }
            return sortSettings.order === 'asc' ? valA - valB : valB - valA;
        });

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

            const kabupatenEscaped = item.kabupaten.replace(/'/g, "\\'");
            const newBusinessesJSON = JSON.stringify(item.new_businesses || []).replace(/"/g, '&quot;');

            const penambahanBadge = (item.new_usaha_today > 0 || item.new_usaha_yesterday > 0)
                ? `<span class="badge-interactive" onclick="openNewBusinessesModal('${kabupatenEscaped}', '${newBusinessesJSON}')" style="cursor: pointer; display: inline-block; padding: 0.25rem 0.5rem; border-radius: 0.5rem; font-size: 0.75rem; font-weight: 800; background-color: rgba(99, 102, 241, 0.1); color: var(--primary); border: 1px solid rgba(99, 102, 241, 0.3); transition: all 0.2s;" title="Klik untuk rincian target baru">
                    +${item.new_usaha_today} | +${item.new_usaha_yesterday}
                   </span>`
                : `<span style="color: var(--text-muted); font-size: 0.85rem;">-</span>`;

            row.innerHTML = `
                <td style="font-weight: 700; color: var(--text-primary);">${highlightText(item.kabupaten, searchVal)}</td>
                <td style="text-align: right; font-family: monospace; font-weight: 500; color: #f59e0b;">${formatNum(item.total_draft)}</td>
                <td style="text-align: right; font-family: monospace; font-weight: 500; color: #3b82f6;">${formatNum(item.total_open)}</td>
                
                <td style="text-align: right; font-family: monospace; font-weight: 700; color: var(--color-delivered);">${formatNum(item.total_submitted)}</td>
                <td style="text-align: right; font-family: monospace; font-weight: 600; color: var(--color-opened);">${formatNum(item.today_completed)}</td>
                <td style="text-align: right; font-family: monospace; font-weight: 600; color: #f59e0b;">${formatNum(item.yesterday_completed)}</td>
                <td style="text-align: right; font-family: monospace; font-weight: 600; color: var(--color-clicked);">${formatNum(item.two_days_ago_completed)}</td>
                
                <td style="text-align: center;">
                    <span style="display: inline-block; padding: 0.25rem 0.5rem; border-radius: 0.5rem; font-size: 0.75rem; font-weight: 800; ${pctClass}">
                        ${item.persentase}%
                    </span>
                </td>
                <td style="text-align: right; font-family: monospace; font-weight: 500; color: var(--text-secondary);">${formatNum(item.total_prelist)}</td>
                <td style="text-align: center;">
                    ${penambahanBadge}
                </td>
            `;
            tbody.appendChild(row);
        });

        // Render Chart
        if (!window.currentChartType) window.currentChartType = { se_umum: 'bar', se_ub: 'bar' };

        window.toggleChartType = function (type) {
            window.currentChartType[type] = window.currentChartType[type] === 'line' ? 'bar' : 'line';
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

            if (cType === 'line') {
                const cumToday = submitted;
                const cumYesterday = submitted - today;
                const cum2DaysAgo = submitted - today - yesterday;

                chartData = {
                    labels: ['H-2', 'Kemarin', 'Hari Ini'],
                    datasets: [{
                        label: 'Total Capaian Selesai (Kumulatif)',
                        data: [cum2DaysAgo, cumYesterday, cumToday],
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.2)',
                        borderWidth: 3,
                        pointBackgroundColor: '#0b1120',
                        pointBorderColor: '#3b82f6',
                        pointBorderWidth: 2,
                        pointRadius: 6,
                        pointHoverRadius: 8,
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
                // Bar Chart Per Kabupaten (Stacked)
                const sortedForBar = [...surveyData].sort((a, b) => b.total_prelist - a.total_prelist);
                chartData = {
                    labels: sortedForBar.map(i => i.kabupaten.replace(/\[\d+\] /g, '')),
                    datasets: [
                        {
                            label: 'Submitted (Selesai)',
                            data: sortedForBar.map(i => i.total_submitted || 0),
                            backgroundColor: 'rgba(16, 185, 129, 0.85)', // Green
                            borderRadius: 4
                        },
                        {
                            label: 'Sisa Usaha (Belum Selesai)',
                            data: sortedForBar.map(i => i.sisa_usaha || 0),
                            backgroundColor: 'rgba(239, 68, 68, 0.85)', // Red
                            borderRadius: 4
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
                type: cType,
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
            tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; padding: 2rem; color: var(--text-secondary);">Data alokasi belum tersedia. Silakan jalankan scrape_assign.py terlebih dahulu.</td></tr>`;
            return;
        }

        const fmt = (n) => new Intl.NumberFormat('id-ID').format(n || 0);
        const rowStyle = 'border-bottom: 1px solid var(--card-border); transition: background-color 0.15s;';
        const tdBase = 'padding: 0.65rem 1.25rem; vertical-align: middle;';

        let totalUsaha = 0;
        let totalSudah = 0;
        let totalBelum = 0;

        const rowsHtml = window.ASSIGN_DATA.map((d, idx) => {
            const total = d.total || 0;
            const assigned = d.assigned || 0;
            const unassigned = d.have_not_assigned || 0;

            totalUsaha += total;
            totalSudah += assigned;
            totalBelum += unassigned;

            const pct = total > 0 ? ((assigned / total) * 100) : 0;
            const pctText = pct.toFixed(2);

            let pctBgColor = '#047857'; // Green (high)
            if (pct < 50) {
                pctBgColor = '#b91c1c'; // Red (low)
            } else if (pct < 80) {
                pctBgColor = '#b45309'; // Orange (mid)
            }

            // Parse name from "[01] BANGGAI KEPULAUAN" -> "BANGGAI KEPULAUAN"
            const namaKabClean = d.nama_kab.replace(/\[\d+\]\s*/, '').trim().toUpperCase();
            const bgColor = idx % 2 === 0 ? '' : 'background-color: rgba(99,102,241,0.03);';

            return `
            <tr style="${rowStyle} ${bgColor}">
                <td style="${tdBase} text-align: center; color: var(--text-secondary); font-weight: 500;">${idx + 1}</td>
                <td style="${tdBase} text-align: center; font-family: monospace; font-size: 0.85rem; color: var(--text-secondary);">${d.kode_kab}</td>
                <td style="${tdBase} font-weight: 600; color: var(--text);">${namaKabClean}</td>
                <td style="${tdBase} text-align: right; font-family: monospace; font-weight: 600; color: var(--text-secondary);">${fmt(total)}</td>
                <td style="${tdBase} text-align: right; font-family: monospace; font-weight: 600; color: #10b981;">${fmt(assigned)}</td>
                <td style="${tdBase} text-align: right; font-family: monospace; font-weight: 600; color: #ef4444;">${fmt(unassigned)}</td>
                <td style="${tdBase} text-align: center; background-color: ${pctBgColor}; color: white; font-weight: 700; font-family: monospace;">${pctText}</td>
            </tr>`;
        }).join('');

        const totalPct = totalUsaha > 0 ? ((totalSudah / totalUsaha) * 100) : 0;
        let totalPctBgColor = '#047857';
        if (totalPct < 50) {
            totalPctBgColor = '#b91c1c';
        } else if (totalPct < 80) {
            totalPctBgColor = '#b45309';
        }

        tbody.innerHTML = rowsHtml + `
        <tr style="border-top: 2px solid var(--card-border); background-color: var(--card-bg); font-weight: 800;">
            <td style="${tdBase} text-align: center; color: var(--text);"></td>
            <td style="${tdBase} text-align: center; color: var(--text);"></td>
            <td style="${tdBase} color: var(--text);">TOTAL</td>
            <td style="${tdBase} text-align: right; font-family: monospace; color: var(--text-secondary);">${fmt(totalUsaha)}</td>
            <td style="${tdBase} text-align: right; font-family: monospace; color: #10b981;">${fmt(totalSudah)}</td>
            <td style="${tdBase} text-align: right; font-family: monospace; color: #ef4444;">${fmt(totalBelum)}</td>
            <td style="${tdBase} text-align: center; background-color: ${totalPctBgColor}; color: white; font-weight: 800; font-family: monospace;">${totalPct.toFixed(2)}</td>
        </tr>`;
    }

    let assignChartInstance = null;
    let progressGaugeInstance = null;

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

        const labels = window.ASSIGN_DATA.map(d => d.nama_kab.replace(/\[\d+\] /, ''));
        const assignedData = window.ASSIGN_DATA.map(d => d.assigned);
        const notAssignedData = window.ASSIGN_DATA.map(d => d.have_not_assigned);

        const textColor = getThemeColor('--text-secondary', '#9ca3af');
        const gridColor = getThemeColor('--card-border', 'rgba(255, 255, 255, 0.08)');
        assignChartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Sudah Ditugaskan',
                        data: assignedData,
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

        // Update Speedometer Gauge Chart
        const ctxGauge = document.getElementById('progressGaugeChart');
        if (ctxGauge) {
            if (progressGaugeInstance) {
                progressGaugeInstance.destroy();
            }

            let totalAssigned = 0;
            let totalTargets = 0;
            window.ASSIGN_DATA.forEach(d => {
                totalAssigned += (d.assigned || 0);
                totalTargets += (d.total || 0);
            });

            const pct = totalTargets > 0 ? (totalAssigned / totalTargets) * 100 : 0;

            const pctCenter = document.getElementById('gauge-percent-center');
            if (pctCenter) pctCenter.innerText = pct.toFixed(2) + '%';

            const statsDetails = document.getElementById('gauge-stats-details');
            if (statsDetails) {
                statsDetails.innerHTML = `<span style="font-weight: 700; color: var(--text-primary); font-size: 1.15rem; display: block; margin-bottom: 0.25rem;">${new Intl.NumberFormat('id-ID').format(totalAssigned)}</span> dari ${new Intl.NumberFormat('id-ID').format(totalTargets)} target usaha telah ditugaskan`;
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
    }

    // SLS state
    window.slsSort = { column: 'kab_name', order: 'asc' };
    window.slsCurrentPage = 1;
    const SLS_ITEMS_PER_PAGE = 25;

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
            return;
        }

        desaSelect.disabled = false;
        const filteredSls = window.ASSIGN_SLS_DATA.filter(i => i.kab_name === kabVal && i.kec_name === kecVal);
        const uniqueDesas = [...new Set(filteredSls.map(i => i.desa_name))].sort();

        desaSelect.innerHTML = '<option value="all">Semua Desa</option>' +
            uniqueDesas.map(d => `<option value="${d}">${d}</option>`).join('');
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
            <th style="font-family: 'Outfit', sans-serif; user-select: none;">Status & Petugas</th>
        `;
    }

    function renderSlsTable() {
        const tbody = document.getElementById('sls-table-body');
        if (!tbody) return;

        if (!window.ASSIGN_SLS_DATA || window.ASSIGN_SLS_DATA.length === 0) {
            tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; padding: 2rem; color: var(--text-secondary);">Data SLS belum tersedia. Pastikan sinkronisasi data sedang berjalan.</td></tr>`;
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
        const assignmentFilter = document.getElementById('sls-assignment-filter')?.value || 'all';

        // 2. Filter logic
        const filtered = window.ASSIGN_SLS_DATA.filter(item => {
            // Region cascading filters
            if (kabFilter !== 'all' && item.kab_name !== kabFilter) return false;
            if (kecFilter !== 'all' && item.kec_name !== kecFilter) return false;
            if (desaFilter !== 'all' && item.desa_name !== desaFilter) return false;

            // Assignment status filter
            if (assignmentFilter === 'fully_assigned' && item.unassigned !== 0) return false;
            if (assignmentFilter === 'partially_assigned' && !(item.assigned > 0 && item.unassigned > 0)) return false;
            if (assignmentFilter === 'unassigned' && item.assigned !== 0) return false;

            // Search val
            if (searchVal) {
                const matchText = (item.sls_code + ' ' + item.sls_name + ' ' + item.desa_name + ' ' + item.kec_name + ' ' + item.kab_name + ' ' + (item.officers || []).join(' ')).toLowerCase();
                if (!matchText.includes(searchVal)) return false;
            }

            return true;
        });

        // 3. Render statistics for the region-filtered or active set of data
        const statsBase = window.ASSIGN_SLS_DATA.filter(item => {
            if (kabFilter !== 'all' && item.kab_name !== kabFilter) return false;
            if (kecFilter !== 'all' && item.kec_name !== kecFilter) return false;
            if (desaFilter !== 'all' && item.desa_name !== desaFilter) return false;
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
            let valA = a[col];
            let valB = b[col];
            if (typeof valA === 'string') {
                return valA.localeCompare(valB) * order;
            }
            return ((valA || 0) - (valB || 0)) * order;
        });

        // Update headers (shows active sort icon)
        renderSlsTableHeaders();

        if (filtered.length === 0) {
            tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; padding: 3rem 1rem; color: var(--text-secondary);">Tidak ada data SLS yang cocok dengan filter pencarian.</td></tr>`;
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
    window.openNewBusinessesModal = function (kabupatenName, businessesJSON) {
        const modal = document.getElementById('businesses-modal');
        const titleText = document.getElementById('modal-title-text');
        const searchInput = document.getElementById('modal-search-input');
        if (!modal || !titleText || !searchInput) return;

        // Clean name
        const cleanKab = kabupatenName.replace(/\[\d+\]\s*/, '').trim().toUpperCase();
        titleText.innerText = `Penambahan Usaha: KAB. ${cleanKab}`;
        searchInput.value = '';

        try {
            activeModalBusinesses = typeof businessesJSON === 'string' ? JSON.parse(businessesJSON) : businessesJSON;
        } catch (e) {
            activeModalBusinesses = [];
        }

        renderModalList();
        modal.classList.add('active');
    };

    window.openProvincialNewBusinessesModal = function (surveyType) {
        const modal = document.getElementById('businesses-modal');
        const titleText = document.getElementById('modal-title-text');
        const searchInput = document.getElementById('modal-search-input');
        if (!modal || !titleText || !searchInput) return;

        titleText.innerText = `Penambahan Usaha: PROVINSI SULAWESI TENGAH (${surveyType === 'se_umum' ? 'Umum' : 'Usaha Besar'})`;
        searchInput.value = '';

        const ipasDataObj = window.IPAS_DATA || { se_umum: [], se_ub: [] };
        const surveyData = ipasDataObj[surveyType] || [];

        activeModalBusinesses = [];
        surveyData.forEach(kab => {
            const cleanKab = kab.kabupaten.replace(/\[\d+\]\s*/, '').trim().toUpperCase();
            const list = kab.new_businesses || [];
            list.forEach(b => {
                activeModalBusinesses.push({
                    ...b,
                    kabName: cleanKab
                });
            });
        });

        renderModalList();
        modal.classList.add('active');
    };

    window.closeNewBusinessesModal = function () {
        const modal = document.getElementById('businesses-modal');
        if (modal) modal.classList.remove('active');
    };

    window.renderModalList = function () {
        const container = document.getElementById('modal-business-list');
        const searchInput = document.getElementById('modal-search-input');
        if (!container || !searchInput) return;

        const q = searchInput.value.toLowerCase().trim();
        const filtered = activeModalBusinesses.filter(b => {
            return (b.name || '').toLowerCase().includes(q) || (b.code || '').toLowerCase().includes(q);
        });

        if (filtered.length === 0) {
            container.innerHTML = `<div style="text-align: center; padding: 3rem 1rem; color: var(--text-secondary); font-size: 0.9rem;">Tidak ada penambahan usaha baru yang ditemukan.</div>`;
            return;
        }

        container.innerHTML = filtered.map(b => {
            const badgeColor = b.date === 'today' ? 'var(--color-delivered)' : '#f59e0b';
            const badgeText = b.date === 'today' ? 'Hari Ini' : 'Kemarin';
            const kabSub = b.kabName ? `<span style="font-size: 0.75rem; color: var(--text-secondary); background: rgba(255,255,255,0.05); padding: 0.15rem 0.45rem; border-radius: 0.25rem; margin-right: 0.5rem;">${b.kabName}</span>` : '';

            return `
                <div class="business-list-item">
                    <div class="business-info">
                        <span class="business-name">${b.name}</span>
                        <span class="business-code">${b.code}</span>
                    </div>
                    <div class="business-badges">
                        ${kabSub}
                        <span style="background: rgba(255,255,255,0.05); padding: 0.25rem 0.5rem; border-radius: 0.5rem; font-size: 0.7rem; font-weight: 700; color: var(--text-secondary); text-transform: uppercase; border: 1px solid var(--card-border);">${b.status || 'DRAFT'}</span>
                        <span style="background: rgba(${b.date === 'today' ? '16,185,129,0.1' : '245,158,11,0.1'}); border: 1px solid rgba(${b.date === 'today' ? '16,185,129,0.3' : '245,158,11,0.3'}); padding: 0.25rem 0.5rem; border-radius: 0.5rem; font-size: 0.7rem; font-weight: 700; color: ${badgeColor};">${badgeText}</span>
                    </div>
                </div>
            `;
        }).join('');
    };

    window.filterModalList = function () {
        renderModalList();
    };

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
            if (mainHeader) mainHeader.textContent = 'Dashboard Sensus Ekonomi Umum';
            if (mainSubheader) mainSubheader.textContent = 'Rekapitulasi progres pendataan Sensus Ekonomi 2026 untuk kategori Usaha Umum';
            if (btnDownloadXlsx) btnDownloadXlsx.style.display = 'none';
            if (btnDownloadBackupCsv) btnDownloadBackupCsv.style.display = 'none';
            renderSeDashboard('se_umum');
        } else if (tabId === 'se_ub') {
            if (mainHeader) mainHeader.textContent = 'Dashboard Sensus Ekonomi Usaha Besar';
            if (mainSubheader) mainSubheader.textContent = 'Rekapitulasi progres pendataan Sensus Ekonomi 2026 untuk kategori Usaha Besar (UB)';
            if (btnDownloadXlsx) btnDownloadXlsx.style.display = 'none';
            if (btnDownloadBackupCsv) btnDownloadBackupCsv.style.display = 'none';
            renderSeDashboard('se_ub');
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
                    const { data, error } = await supabaseClient
                        .from('email_logs')
                        .select('*')
                        .range(fromOffset, fromOffset + limitVal - 1);

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

        // Dynamically reload IPAS ipas_data.js
        await new Promise((resolve) => {
            const script = document.createElement('script');
            script.src = 'ipas_data.js?v=' + Date.now();
            script.onload = () => resolve();
            script.onerror = () => resolve();
            document.head.appendChild(script);
        });

        // Dynamically reload assign_data.js
        await new Promise((resolve) => {
            const script = document.createElement('script');
            script.src = 'assign_data.js?v=' + Date.now();
            script.onload = () => resolve();
            script.onerror = () => resolve();
            document.head.appendChild(script);
        });

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

        if (activeTab === 'assign') {
            const activeSubtab = localStorage.getItem('active_assign_subtab') || 'se2026';
            if (typeof filterAssignData === 'function') {
                filterAssignData(activeSubtab);
            } else {
                renderAssignChart();
                renderSlsTable();
            }
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

    // Initial Execution
    fetchDataAndRender().then(() => {
        // Restore active tab from localStorage, default to 'se_umum'
        const activeTab = localStorage.getItem('active_tab') || 'se_umum';
        window.switchTab(activeTab);
    });
});