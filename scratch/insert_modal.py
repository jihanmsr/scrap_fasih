import re

with open("index.html", "r") as f:
    content = f.read()

modal_html = """
    <!-- ====== MODAL RANKING ====== -->
    <div id="ranking-modal" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.55); z-index:9999; align-items:center; justify-content:center; backdrop-filter:blur(4px);">
        <div style="background:var(--card-bg); width:90%; max-width:500px; border-radius:1rem; box-shadow:0 20px 25px -5px rgba(0,0,0,0.1), 0 10px 10px -5px rgba(0,0,0,0.04); overflow:hidden; border:1px solid var(--card-border); display:flex; flex-direction:column; max-height:85vh;">
            <div style="padding:1.25rem 1.5rem; border-bottom:1px solid var(--card-border); display:flex; justify-content:space-between; align-items:center; background:rgba(249, 115, 22, 0.05);">
                <div>
                    <h3 id="ranking-modal-title" style="margin:0;font-size:1.15rem;font-weight:800;color:var(--text-primary);display:flex;align-items:center;gap:0.5rem;">
                        🏆 Ranking Kabupaten/Kota
                    </h3>
                </div>
                <button onclick="document.getElementById('ranking-modal').style.display='none'" style="background:none;border:none;cursor:pointer;color:var(--text-secondary);padding:0.25rem;border-radius:0.5rem;line-height:1;">
                    <svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6L6 18M6 6l12 12"/></svg>
                </button>
            </div>
            <div id="ranking-modal-body" style="padding:1rem 1.5rem; overflow-y:auto; flex:1; display:flex; flex-direction:column; gap:0.5rem;">
                <!-- Content goes here -->
            </div>
            <div style="padding:1rem 1.5rem; border-top:1px solid var(--card-border); background:var(--bg-body); display:flex; justify-content:flex-end;">
                <button onclick="document.getElementById('ranking-modal').style.display='none'" style="padding:0.6rem 1.25rem;border-radius:0.75rem;border:1px solid var(--card-border);background:transparent;color:var(--text-secondary);font-size:0.85rem;font-weight:600;cursor:pointer;font-family:Outfit,sans-serif;">Tutup</button>
            </div>
        </div>
    </div>
"""

content = content.replace("<!-- ====== MODAL DOWNLOAD EXCEL PETUGAS ====== -->", modal_html + "\n    <!-- ====== MODAL DOWNLOAD EXCEL PETUGAS ====== -->")

# Also restore max-height for se_umum-ranking-list and se_ub-ranking-list
content = content.replace("max-height: none;", "max-height: 165px;")

with open("index.html", "w") as f:
    f.write(content)
