const fs = require('fs');

const appJs = fs.readFileSync('app.js', 'utf8');

// We need to evaluate getHistoryVal logic
const allDates = ["2026-07-09", "2026-07-13", "2026-07-14"];
const dIdx = 1; // 13 JUL
const targetDate = "2026-07-13";
const PETUGAS_HISTORY_MAP = {
    "2026-07-09": {
        "Pencacah": {
            "test@gmail.com": { approved: 0, submitted_pencacah: 0 }
        }
    },
    "2026-07-13": {
        "Pencacah": {
            "test@gmail.com": { approved: 2, submitted_pencacah: 0 }
        }
    }
};

const pItem = { role: "Pencacah", email: "test@gmail.com" };

const getHistoryVal = (pItem) => {
    if (PETUGAS_HISTORY_MAP && PETUGAS_HISTORY_MAP[targetDate] && PETUGAS_HISTORY_MAP[targetDate][pItem.role]) {
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

console.log(getHistoryVal(pItem));
