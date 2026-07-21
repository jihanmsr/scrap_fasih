const fs = require('fs');
const historyRaw = fs.readFileSync('fast_petugas_history.js', 'utf8');
const jsonStr = historyRaw.substring(historyRaw.indexOf('{'), historyRaw.lastIndexOf('}')+1);
const PETUGAS_HISTORY_MAP = JSON.parse(jsonStr);

function getDelta(email, targetDate, prevDate) {
    const hSnap = PETUGAS_HISTORY_MAP[targetDate]['Pencacah'][email] || {};
    const pSnap = PETUGAS_HISTORY_MAP[prevDate]['Pencacah'][email] || {};
    
    const currCum = (hSnap.submitted_pencacah || 0) + (hSnap.approved || 0) + (hSnap.rejected || 0) + (hSnap.edited_admin || 0) + (hSnap.completed_admin || 0) + (hSnap.submitted_respondent || 0) + (hSnap.revoked || 0) + (hSnap.edited_pengawas || 0);
    const prevCum = (pSnap.submitted_pencacah || 0) + (pSnap.approved || 0) + (pSnap.rejected || 0) + (pSnap.edited_admin || 0) + (pSnap.completed_admin || 0) + (pSnap.submitted_respondent || 0) + (pSnap.revoked || 0) + (pSnap.edited_pengawas || 0);
    return currCum - prevCum;
}

const emails = ['niswanveby4@gmail.com', 'arifudinstimikarif@gmail.com'];
for (const email of emails) {
    console.log(email, "20 JUL:", getDelta(email, '2026-07-20', '2026-07-19'));
    console.log(email, "21 JUL:", getDelta(email, '2026-07-21', '2026-07-20'));
}
