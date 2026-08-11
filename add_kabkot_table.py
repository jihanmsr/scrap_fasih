with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

target = "                <!-- TABEL PETUGAS -->"

kabkot_html = """                <!-- TABEL KABKOT -->
                <div id="rekon-sub-kabkot" class="ipas-table-wrapper" style="display: none; max-height: 600px; overflow-y: auto;">
                    <table class="ipas-table">
                        <thead>
                            <tr>
                                <th rowspan="2" class="sortable" onclick="sortRekon('kabkot', 'nmkab')">Kab/Kota</th>
                                <th colspan="3"
                                    style="text-align: center; background: rgba(59,130,246,0.1); border-bottom: 1px solid var(--card-border);">
                                    USAHA (UTP)</th>
                                <th colspan="3"
                                    style="text-align: center; background: rgba(16,185,129,0.1); border-bottom: 1px solid var(--card-border);">
                                    USAHA (SBR)</th>
                                <th colspan="3"
                                    style="text-align: center; background: rgba(245,158,11,0.1); border-bottom: 1px solid var(--card-border);">
                                    KELUARGA</th>
                            </tr>
                            <tr>
                                <!-- UTP -->
                                <th class="sortable" onclick="sortRekon('kabkot', 'muatan_utp')" style="text-align:right;">Muatan</th>
                                <th class="sortable" onclick="sortRekon('kabkot', 'realisasi_utp')" style="text-align:right;">Realisasi</th>
                                <th class="sortable" onclick="sortRekon('kabkot', 'diff_utp')" style="text-align:right;">Selisih</th>
                                <!-- SBR -->
                                <th class="sortable" onclick="sortRekon('kabkot', 'muatan_sbr')" style="text-align:right;">Muatan</th>
                                <th class="sortable" onclick="sortRekon('kabkot', 'realisasi_sbr')" style="text-align:right;">Realisasi</th>
                                <th class="sortable" onclick="sortRekon('kabkot', 'diff_sbr')" style="text-align:right;">Selisih</th>
                                <!-- KELUARGA -->
                                <th class="sortable" onclick="sortRekon('kabkot', 'muatan_keluarga')" style="text-align:right;">Muatan</th>
                                <th class="sortable" onclick="sortRekon('kabkot', 'realisasi_keluarga')" style="text-align:right;">Realisasi</th>
                                <th class="sortable" onclick="sortRekon('kabkot', 'diff_keluarga')" style="text-align:right;">Selisih</th>
                            </tr>
                        </thead>
                        <tbody id="rekon-table-kabkot"></tbody>
                    </table>
                </div>

"""

if "id=\"rekon-sub-kabkot\"" not in content:
    content = content.replace(target, kabkot_html + target)
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Added KabKot table to index.html")
else:
    print("KabKot table already exists in index.html")
