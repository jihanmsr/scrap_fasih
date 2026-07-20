const fs = require('fs');
let code = fs.readFileSync('app.js', 'utf8');

// Replace fetch block with dynamic script loading
const oldFetch = `        try {
            if (!window.ALL_REGIONS_MAP) {
                const resp = await fetch('region_map_sulteng_full.json');
                const data = await resp.json();
                const lookup = {};
                if (data && data.kabupaten) {
                    for (const kabCode of Object.keys(data.kabupaten)) {
                        const kab = data.kabupaten[kabCode];
                        if (!kab.kecamatan) continue;
                        for (const kecCode of Object.keys(kab.kecamatan)) {
                            const kec = kab.kecamatan[kecCode];
                            if (!kec.desa) continue;
                            for (const desaCode of Object.keys(kec.desa)) {
                                lookup[desaCode] = {
                                    kec: kec.kec_name,
                                    desa: kec.desa[desaCode].desa_name
                                };
                            }
                        }
                    }
                }
                window.ALL_REGIONS_MAP = lookup;
            }
            regionLookup = window.ALL_REGIONS_MAP;
            if (statusEl) statusEl.textContent = '⏳ Data wilayah siap. (2/2)...';
        } catch (e) {
            console.error('Gagal fetch wilayah', e);
            if (statusEl) statusEl.textContent = '⚠️ Gagal menarik data wilayah. Mengabaikan opsi wilayah.';
        }`;

const newFetch = `        try {
            if (!window.ALL_REGIONS_MAP) {
                await new Promise((resolve, reject) => {
                    const script = document.createElement('script');
                    script.src = 'region_map_sulteng_full.js';
                    script.onload = resolve;
                    script.onerror = reject;
                    document.head.appendChild(script);
                });
                
                const data = window.REGION_MAP_SULTENG_FULL;
                const lookup = {};
                if (data && data.kabupaten) {
                    for (const kabCode of Object.keys(data.kabupaten)) {
                        const kab = data.kabupaten[kabCode];
                        if (!kab.kecamatan) continue;
                        for (const kecCode of Object.keys(kab.kecamatan)) {
                            const kec = kab.kecamatan[kecCode];
                            if (!kec.desa) continue;
                            for (const desaCode of Object.keys(kec.desa)) {
                                lookup[desaCode] = {
                                    kec: kec.kec_name,
                                    desa: kec.desa[desaCode].desa_name
                                };
                            }
                        }
                    }
                }
                window.ALL_REGIONS_MAP = lookup;
            }
            regionLookup = window.ALL_REGIONS_MAP;
            if (statusEl) statusEl.textContent = '⏳ Data wilayah siap. (2/2)...';
        } catch (e) {
            console.error('Gagal load wilayah js', e);
            if (statusEl) statusEl.textContent = '⚠️ Gagal meload file wilayah. Mengabaikan opsi wilayah.';
        }`;

code = code.replace(oldFetch, newFetch);


// Replace filename logic for Petugas
const oldFilenamePetugas = `const filename = \`Rekap_Petugas_\${surveyLabel}_\${kabLabel}_\${today}\${ext}\`;`;
const newFilenamePetugas = `const suffixW = includeRegion ? '_Wilayah' : '';\n                const filename = \`Rekap_Petugas_\${surveyLabel}_\${kabLabel}\${suffixW}_\${today}\${ext}\`;`;
code = code.replace(oldFilenamePetugas, newFilenamePetugas);

// Replace filename logic for Desa just in case
const oldFilenameDesa = `const filename = \`Rekap_Desa_\${surveyLabel}_\${kabLabel}_\${today}\${ext}\`;`;
const newFilenameDesa = `const filename = \`Rekap_Desa_\${surveyLabel}_\${kabLabel}_\${today}\${ext}\`;`;

fs.writeFileSync('app.js', code);
console.log("Patched app.js successfully!");
