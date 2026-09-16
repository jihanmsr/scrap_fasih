import re

with open('keberadaan_petugas.js', 'r') as f:
    content = f.read()

# 1. Update renderTableHeader variables
header_injection = """
        const isSlsMode = (window.keberadaanGrouping === 'sls');
        const col2Title = isSlsMode ? `Kode SLS ${sortIcon('id')}` : `Nama Petugas ${sortIcon('name')}`;
        const col3Title = isSlsMode ? `Petugas ${sortIcon('petugas_name')}` : `SLS ${sortIcon('sls_count')}`;
        const col2Sort = isSlsMode ? 'id' : 'name';
        const col3Sort = isSlsMode ? 'petugas_name' : 'sls_count';
"""

content = re.sub(
    r'(function renderTableHeader\(\) \{[\s\S]*?function sortIcon\(f\) \{[\s\S]*?return `<span style="font-size:0\.75rem; color:var\(--primary\); font-weight:800;">\$\{so === 1 \? \' ▲\' : \' ▼\'\}</span>`;\n        \})',
    r'\1\n' + header_injection,
    content
)

# 2. Update COMPACT VIEW header
content = re.sub(
    r'<th style="text-align: left; min-width: 190px; cursor: pointer;" onclick="window\.sortKeberadaan\(\'name\'\)">Nama Petugas \$\{sortIcon\(\'name\'\)\}<\/th>\n\s*<th style="text-align: center; width: 70px; cursor: pointer;" onclick="window\.sortKeberadaan\(\'sls_count\'\)">SLS \$\{sortIcon\(\'sls_count\'\)\}<\/th>',
    r'<th style="text-align: left; min-width: 190px; cursor: pointer;" onclick="window.sortKeberadaan(\'${col2Sort}\')">${col2Title}</th>\n                    <th style="text-align: center; width: 140px; cursor: pointer;" onclick="window.sortKeberadaan(\'${col3Sort}\')">${col3Title}</th>',
    content
)

# 3. Update FULL VIEW header
content = re.sub(
    r'<th rowspan="2" style="text-align: left; min-width: 190px; vertical-align: middle; cursor: pointer;" onclick="window\.sortKeberadaan\(\'name\'\)">Nama Petugas \$\{sortIcon\(\'name\'\)\}<\/th>\n\s*<th rowspan="2" style="text-align: center; width: 65px; vertical-align: middle; cursor: pointer;" onclick="window\.sortKeberadaan\(\'sls_count\'\)">SLS \$\{sortIcon\(\'sls_count\'\)\}<\/th>',
    r'<th rowspan="2" style="text-align: left; min-width: 190px; vertical-align: middle; cursor: pointer;" onclick="window.sortKeberadaan(\'${col2Sort}\')">${col2Title}</th>\n                    <th rowspan="2" style="text-align: center; width: 140px; vertical-align: middle; cursor: pointer;" onclick="window.sortKeberadaan(\'${col3Sort}\')">${col3Title}</th>',
    content
)

# 4. Update data generation logic
flatten_logic = """
        let rawList = [];
        if (window.keberadaanGrouping === 'sls') {
            const pencacah = window.DATA_KEBERADAAN_PETUGAS.pencacah || [];
            const pengawas = window.DATA_KEBERADAAN_PETUGAS.pengawas || [];
            const allPetugas = (window.keberadaanRole === 'Pengawas') ? pengawas : pencacah;
            
            allPetugas.forEach(p => {
                if (p.sls && Array.isArray(p.sls)) {
                    p.sls.forEach(s => {
                        const kode14 = s[0] || '';
                        const sub2 = s[1] || '';
                        const kode16 = kode14 + sub2;
                        const kab = kode14.substring(0, 4);
                        const kec = kode14.substring(0, 7);
                        const petName = getPetugasName(p.email);
                        
                        rawList.push({
                            is_sls: true,
                            id: kode16,
                            name: kode16, 
                            petugas_name: petName,
                            role: p.role,
                            email: p.email,
                            kabs: [kab],
                            kecs: [kec],
                            bu_dit: s[2]||0,
                            bu_bar: s[3]||0,
                            bu_tdk: s[4]||0,
                            bu_tut: s[5]||0,
                            bu_gan: s[6]||0,
                            bu_pus: s[7]||0,
                            kl_dit: s[8]||0,
                            kl_bar: s[9]||0,
                            kl_tdk: s[10]||0,
                            kl_men: s[11]||0,
                            kl_eli: s[12]||0,
                            kl_tem: s[13]||0,
                            kl_khu: s[14]||0,
                            tot_status: s[15]||0,
                            tot_keb: s[16]||0,
                            selisih: s[17]||0,
                            anomali_count: (s[17] !== 0) ? 1 : 0
                        });
                    });
                }
            });
        } else {
            rawList = (window.keberadaanRole === 'Pengawas')
                ? (window.DATA_KEBERADAAN_PETUGAS.pengawas || [])
                : (window.DATA_KEBERADAAN_PETUGAS.pencacah || []);
        }

        let filtered = rawList.map(p => {
"""

