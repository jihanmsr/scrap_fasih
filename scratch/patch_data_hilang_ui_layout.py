import re

with open('/Users/jihanmaisaroh/scrap_fasih/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# We need to find the section between `<div id="data_hilang-data-section"` and `<div id="data_hilang-loading"`
pattern = re.compile(r'(<div id="data_hilang-data-section" style="display: none;">)(.*?)(<!-- Loading -->)', re.DOTALL)

replacement = r"""\1
                    <!-- Top Bar -->
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1.5rem; gap: 0.75rem; flex-wrap: wrap;">
                        <div>
                            <div style="font-weight: 700; color: var(--text-primary); font-size: 1.05rem;">Halo, <span id="data_hilang-user-name" style="color: var(--primary);"></span> <span id="data_hilang-user-kab" style="font-size: 0.8rem; color: var(--text-secondary); font-weight: 400;"></span></div>
                            <div id="main-subheader" style="font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.3rem;">Usahanya tidak ditemukan tapi bisa dilacak keluarganya</div>
                        </div>
                        <div style="display: flex; align-items: center; gap: 0.6rem; flex-wrap: wrap;">
                            <button onclick="logoutDataHilang()" style="padding: 0.5rem 1.2rem; background: #f1f5f9; color: #475569; border: none; border-radius: 0.5rem; cursor: pointer; font-weight: 600; font-family: 'Plus Jakarta Sans', sans-serif; font-size: 0.85rem;">Logout</button>
                        </div>
                    </div>

                    <!-- Toggle Usaha vs Keluarga -->
                    <div id="data_hilang-tab-switcher" style="display: flex; gap: 0.5rem; margin-bottom: 1rem; border-bottom: 1px solid var(--card-border); padding-bottom: 0.5rem;">
                        <button id="btn-data-hilang-usaha" onclick="window.switchDataHilangSubTab('usaha')" style="padding: 0.6rem 1.5rem; border-radius: 0.5rem; border: none; background: var(--primary); color: white; font-weight: 700; cursor: pointer; transition: all 0.2s; font-family: 'Plus Jakarta Sans', sans-serif;">Usaha Hilang</button>
                        <button id="btn-data-hilang-keluarga" onclick="window.switchDataHilangSubTab('keluarga')" style="padding: 0.6rem 1.5rem; border-radius: 0.5rem; border: none; background: transparent; color: var(--text-secondary); font-weight: 600; cursor: pointer; transition: all 0.2s; font-family: 'Plus Jakarta Sans', sans-serif;">Keluarga Hilang</button>
                    </div>

                    <!-- Statistics & Filter bar -->
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; flex-wrap: wrap; gap: 1rem;">
                        <div style="display: flex; align-items: center; gap: 0.75rem;">
                            <div style="background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 0.75rem; padding: 0.5rem 1rem; display: flex; align-items: center; gap: 0.75rem;">
                                <div style="font-size: 0.7rem; color: var(--text-secondary); font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em;">Total Data:</div>
                                <div style="font-size: 1.4rem; font-weight: 800; color: var(--text-primary); font-family: 'Outfit', sans-serif; line-height: 1;" id="data_hilang-count-total">-</div>
                            </div>
                        </div>

                        <div style="display: flex; gap: 0.5rem; flex-wrap: wrap; align-items: center; background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 0.75rem; padding: 0.5rem 0.75rem; box-shadow: var(--shadow-sm);">
                            <svg width="14" height="14" fill="none" stroke="var(--text-secondary)" stroke-width="2.5" viewBox="0 0 24 24" style="flex-shrink:0;">
                                <circle cx="11" cy="11" r="8" />
                                <path d="M21 21l-4.35-4.35" />
                            </svg>
                            <input type="text" id="data_hilang-search" placeholder="Cari nama / NIK / wilayah..." oninput="window.filterDataHilangTable()" style="flex: 1; min-width: 180px; padding: 0.3rem 0.4rem; border: none; background: transparent; color: var(--text-primary); font-family: 'Plus Jakarta Sans', sans-serif; font-size: 0.85rem; outline: none;">
                            <div style="width: 1px; height: 20px; background: var(--card-border);"></div>
                            <select id="data_hilang-filter-kab" onchange="window.filterDataHilangTable()" style="padding: 0.3rem 0.5rem; border: none; border-radius: 0.4rem; background: var(--input-bg); color: var(--text-primary); font-family: 'Plus Jakarta Sans', sans-serif; font-size: 0.85rem; outline: none; cursor: pointer; font-weight: 600;">
                                <option value="">Semua Kab/Kota</option>
                            </select>
                        </div>
                    </div>

                    \3"""

new_html = pattern.sub(replacement, html)

with open('/Users/jihanmaisaroh/scrap_fasih/index.html', 'w', encoding='utf-8') as f:
    f.write(new_html)

print("index.html layout patched")
