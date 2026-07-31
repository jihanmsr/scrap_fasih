import re

with open('index.html', 'r') as f:
    content = f.read()

# 1. Ubah teks tombol sidebar dari "Perbandingan" ke "Tabulasi"
content = content.replace('                    Perbandingan\n                </button>', '                    Tabulasi\n                </button>')

# 2. Ubah header tabel SLS
new_sls_thead = """                <thead>
                    <tr>
                        <th rowspan="2" class="sortable" onclick="sortRekon('sls', 'sls_id')">ID SLS</th>
                        <th rowspan="2" class="sortable" onclick="sortRekon('sls', 'nmkab')">Kab/Kec/Desa</th>
                        <th colspan="3" style="text-align: center; background: rgba(59,130,246,0.1); border-bottom: 1px solid var(--card-border);">USAHA (UTP)</th>
                        <th colspan="3" style="text-align: center; background: rgba(16,185,129,0.1); border-bottom: 1px solid var(--card-border);">USAHA (SBR)</th>
                        <th colspan="3" style="text-align: center; background: rgba(245,158,11,0.1); border-bottom: 1px solid var(--card-border);">KELUARGA</th>
                    </tr>
                    <tr>
                        <!-- UTP -->
                        <th class="sortable" onclick="sortRekon('sls', 'muatan_utp')" style="text-align:right;">Muatan</th>
                        <th class="sortable" onclick="sortRekon('sls', 'realisasi_utp')" style="text-align:right;">Realisasi</th>
                        <th class="sortable" onclick="sortRekon('sls', 'diff_utp')" style="text-align:right;">Selisih</th>
                        <!-- SBR -->
                        <th class="sortable" onclick="sortRekon('sls', 'muatan_sbr')" style="text-align:right;">Muatan</th>
                        <th class="sortable" onclick="sortRekon('sls', 'realisasi_sbr')" style="text-align:right;">Realisasi</th>
                        <th class="sortable" onclick="sortRekon('sls', 'diff_sbr')" style="text-align:right;">Selisih</th>
                        <!-- KELUARGA -->
                        <th class="sortable" onclick="sortRekon('sls', 'muatan_keluarga')" style="text-align:right;">Muatan</th>
                        <th class="sortable" onclick="sortRekon('sls', 'realisasi_keluarga')" style="text-align:right;">Realisasi</th>
                        <th class="sortable" onclick="sortRekon('sls', 'diff_keluarga')" style="text-align:right;">Selisih</th>
                    </tr>
                </thead>"""
content = re.sub(r'                <thead>\n                    <tr>\n                        <th class="sortable" onclick="sortRekon\(\'sls\', \'sls_id\'\)".*?</tr>\n                </thead>', new_sls_thead, content, flags=re.DOTALL)

# 3. Ubah header tabel Petugas
new_petugas_thead = """                <thead>
                    <tr>
                        <th rowspan="2" class="sortable" onclick="sortRekon('petugas', 'email')">Email Petugas</th>
                        <th colspan="3" style="text-align: center; background: rgba(59,130,246,0.1); border-bottom: 1px solid var(--card-border);">USAHA (UTP)</th>
                        <th colspan="3" style="text-align: center; background: rgba(16,185,129,0.1); border-bottom: 1px solid var(--card-border);">USAHA (SBR)</th>
                        <th colspan="3" style="text-align: center; background: rgba(245,158,11,0.1); border-bottom: 1px solid var(--card-border);">KELUARGA</th>
                    </tr>
                    <tr>
                        <!-- UTP -->
                        <th class="sortable" onclick="sortRekon('petugas', 'muatan_utp')" style="text-align:right;">Muatan</th>
                        <th class="sortable" onclick="sortRekon('petugas', 'realisasi_utp')" style="text-align:right;">Realisasi</th>
                        <th class="sortable" onclick="sortRekon('petugas', 'diff_utp')" style="text-align:right;">Selisih</th>
                        <!-- SBR -->
                        <th class="sortable" onclick="sortRekon('petugas', 'muatan_sbr')" style="text-align:right;">Muatan</th>
                        <th class="sortable" onclick="sortRekon('petugas', 'realisasi_sbr')" style="text-align:right;">Realisasi</th>
                        <th class="sortable" onclick="sortRekon('petugas', 'diff_sbr')" style="text-align:right;">Selisih</th>
                        <!-- KELUARGA -->
                        <th class="sortable" onclick="sortRekon('petugas', 'muatan_keluarga')" style="text-align:right;">Muatan</th>
                        <th class="sortable" onclick="sortRekon('petugas', 'realisasi_keluarga')" style="text-align:right;">Realisasi</th>
                        <th class="sortable" onclick="sortRekon('petugas', 'diff_keluarga')" style="text-align:right;">Selisih</th>
                    </tr>
                </thead>"""
content = re.sub(r'                <thead>\n                    <tr>\n                        <th class="sortable" onclick="sortRekon\(\'petugas\', \'email\'\)".*?</tr>\n                </thead>', new_petugas_thead, content, flags=re.DOTALL)

with open('index.html', 'w') as f:
    f.write(content)
