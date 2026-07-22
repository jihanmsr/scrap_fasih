const fs = require('fs');

const PETUGAS_HISTORY_MAP = {
    "2026-07-13": { "Pencacah": { "a@gmail.com": { submitted_pencacah: 2 }, "b@gmail.com": { submitted_pencacah: 1 } } },
    "2026-07-14": { "Pencacah": { "a@gmail.com": { submitted_pencacah: 20 }, "b@gmail.com": { submitted_pencacah: 25 } } }
};

let arr = [
    { name: "A", email: "a@gmail.com", role: "Pencacah", total: 100 },
    { name: "B", email: "b@gmail.com", role: "Pencacah", total: 100 }
];

const sortField = 'history_2026-07-14';
const sortOrder = -1; // Descending

arr.sort((a, b) => {
    let valA, valB;
    if (sortField.startsWith('history_')) {
        const targetDate = sortField.replace('history_', '');
        const allDates = Object.keys(PETUGAS_HISTORY_MAP || {}).sort();
        const dIdx = allDates.indexOf(targetDate);
        const getHistoryVal = (pItem) => {
            if (PETUGAS_HISTORY_MAP && PETUGAS_HISTORY_MAP[targetDate] && PETUGAS_HISTORY_MAP[targetDate][pItem.role]) {
                if (dIdx > 0) {
                    const prevDate = allDates[dIdx-1];
                    const hSnap = PETUGAS_HISTORY_MAP[targetDate][pItem.role]?.[pItem.email] || {};
                    const pSnap = PETUGAS_HISTORY_MAP[prevDate][pItem.role]?.[pItem.email] || {};
                    
                    let currCum = (hSnap.submitted_pencacah || 0);
                    let prevCum = (pSnap.submitted_pencacah || 0);
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

console.log(arr.map(x => x.name));
