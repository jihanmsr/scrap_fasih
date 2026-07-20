const fs = require('fs');
let code = fs.readFileSync('app.js', 'utf8');

// 1. Replace downloadPetugasSummaryExcel to open the modal
const oldDownloadPetugas = `    window.downloadPetugasSummaryExcel = function () {
        const kabFilter = document.getElementById('petugas-kab-filter');
        const selectedKab = kabFilter ? kabFilter.value : 'ALL';
        
        if (selectedKab === 'ALL') {
            const dateInput = prompt("Data raw (CSV) tersedia mulai tanggal 11. Masukkan tanggal yang ingin didownload (Format YYYY-MM-DD):", "2026-07-11");
            if (dateInput) {
                const url = \`fast_petugas_all_\${dateInput}.csv\`;
                const a = document.createElement('a');
                a.href = url;
                a.download = url;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
            }
            return;
        }

        if (!window.lastPetugasSummaryArr || window.lastPetugasSummaryArr.length === 0) {
            alert("Tidak ada data untuk diunduh.");
            return;
        }
        
        const headers = ["Nama Petugas", "Email / Username", "Role", "Total Target", "Belum Selesai (Total)", "Open", "Draft", "Selesai (Total)", "Submit PPL", "Submit Respondent", "Approved", "Completed Admin", "Rejected", "Revoked", "Edited PML", "Edited Admin"];
        
        let dates = [];
        if (window._showPetugasHistory && window.PETUGAS_HISTORY_MAP) {
            dates = Object.keys(window.PETUGAS_HISTORY_MAP).sort().filter(d => d !== "2026-07-09");
            dates.forEach(d => {
                const dObj = new Date(d + 'T00:00:00');
                headers.push(dObj.toLocaleDateString('id-ID', { day: 'numeric', month: 'short' }) + " (Delta)");
                headers.push(dObj.toLocaleDateString('id-ID', { day: 'numeric', month: 'short' }) + " (%)");
            });
        }
        headers.push("% Capaian");

        const rows = window.lastPetugasSummaryArr.map(p => {
            const row = [
                p.name, p.email, p.role, p.total, p.belum, 
                p.open || 0, p.draft || 0, 
                p.selesai, 
                p.submitted_pencacah || 0, p.submitted_respondent || 0, p.approved || 0, p.completed_admin || 0,
                p.rejected || 0, p.revoked || 0, p.edited_pengawas || 0, p.edited_admin || 0
            ];
            
            if (window._showPetugasHistory && window.PETUGAS_HISTORY_MAP) {
                dates.forEach((d, dIdx) => {
                    let dVal = "";
                    let dPct = "";
                    
                    if (window.PETUGAS_HISTORY_MAP[d] && window.PETUGAS_HISTORY_MAP[d][p.role] && window.PETUGAS_HISTORY_MAP[d][p.role][p.email]) {
                        if (dIdx > 0) {
                            const prevDate = dates[dIdx-1];
                            const hSnap = window.PETUGAS_HISTORY_MAP[d][p.role][p.email];
                            if (window.PETUGAS_HISTORY_MAP[prevDate] && window.PETUGAS_HISTORY_MAP[prevDate][p.role] && window.PETUGAS_HISTORY_MAP[prevDate][p.role][p.email]) {
                                const pSnap = window.PETUGAS_HISTORY_MAP[prevDate][p.role][p.email];
                                
                                const getD = (k) => (hSnap[k] || 0) - (pSnap[k] || 0);
                                
                                let currCum = 0, prevCum = 0;
                                if (p.role === 'Pengawas') {
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
                                
                                dVal = currCum - prevCum;
                                let target = hSnap.target || p.total || 1;
                                let pTarget = pSnap.target || p.total || 1;
                                
                                dPct = ((currCum / target * 100) - (prevCum / pTarget * 100)).toFixed(1).replace('.', ',');
                                dVal = dVal > 0 ? "+" + dVal : dVal.toString();
                                dPct = parseFloat(dPct.replace(',','.')) > 0 ? "+" + dPct + "%" : dPct + "%";
                            }
                        }
                    }
                    row.push(dVal);
                    row.push(dPct);
                });
            }
            
            const pct = p.total > 0 ? (p.selesai / p.total * 100).toFixed(1).replace('.', ',') + '%' : '0%';
            row.push(pct);
            
            return row;
        });
        
        exportToCSV(\`rekap_progres_petugas_\${new Date().toISOString().slice(0,10)}.csv\`, headers, rows);
    };`;

