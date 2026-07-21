const fs = require('fs');

const historyRaw = fs.readFileSync('fast_petugas_history.js', 'utf8');
const jsonStr = historyRaw.substring(historyRaw.indexOf('{'), historyRaw.lastIndexOf('}')+1);
const PETUGAS_HISTORY_MAP = JSON.parse(jsonStr);

let arr = [];
for (const email in PETUGAS_HISTORY_MAP['2026-07-21']['Pencacah']) {
    arr.push({ email: email, role: 'Pencacah', name: email, total: 100 });
}
for (const email in PETUGAS_HISTORY_MAP['2026-07-21']['Pengawas']) {
    arr.push({ email: email, role: 'Pengawas', name: email, total: 100 });
}

console.log("Total officers:", arr.length);

const sortField = 'history_2026-07-21';
const sortOrder = -1;

try {
    arr.sort((a, b) => {
        let valA, valB;
        if (sortField.startsWith('history_')) {
            const targetDate = sortField.split('_')[1];
            const getHistoryVal = (pItem) => {
                if (PETUGAS_HISTORY_MAP && PETUGAS_HISTORY_MAP[targetDate]) {
                    const allDates = Object.keys(PETUGAS_HISTORY_MAP).sort();
                    const dIdx = allDates.indexOf(targetDate);
                    if (dIdx > 0) {
                        const prevDate = allDates[dIdx-1];
                        const hSnap = PETUGAS_HISTORY_MAP[targetDate][pItem.role]?.[pItem.email] || {};
                        const pSnap = PETUGAS_HISTORY_MAP[prevDate][pItem.role]?.[pItem.email] || {};
                        
                        let currCum = 0, prevCum = 0;
                        if (pItem.role === 'Pengawas') {
                            currCum = (hSnap.approved || 0) + (hSnap.rejected || 0) + (hSnap.revoked || 0);
                            prevCum = (pSnap.approved || 0) + (pSnap.rejected || 0) + (pSnap.revoked || 0);
                        } else {
                            currCum = (hSnap.submitted_pencacah || 0) + (hSnap.approved || 0) + (hSnap.rejected || 0) + 
                                      (hSnap.edited_admin || 0) + (hSnap.completed_admin || 0) + (hSnap.submitted_respondent || 0) + 
                                      (hSnap.revoked || 0) + (hSnap.edited_pengawas || 0);
                            prevCum = (pSnap.submitted_pencacah || 0) + (pSnap.approved || 0) + (pSnap.rejected || 0) + 
                                      (pSnap.edited_admin || 0) + (pSnap.completed_admin || 0) + (pSnap.submitted_respondent || 0) + 
                                      (pSnap.revoked || 0) + (pSnap.edited_pengawas || 0);
                        }
                        return currCum - prevCum;
                    }
                }
                return 0;
            };
            valA = getHistoryVal(a);
            valB = getHistoryVal(b);
        }
        
        if (typeof valA === 'string' && typeof valB === 'string') {
            const cmp = valA.localeCompare(valB) * sortOrder;
            if (cmp !== 0) return cmp;
        } else {
            const cmp = (valA - valB) * sortOrder;
            if (cmp !== 0) return cmp;
        }
        
        if (a.total !== b.total) {
            return b.total - a.total;
        }
        return a.name.localeCompare(b.name);
    });
    console.log("Sort successful!");
    console.log("Top 3 values:", arr.slice(0, 3).map(a => {
        // compute val again to show it
        const targetDate = '2026-07-21';
        const prevDate = '2026-07-20';
        const hSnap = PETUGAS_HISTORY_MAP[targetDate][a.role]?.[a.email] || {};
        const pSnap = PETUGAS_HISTORY_MAP[prevDate][a.role]?.[a.email] || {};
        let currCum = 0, prevCum = 0;
        if (a.role === 'Pengawas') {
            currCum = (hSnap.approved || 0) + (hSnap.rejected || 0) + (hSnap.revoked || 0);
            prevCum = (pSnap.approved || 0) + (pSnap.rejected || 0) + (pSnap.revoked || 0);
        } else {
            currCum = (hSnap.submitted_pencacah || 0) + (hSnap.approved || 0) + (hSnap.rejected || 0) + (hSnap.edited_admin || 0) + (hSnap.completed_admin || 0) + (hSnap.submitted_respondent || 0) + (hSnap.revoked || 0) + (hSnap.edited_pengawas || 0);
            prevCum = (pSnap.submitted_pencacah || 0) + (pSnap.approved || 0) + (pSnap.rejected || 0) + (pSnap.edited_admin || 0) + (pSnap.completed_admin || 0) + (pSnap.submitted_respondent || 0) + (pSnap.revoked || 0) + (pSnap.edited_pengawas || 0);
        }
        return currCum - prevCum;
    }));
} catch (e) {
    console.error("SORT FAILED!", e);
}
