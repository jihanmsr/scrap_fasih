const fs = require('fs');
const historyRaw = fs.readFileSync('fast_petugas_history.js', 'utf8');
const jsonStr = historyRaw.substring(historyRaw.indexOf('{'), historyRaw.lastIndexOf('}')+1);
const PETUGAS_HISTORY_MAP = JSON.parse(jsonStr);

let found = [];

for (const email in PETUGAS_HISTORY_MAP['2026-07-21']['Pencacah']) {
    const h21 = PETUGAS_HISTORY_MAP['2026-07-21']['Pencacah'][email] || {};
    const c21 = (h21.submitted_pencacah || 0) + (h21.approved || 0) + (h21.rejected || 0) + (h21.edited_admin || 0) + (h21.completed_admin || 0) + (h21.submitted_respondent || 0) + (h21.revoked || 0) + (h21.edited_pengawas || 0);
    const target = h21.target || 1;
    const pct = (c21 / target) * 100;
    
    if (Math.abs(pct - 96.5) < 0.1 || Math.abs(pct - 94.9) < 0.1) {
        found.push({email, pct});
    }
}
console.log(found);