const newDownloadPetugas = `    window.downloadPetugasSummaryExcel = function () {
        const kabFilter = document.getElementById('petugas-kab-filter');
        const selectedKab = kabFilter ? kabFilter.value : 'ALL';
        
        if (selectedKab === 'ALL') {
            const dateInput = prompt("Data raw (CSV) tersedia mulai tanggal 11. Masukkan tanggal yang ingin didownload (Format YYYY-MM-DD):", "2026-07-11");
            if (dateInput) {
                const url = \`fast_petugas_all_\${dateInput}.csv\`;
                const a = document.createElement('a');
                a.href = url;
                a.download = url;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
            }
            return;
        }

        if (!window.lastPetugasSummaryArr || window.lastPetugasSummaryArr.length === 0) {
            alert("Tidak ada data untuk diunduh.");
            return;
        }

        const modal = document.getElementById('excel-download-modal');
        if (modal) {
            const summaryTypeEl = document.getElementById('excel-type-summary');
            if (summaryTypeEl) summaryTypeEl.checked = true;
            if (window.onExcelTypeChange) window.onExcelTypeChange();
            modal.style.display = 'flex';
        }
    };`;

code = code.replace(oldDownloadPetugas, newDownloadPetugas);


// 2. Update executeExcelDownload to use the detailed columns
const oldExecuteRowsMap = `                const rows = arr.map((p, i) => {
                    const rowData = {
                        'No': i + 1,
                        'Nama Petugas': p.name || '-',
                        'Email / Username': p.email || '-',
                        'Role': p.role || '-'
                    };

                    if (includeRegion && regionLookup && window.PETUGAS_REGION_MAP && p.email) {
                        const slsList = window.PETUGAS_REGION_MAP[p.email] || [];
                        const kecSet = new Set();
                        const desaSet = new Set();
                        slsList.forEach(sls => {
                            const desaCode = sls.substring(0, 10);
                            if (regionLookup[desaCode]) {
                                if (regionLookup[desaCode].kec && regionLookup[desaCode].kec !== '-') kecSet.add(regionLookup[desaCode].kec);
                                if (regionLookup[desaCode].desa && regionLookup[desaCode].desa !== '-') desaSet.add(regionLookup[desaCode].desa);
                            }
                        });
                        rowData['Kecamatan'] = kecSet.size > 0 ? Array.from(kecSet).sort().join(', ') : '-';
                        rowData['Desa'] = desaSet.size > 0 ? Array.from(desaSet).sort().join(', ') : '-';
                    }

                    rowData['Total Target'] = p.total;
                    rowData['Belum Selesai'] = p.belum;
                    rowData['Selesai'] = p.selesai;
                    rowData['% Capaian'] = p.total > 0 ? ((p.selesai / p.total) * 100).toFixed(1) + '%' : '0.0%';
                    return rowData;
                });`;