content = re.sub(
    r'        const rawList = \(window\.keberadaanRole === \'Pengawas\'\)\n\s*\? \(window\.DATA_KEBERADAAN_PETUGAS\.pengawas \|\| \[\]\)\n\s*: \(window\.DATA_KEBERADAAN_PETUGAS\.pencacah \|\| \[\]\);\n\n\s*let filtered = rawList\.map\(p => \{',
    flatten_logic,
    content
)

# 5. Update row rendering to handle SLS specific rendering
row_rendering = """
            const isSlsMode = (window.keberadaanGrouping === 'sls');
            const col2Content = isSlsMode 
                ? `<span>${p.id}</span>` 
                : `<span>${p.name}</span>\n                            ${roleBadge}`;
            const col3Content = isSlsMode 
                ? `<div style="text-align: left; font-size: 0.78rem; display: flex; flex-direction: column; gap: 0.1rem;">
                       <span style="font-weight: 700; color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 130px;" title="${p.petugas_name}">${p.petugas_name}</span>
                       ${roleBadge}
                   </div>`
                : `<span class="badge" style="background: var(--bg-secondary); color: var(--text-primary); font-weight: 700; padding: 2px 6px; border-radius: 6px; border: 1px solid var(--border-light); font-size: 0.78rem;">${p.sls_count}</span>`;
            
            const emailSubtitle = isSlsMode ? `<div style="font-size: 0.76rem; color: var(--text-secondary); margin-top: 1px;">SLS</div>` : `<div style="font-size: 0.76rem; color: var(--text-secondary); margin-top: 1px; font-family: monospace;">${p.email}</div>`;
"""

content = re.sub(
    r'            const roleBadge = \(p\.role === \'Pengawas\'\)\n[\s\S]*?Detail\n\s*</button>\n\s*`;',
    lambda m: m.group(0) + '\n' + row_rendering,
    content
)

# 6. Replace hardcoded cells in COMPACT ROW
content = re.sub(
    r'                            <span>\$\{p\.name\}</span>\n                            \$\{roleBadge\}\n                        </div>\n                        <div style="font-size: 0\.76rem; color: var\(--text-secondary\); margin-top: 1px; font-family: monospace;">\$\{p\.email\}</div>\n                    </td>\n                    <td style="text-align: center;">\n                        <span class="badge" style="background: var\(--bg-secondary\); color: var\(--text-primary\); font-weight: 700; padding: 3px 8px; border-radius: 6px; border: 1px solid var\(--border-light\);">\$\{p\.sls_count\}</span>\n                    </td>',
    r'                            ${col2Content}\n                        </div>\n                        ${emailSubtitle}\n                    </td>\n                    <td style="text-align: center;">\n                        ${col3Content}\n                    </td>',
    content
)

# 7. Replace hardcoded cells in FULL ROW
content = re.sub(
    r'                            <span>\$\{p\.name\}</span>\n                            \$\{roleBadge\}\n                        </div>\n                        <div style="font-size: 0\.74rem; color: var\(--text-secondary\); margin-top: 1px; font-family: monospace;">\$\{p\.email\}</div>\n                    </td>\n                    <td style="text-align: center;">\n                        <span class="badge" style="background: var\(--bg-secondary\); color: var\(--text-primary\); font-weight: 700; padding: 2px 6px; border-radius: 6px; border: 1px solid var\(--border-light\); font-size: 0\.78rem;">\$\{p\.sls_count\}</span>\n                    </td>',
    r'                            ${col2Content}\n                        </div>\n                        ${emailSubtitle}\n                    </td>\n                    <td style="text-align: center;">\n                        ${col3Content}\n                    </td>',
    content
)

# 8. Hide "Aksi" detail button in SLS mode since it's meant for showing a modal of subsls of a Petugas
content = re.sub(
    r'                    <td style="text-align: center;">\$\{actionBtn\}</td>',
    r'                    <td style="text-align: center;">${isSlsMode ? "-" : actionBtn}</td>',
    content
)

# 9. Update pagination info
content = re.sub(
    r'Menampilkan <b>\$\{startDisplay\} - \$\{endDisplay\}</b> dari <b>\$\{formatNumber\(totalItems\)\}</b> \$\{window\.keberadaanRole\}',
    r'Menampilkan <b>${startDisplay} - ${endDisplay}</b> dari <b>${formatNumber(totalItems)}</b> ${isSlsMode ? \'SLS\' : window.keberadaanRole}',
    content
)
content = re.sub(
    r'Tidak ada data \$\{window\.keberadaanRole\} yang cocok dengan filter.',
    r'Tidak ada data ${isSlsMode ? \'SLS\' : window.keberadaanRole} yang cocok dengan filter.',
    content
)

with open('keberadaan_petugas.js', 'w') as f:
    f.write(content)

print("Patch applied")
