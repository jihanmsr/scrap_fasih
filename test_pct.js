const fs = require('fs');
const historyRaw = fs.readFileSync('fast_petugas_history.js', 'utf8');
const jsonStr = historyRaw.substring(historyRaw.indexOf('{'), historyRaw.lastIndexOf('}')+1);
const PETUGAS_HISTORY_MAP = JSON.parse(jsonStr);

const d20 = PETUGAS_HISTORY_MAP['2026-07-20']['Pencacah']['riskasafitri306@gmail.com'];
const selesai1 = (d20.submitted_pencacah || 0) + (d20.approved || 0) + (d20.rejected || 0) + 
                 (d20.edited_admin || 0) + (d20.completed_admin || 0) + (d20.submitted_respondent || 0) + 
                 (d20.revoked || 0) + (d20.edited_pengawas || 0);
console.log("Riska Safitri - Target:", d20.target, "Selesai:", selesai1, "PCT:", (selesai1 / d20.target) * 100);

const itaa = PETUGAS_HISTORY_MAP['2026-07-20']['Pencacah']['itaaariska33@gmail.com'];
const selesai2 = (itaa.submitted_pencacah || 0) + (itaa.approved || 0) + (itaa.rejected || 0) + 
                 (itaa.edited_admin || 0) + (itaa.completed_admin || 0) + (itaa.submitted_respondent || 0) + 
                 (itaa.revoked || 0) + (itaa.edited_pengawas || 0);
console.log("Ita Riska - Target:", itaa.target, "Selesai:", selesai2, "PCT:", (selesai2 / itaa.target) * 100);