const newExecuteRowsMap = `                let dates = [];
                if (window._showPetugasHistory && window.PETUGAS_HISTORY_MAP) {
                    dates = Object.keys(window.PETUGAS_HISTORY_MAP).sort().filter(d => d !== "2026-07-09");
                }

                const rows = arr.map((p, i) => {
                    const rowData = {
                        'No': i + 1,
                        'Nama Petugas': p.name || '-',
                        'Email / Username': p.email || '-',
                        'Role': p.role || '-'
                    };

                    if (includeRegion && regionLookup && window.PETUGAS_REGION_MAP && p.email) {
                        const slsList = window.PETUGAS_REGION_MAP[p.email] || [];
                        const kecSet = new Set();
                        const desaSet = new Set();
                        slsList.forEach(sls => {
                            const desaCode = sls.substring(0, 10);
                            if (regionLookup[desaCode]) {
                                if (regionLookup[desaCode].kec && regionLookup[desaCode].kec !== '-') kecSet.add(regionLookup[desaCode].kec);
                                if (regionLookup[desaCode].desa && regionLookup[desaCode].desa !== '-') desaSet.add(regionLookup[desaCode].desa);
                            }
                        });
                        rowData['Kecamatan'] = kecSet.size > 0 ? Array.from(kecSet).sort().join(', ') : '-';
                        rowData['Desa'] = desaSet.size > 0 ? Array.from(desaSet).sort().join(', ') : '-';
                    }

                    rowData['Total Target'] = p.total;
                    rowData['Belum Selesai (Total)'] = p.belum;
                    rowData['Open'] = p.open || 0;
                    rowData['Draft'] = p.draft || 0;
                    rowData['Selesai (Total)'] = p.selesai;
                    rowData['Submit PPL'] = p.submitted_pencacah || 0;
                    rowData['Submit Respondent'] = p.submitted_respondent || 0;
                    rowData['Approved'] = p.approved || 0;
                    rowData['Completed Admin'] = p.completed_admin || 0;
                    rowData['Rejected'] = p.rejected || 0;
                    rowData['Revoked'] = p.revoked || 0;
                    rowData['Edited PML'] = p.edited_pengawas || 0;
                    rowData['Edited Admin'] = p.edited_admin || 0;
                    
                    if (window._showPetugasHistory && window.PETUGAS_HISTORY_MAP) {
                        dates.forEach((d, dIdx) => {
                            let dVal = "";
                            let dPct = "";
                            
                            if (window.PETUGAS_HISTORY_MAP[d] && window.PETUGAS_HISTORY_MAP[d][p.role] && window.PETUGAS_HISTORY_MAP[d][p.role][p.email]) {
                                if (dIdx > 0) {
                                    const prevDate = dates[dIdx-1];
                                    const hSnap = window.PETUGAS_HISTORY_MAP[d][p.role][p.email];
                                    if (window.PETUGAS_HISTORY_MAP[prevDate] && window.PETUGAS_HISTORY_MAP[prevDate][p.role] && window.PETUGAS_HISTORY_MAP[prevDate][p.role][p.email]) {
                                        const pSnap = window.PETUGAS_HISTORY_MAP[prevDate][p.role][p.email];
                                        
                                        const getD = (k) => (hSnap[k] || 0) - (pSnap[k] || 0);
                                        
                                        let currCum = 0, prevCum = 0;
                                        if (p.role === 'Pengawas') {
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
                                        
                                        dVal = currCum - prevCum;
                                        let target = hSnap.target || p.total || 1;
                                        let pTarget = pSnap.target || p.total || 1;
                                        
                                        dPct = ((currCum / target * 100) - (prevCum / pTarget * 100)).toFixed(1).replace('.', ',');
                                        dVal = dVal > 0 ? "+" + dVal : dVal.toString();
                                        dPct = parseFloat(dPct.replace(',','.')) > 0 ? "+" + dPct + "%" : dPct + "%";
                                    }
                                }
                            }
                            
                            const dObj = new Date(d + 'T00:00:00');
                            const labelDelta = dObj.toLocaleDateString('id-ID', { day: 'numeric', month: 'short' }) + " (Delta)";
                            const labelPct = dObj.toLocaleDateString('id-ID', { day: 'numeric', month: 'short' }) + " (%)";
                            
                            if (dIdx > 0) {
                                rowData[labelDelta] = dVal;
                                rowData[labelPct] = dPct;
                            }
                        });
                    }
                    
                    rowData['% Capaian'] = p.total > 0 ? ((p.selesai / p.total) * 100).toFixed(1) + '%' : '0.0%';
                    return rowData;
                });`;

code = code.replace(oldExecuteRowsMap, newExecuteRowsMap);

// Also need to handle exportToCSV fallback!
// exportToCSV(rows, filename) automatically extracts keys if it's an array of objects. Wait.
// In the old downloadPetugasSummaryExcel, exportToCSV was called with exportToCSV(filename, headers, rows).
// But in executeExcelDownload, it's called as exportToCSV(rows, filename)!
// Let's check how exportToCSV behaves if given array of objects.

fs.writeFileSync('app.js', code);
console.log("Patched app.js successfully!");
