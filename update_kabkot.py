import re

with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Change Level Kab/Kota to Rekap Kab/Kota
content = content.replace("Level Kab/Kota", "Rekap Kab/Kota")

# Change colspan="3" to colspan="4" in the kabkot table header
target_block_regex = r'(<div id="rekon-sub-kabkot".*?)(<div id="rekon-sub-petugas")'
match = re.search(target_block_regex, content, re.DOTALL)
if match:
    kabkot_html = match.group(1)
    
    # Change colspans
    kabkot_html = kabkot_html.replace('colspan="3"', 'colspan="4"')
    
    # Insert new headers
    kabkot_html = kabkot_html.replace('<th class="sortable" onclick="sortRekon(\'kabkot\', \'diff_utp\')" style="text-align:right;">Selisih</th>', '<th class="sortable" onclick="sortRekon(\'kabkot\', \'diff_utp\')" style="text-align:right;">Selisih</th>\n                                <th class="sortable" onclick="sortRekon(\'kabkot\', \'pct_utp\')" style="text-align:right;">% Capaian</th>')
    kabkot_html = kabkot_html.replace('<th class="sortable" onclick="sortRekon(\'kabkot\', \'diff_sbr\')" style="text-align:right;">Selisih</th>', '<th class="sortable" onclick="sortRekon(\'kabkot\', \'diff_sbr\')" style="text-align:right;">Selisih</th>\n                                <th class="sortable" onclick="sortRekon(\'kabkot\', \'pct_sbr\')" style="text-align:right;">% Capaian</th>')
    kabkot_html = kabkot_html.replace('<th class="sortable" onclick="sortRekon(\'kabkot\', \'diff_keluarga\')" style="text-align:right;">Selisih</th>', '<th class="sortable" onclick="sortRekon(\'kabkot\', \'diff_keluarga\')" style="text-align:right;">Selisih</th>\n                                <th class="sortable" onclick="sortRekon(\'kabkot\', \'pct_keluarga\')" style="text-align:right;">% Capaian</th>')
    
    content = content[:match.start()] + kabkot_html + match.group(2) + content[match.end():]

# Cache buster
import time
new_v = 'v=' + str(int(time.time()))
content = re.sub(r'v=\d+', new_v, content)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)


with open('rekon.js', 'r', encoding='utf-8') as f:
    js_content = f.read()

# Add sorting for pct
js_content = js_content.replace("else if (sortKey === 'diff_utp') { valA = a.r_utp - a.m_utp; valB = b.r_utp - b.m_utp; }", "else if (sortKey === 'diff_utp') { valA = a.r_utp - a.m_utp; valB = b.r_utp - b.m_utp; }\n            else if (sortKey === 'pct_utp') { valA = a.m_utp ? (a.r_utp/a.m_utp)*100 : 0; valB = b.m_utp ? (b.r_utp/b.m_utp)*100 : 0; }")
js_content = js_content.replace("else if (sortKey === 'diff_sbr') { valA = a.r_sbr - a.m_sbr; valB = b.r_sbr - b.m_sbr; }", "else if (sortKey === 'diff_sbr') { valA = a.r_sbr - a.m_sbr; valB = b.r_sbr - b.m_sbr; }\n            else if (sortKey === 'pct_sbr') { valA = a.m_sbr ? (a.r_sbr/a.m_sbr)*100 : 0; valB = b.m_sbr ? (b.r_sbr/b.m_sbr)*100 : 0; }")
js_content = js_content.replace("else if (sortKey === 'diff_keluarga') { valA = a.r_kel - a.m_kel; valB = b.r_kel - b.m_kel; }", "else if (sortKey === 'diff_keluarga') { valA = a.r_kel - a.m_kel; valB = b.r_kel - b.m_kel; }\n            else if (sortKey === 'pct_keluarga') { valA = a.m_kel ? (a.r_kel/a.m_kel)*100 : 0; valB = b.m_kel ? (b.r_kel/b.m_kel)*100 : 0; }")

old_tr = """            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${d.nmkab}</td>
                <td style="text-align: right;">${d.m_utp.toLocaleString('id-ID')}</td>
                <td style="text-align: right;">${d.r_utp.toLocaleString('id-ID')}</td>
                <td style="text-align: right; color: ${diffColorUTP}; font-weight: bold;">${diff_utp.toLocaleString('id-ID')}</td>
                <td style="text-align: right;">${d.m_sbr.toLocaleString('id-ID')}</td>
                <td style="text-align: right;">${d.r_sbr.toLocaleString('id-ID')}</td>
                <td style="text-align: right; color: ${diffColorSBR}; font-weight: bold;">${diff_sbr.toLocaleString('id-ID')}</td>
                <td style="text-align: right;">${d.m_kel.toLocaleString('id-ID')}</td>
                <td style="text-align: right;">${d.r_kel.toLocaleString('id-ID')}</td>
                <td style="text-align: right; color: ${diffColorKel}; font-weight: bold;">${diff_kel.toLocaleString('id-ID')}</td>
            `;"""

new_tr = """            const pct_utp = d.m_utp ? ((d.r_utp / d.m_utp) * 100).toFixed(2) : 0;
            const pct_sbr = d.m_sbr ? ((d.r_sbr / d.m_sbr) * 100).toFixed(2) : 0;
            const pct_kel = d.m_kel ? ((d.r_kel / d.m_kel) * 100).toFixed(2) : 0;
            
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${d.nmkab}</td>
                <td style="text-align: right;">${d.m_utp.toLocaleString('id-ID')}</td>
                <td style="text-align: right;">${d.r_utp.toLocaleString('id-ID')}</td>
                <td style="text-align: right; color: ${diffColorUTP}; font-weight: bold;">${diff_utp.toLocaleString('id-ID')}</td>
                <td style="text-align: right;">${pct_utp}%</td>
                <td style="text-align: right;">${d.m_sbr.toLocaleString('id-ID')}</td>
                <td style="text-align: right;">${d.r_sbr.toLocaleString('id-ID')}</td>
                <td style="text-align: right; color: ${diffColorSBR}; font-weight: bold;">${diff_sbr.toLocaleString('id-ID')}</td>
                <td style="text-align: right;">${pct_sbr}%</td>
                <td style="text-align: right;">${d.m_kel.toLocaleString('id-ID')}</td>
                <td style="text-align: right;">${d.r_kel.toLocaleString('id-ID')}</td>
                <td style="text-align: right; color: ${diffColorKel}; font-weight: bold;">${diff_kel.toLocaleString('id-ID')}</td>
                <td style="text-align: right;">${pct_kel}%</td>
            `;"""

js_content = js_content.replace(old_tr, new_tr)

with open('rekon.js', 'w', encoding='utf-8') as f:
    f.write(js_content)
