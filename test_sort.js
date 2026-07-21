const fs = require('fs');

const historyRaw = fs.readFileSync('fast_petugas_history.js', 'utf8');
const jsonStr = historyRaw.substring(historyRaw.indexOf('{'), historyRaw.lastIndexOf('}')+1);
const PETUGAS_HISTORY_MAP = JSON.parse(jsonStr);

global.window = {
    PETUGAS_HISTORY_MAP: PETUGAS_HISTORY_MAP,
    petugasSortField: 'history_2026-07-14',
    petugasSortOrder: -1
};

let arr = [
    { email: 'riskasafitri306@gmail.com', role: 'Pencacah', total: 376, name: 'Riska Safitri' },
    { email: 'itaaariska33@gmail.com', role: 'Pencacah', total: 350, name: 'Ita Riska' }
];

arr.sort((a, b) => {
    let valA, valB;
    const sortField = window.petugasSortField || 'pct';
    const sortOrder = window.petugasSortOrder || -1;
    
    if (sortField.startsWith('history_')) {
        const targetDate = sortField.split('_')[1];
        const getHistoryVal = (pItem) => {
            if (window.PETUGAS_HISTORY_MAP && window.PETUGAS_HISTORY_MAP[targetDate]) {
                const allDates = Object.keys(window.PETUGAS_HISTORY_MAP).sort();
                const dIdx = allDates.indexOf(targetDate);
                if (dIdx > 0) {
                    const prevDate = allDates[dIdx-1];
                    const hSnap = window.PETUGAS_HISTORY_MAP[targetDate][pItem.role]?.[pItem.email] || {};
                    const pSnap = window.PETUGAS_HISTORY_MAP[prevDate][pItem.role]?.[pItem.email] || {};
                    
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
    console.log(`Comparing ${a.email} (${valA}) and ${b.email} (${valB})`);
    
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

console.log(arr.map(x => x.email));
