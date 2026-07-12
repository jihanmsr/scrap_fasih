const fs = require('fs');
// Mock DOM and window
global.window = {};
// Load ipas_data
eval(fs.readFileSync('ipas_data.js', 'utf8'));
const ipasData = window.IPAS_DATA;
const kabFilter = "[10] SIGI";

let totalAll = 0;
let desaMap = {};
const seData = ipasData['se_umum'] || [];
seData.forEach(kab => {
    if (kabFilter !== 'all') {
        const cleanKab = kabFilter.replace(/^\[\d+\]\s*/, '').trim().toUpperCase();
        const cleanItemKab = (kab.kabupaten || '').replace(/^\[\d+\]\s*/, '').trim().toUpperCase();
        if (cleanItemKab !== cleanKab) return;
    }
    (kab.kecamatan_list || []).forEach(kec => {
        if (!kec.kec_name || kec.kec_name === '-') return;
        const key = `${kec.kec_name} | (data per kecamatan)`;
        desaMap[key] = { kec: kec.kec_name };
        totalAll += 1;
    });
});
console.log("Total: ", totalAll);
console.log("Desa Map length: ", Object.keys(desaMap).length);
