import re

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Change Tab Name
html = html.replace('Rekonsiliasi Data Lintas Sistem', 'Rekap Lintas Sistem')
html = html.replace('id="tab-btn-rekon" onclick="switchTab(\'rekon\')" title="Rekap Lintas Sistem">\n                    <svg', 'id="tab-btn-rekon" onclick="switchTab(\'rekon\')" title="Rekap Lintas Sistem">\n                    <svg')
html = html.replace('Rekonsiliasi\n                </button>', 'Perbandingan\n                </button>')
html = html.replace('<h2>Rekonsiliasi Lintas Sistem', '<h2>Perbandingan Lintas Sistem')

# Add Filters
filters_html = """
        <!-- FILTERS -->
        <div class="filters-container" style="display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 1rem;">
            <input type="text" id="rekon-filter-search" placeholder="Cari nama/email/SLS..." class="search-input" style="flex: 1; min-width: 150px;" oninput="renderRekon()">
            <select id="rekon-filter-kab" class="filter-select" onchange="updateKec(); renderRekon()"><option value="">Semua Kab</option></select>
            <select id="rekon-filter-kec" class="filter-select" onchange="updateDesa(); renderRekon()"><option value="">Semua Kec</option></select>
            <select id="rekon-filter-desa" class="filter-select" onchange="updateSls(); renderRekon()"><option value="">Semua Desa</option></select>
            <select id="rekon-filter-sls" class="filter-select" onchange="renderRekon()"><option value="">Semua SLS</option></select>
            <select id="rekon-filter-petugas" class="filter-select" onchange="renderRekon()" style="display:none;"><option value="">Semua Petugas</option></select>
        </div>
"""

# Find the old filter block and replace it
import re
html = re.sub(r'<!-- FILTERS -->.*?<!-- TABEL SLS -->', filters_html + '\n        <!-- TABEL SLS -->', html, flags=re.DOTALL)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)
