with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Add JS script tags
html = html.replace('<script src="daily_summary.js?v=20260723_v1"></script>', 
                    '<script src="daily_summary.js?v=20260723_v1"></script>\n    <script src="rekon_data.js"></script>\n    <script src="rekon.js"></script>')

# 2. Add Tab Button
tab_button = """                <button class="btn-tab" id="tab-btn-rekon" onclick="switchTab('rekon')" title="Rekap Lintas Sistem">
                    <svg fill="none" height="18" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"
                        stroke-width="2.5" style="margin-right: 0.75rem;" viewbox="0 0 24 24" width="18">
                        <path d="M4 4v16h16"></path>
                        <path d="M4 12h16"></path>
                        <path d="M12 4v16"></path>
                    </svg>
                    Perbandingan
                </button>
"""
html = html.replace('<!-- <button class="btn-tab" id="tab-btn-timeline"', tab_button + '\n                <!-- <button class="btn-tab" id="tab-btn-timeline"')

# 3. Add Tab Content
tab_content = """
    <!-- TAB REKONSILIASI -->
    <div class="tab-content" id="tab-content-rekon" style="display: none; padding: 1rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
            <h2>Perbandingan Lintas Sistem (Muatan vs Fasih vs SQL Lab)</h2>
        </div>

        <!-- SUMMARY CARDS -->
        <div class="summary-cards" id="rekon-summary" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 1.5rem;">
            <!-- Diisi via JS -->
        </div>

        <!-- SUB TAB NAVIGATION -->
        <div class="sub-tabs-container">
            <button class="btn-sub-tab active" id="rekon-sub-btn-sls" onclick="switchRekonSubTab('sls')">
                Level SLS
            </button>
            <button class="btn-sub-tab" id="rekon-sub-btn-petugas" onclick="switchRekonSubTab('petugas')">
                Level Petugas
            </button>
        </div>

        <!-- FILTERS -->
        <div class="filters-container" style="display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 1rem;">
            <input type="text" id="rekon-filter-search" placeholder="Cari nama/email/SLS..." class="search-input" style="flex: 1; min-width: 150px;" oninput="renderRekon()">
            <select id="rekon-filter-kab" class="filter-select" onchange="updateKec(); renderRekon()"><option value="">Semua Kab</option></select>
            <select id="rekon-filter-kec" class="filter-select" onchange="updateDesa(); renderRekon()"><option value="">Semua Kec</option></select>
            <select id="rekon-filter-desa" class="filter-select" onchange="updateSls(); renderRekon()"><option value="">Semua Desa</option></select>
            <select id="rekon-filter-sls" class="filter-select" onchange="renderRekon()"><option value="">Semua SLS</option></select>
            <select id="rekon-filter-petugas" class="filter-select" onchange="renderRekon()" style="display:none;"><option value="">Semua Petugas</option></select>
        </div>

        <!-- TABEL SLS -->
        <div id="rekon-sub-sls" class="ipas-table-wrapper" style="max-height: 600px; overflow-y: auto;">
            <table class="ipas-table">
                <thead>
                    <tr>
                        <th class="sortable" onclick="sortRekon('sls', 'sls_id')">ID SLS</th>
                        <th class="sortable" onclick="sortRekon('sls', 'nmkab')">Kab/Kec/Desa</th>
                        <th class="sortable" onclick="sortRekon('sls', 'total_muatan')">Total Muatan (UTP+SBR+Kel)</th>
                        <th class="sortable" onclick="sortRekon('sls', 'fasih_target_pencacah')">Target Fasih (Pencacah)</th>
                        <th class="sortable" onclick="sortRekon('sls', 'diff_fasih_vs_muatan_total')">Selisih (Fasih - Muatan)</th>
                    </tr>
                </thead>
                <tbody id="rekon-table-sls"></tbody>
            </table>
        </div>

        <!-- TABEL PETUGAS -->
        <div id="rekon-sub-petugas" class="ipas-table-wrapper" style="display: none; max-height: 600px; overflow-y: auto;">
            <table class="ipas-table">
                <thead>
                    <tr>
                        <th class="sortable" onclick="sortRekon('petugas', 'email')">Email Petugas</th>
                        <th class="sortable" onclick="sortRekon('petugas', 'total_muatan_assigned')">Beban Muatan (Assign)</th>
                        <th class="sortable" onclick="sortRekon('petugas', 'total_fasih')">Target Fasih</th>
                        <th class="sortable" onclick="sortRekon('petugas', 'total_sqllab')">Target SQL Lab</th>
                        <th class="sortable" onclick="sortRekon('petugas', 'diff_fasih_vs_muatan')">Fasih vs Muatan</th>
                        <th class="sortable" onclick="sortRekon('petugas', 'diff_fasih_vs_sqllab')">Fasih vs SQL Lab</th>
                    </tr>
                </thead>
                <tbody id="rekon-table-petugas"></tbody>
            </table>
        </div>
    </div>
"""

# Inject right before the closing </main> or inside main-content at the end
# The best place is after the last tab-content, let's find '<div class="tab-content" id="tab-content-anomali"'
# and inject after its closing div. It's safer to just inject right before `<div id="excel-download-modal"` which is at the end of the body
html = html.replace('<div id="excel-download-modal"', tab_content + '\n        <div id="excel-download-modal"')

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)
