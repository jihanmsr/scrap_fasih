// ========================================================
// penyisiran_keluarga.js - Tabulasi & Prioritas Penyisiran Keluarga per SLS
// Update Data 9 September 2026
// ========================================================

(function () {
    let pnyKelFiltered = [];
    let pnyKelPage = 1;
    const PNY_KEL_PER_PAGE = 50;
    let pnyKelSortAsc = false; // DESC by default

    // ── Init saat tab dibuka ─────────────────────────────────────────────────
    window.initPenyisiranKeluarga = function () {
        const data = window.PENYISIRAN_KELUARGA_DATA;
        if (!data || data.length === 0) return;

        // Isi dropdown Kab
        const kabSel = document.getElementById('pny-kel-filter-kab');
        if (kabSel && kabSel.options.length <= 1) {
            const kabList = [...new Set(data.map(d => d.kabupaten))].filter(Boolean).sort(window.sortKabupatenCallback || undefined);
            kabList.forEach(k => {
                const opt = document.createElement('option');
                opt.value = k;
                opt.textContent = k;
                kabSel.appendChild(opt);
            });
        }

        window.renderPenyisiranKeluarga();
    };

    // ── Render ───────────────────────────────────────────────────────────────
    window.renderPenyisiranKeluarga = function () {
        const data = window.PENYISIRAN_KELUARGA_DATA;
        if (!data) return;

        const search   = (document.getElementById('pny-kel-search')?.value || '').toLowerCase();
        const kab      = document.getElementById('pny-kel-filter-kab')?.value || '';
        const kategori = document.getElementById('pny-kel-filter-kategori')?.value || '';
        const sortKey  = document.getElementById('pny-kel-sort-by')?.value || 'skor_perhatian';

        // Filter
        pnyKelFiltered = data.filter(d => {
            if (kab && d.kabupaten !== kab) return false;
            if (kategori && d.kategori_sisir !== kategori) return false;
            if (search) {
                const haystack = [d.kabupaten, d.kecamatan, d.desa_kel, d.sls, d.id_sub_sls, d.ppl, d.pml].join(' ').toLowerCase();
                if (!haystack.includes(search)) return false;
            }
            return true;
        });

        // Sort
        pnyKelFiltered.sort((a, b) => {
            const va = a[sortKey] ?? 0;
            const vb = b[sortKey] ?? 0;
            return pnyKelSortAsc ? va - vb : vb - va;
        });

        pnyKelPage = 1;
        updatePnyKelSummaryCards();
        renderPnyKelTable();
    };

    // ── Summary cards (based on full filtered set) ───────────────────────────
    function updatePnyKelSummaryCards() {
        const totalSls    = pnyKelFiltered.length;
        const totalBeban  = pnyKelFiltered.reduce((s, d) => s + (d.target_muatan || 0), 0);
        const totalHilang = pnyKelFiltered.reduce((s, d) => s + (d.tidak_ditemukan || 0), 0);
        const p1 = pnyKelFiltered.filter(d => d.kategori_sisir === 'PRIORITAS 1 - SISIR SEGERA').length;
        const p2 = pnyKelFiltered.filter(d => d.kategori_sisir === 'PRIORITAS 2 - PERLU CEK').length;
        const p3 = pnyKelFiltered.filter(d => d.kategori_sisir === 'PRIORITAS 3 - WAJAR').length;
        const pctHilang = totalBeban > 0 ? ((totalHilang / totalBeban) * 100).toFixed(1) : 0;

        setText('pny-kel-total-sls', totalSls.toLocaleString('id-ID'));
        setText('pny-kel-total-beban', totalBeban.toLocaleString('id-ID'));
        setText('pny-kel-total-hilang', totalHilang.toLocaleString('id-ID'));
        setText('pny-kel-pct-hilang', pctHilang + '% dari total beban SLS');
        setText('pny-kel-p1', p1.toLocaleString('id-ID'));
        setText('pny-kel-p2', p2.toLocaleString('id-ID'));
        setText('pny-kel-p3', p3.toLocaleString('id-ID'));
        setText('pny-kel-count', totalSls.toLocaleString('id-ID') + ' SLS');
    }

    function setText(id, val) {
        const el = document.getElementById(id);
        if (el) el.textContent = val;
    }

    // ── Render Table ─────────────────────────────────────────────────────────
    function renderPnyKelTable() {
        const tbody = document.getElementById('penyisiran-keluarga-tbody');
        if (!tbody) return;

        const total = pnyKelFiltered.length;
        const totalPages = Math.ceil(total / PNY_KEL_PER_PAGE);
        const start = (pnyKelPage - 1) * PNY_KEL_PER_PAGE;
        const pageData = pnyKelFiltered.slice(start, start + PNY_KEL_PER_PAGE);

        if (pageData.length === 0) {
            tbody.innerHTML = '<tr><td colspan="12" style="text-align:center;padding:2rem;color:var(--text-secondary);">Tidak ada data SLS keluarga hilang yang sesuai filter.</td></tr>';
            renderPnyKelPagination(total, totalPages);
            return;
        }

        const tdR = 'padding:0.6rem 0.75rem;font-size:0.82rem;text-align:right;border-bottom:1px solid var(--card-border);';
        const tdL = 'padding:0.6rem 0.75rem;font-size:0.82rem;text-align:left;border-bottom:1px solid var(--card-border);';
        const tdC = 'padding:0.6rem 0.75rem;font-size:0.82rem;text-align:center;border-bottom:1px solid var(--card-border);';

        const rows = pageData.map((d, i) => {
            const rank = start + i + 1;
            const kategoriColor = d.kategori_sisir === 'PRIORITAS 1 - SISIR SEGERA'
                ? { bg: 'rgba(239,68,68,0.08)', text: '#dc2626', dot: '🔴', border: '#ef4444' }
                : d.kategori_sisir === 'PRIORITAS 2 - PERLU CEK'
                ? { bg: 'rgba(245,158,11,0.08)', text: '#d97706', dot: '🟡', border: '#f59e0b' }
                : { bg: 'rgba(34,197,94,0.06)', text: '#16a34a', dot: '🟢', border: '#22c55e' };

            const rowBg = d.kategori_sisir === 'PRIORITAS 1 - SISIR SEGERA' ? 'background:rgba(239,68,68,0.035);' : '';

            const skorColor = d.skor_perhatian >= 70 ? '#dc2626'
                : d.skor_perhatian >= 45 ? '#d97706'
                : '#16a34a';

            const pctColor = d.pct_tdk_ditemukan >= 60 ? '#dc2626'
                : d.pct_tdk_ditemukan >= 35 ? '#d97706'
                : '#16a34a';

            const hilangNum = `<span style="color:#ef4444;font-weight:700;">${(d.tidak_ditemukan || 0).toLocaleString('id-ID')}</span>`;

            return `<tr style="${rowBg}" onmouseenter="this.style.background='var(--hover-bg)'" onmouseleave="this.style.background='${d.kategori_sisir === 'PRIORITAS 1 - SISIR SEGERA' ? 'rgba(239,68,68,0.035)' : ''}'">
                <td style="${tdC}color:var(--text-secondary);font-size:0.75rem;">${rank}</td>
                <td style="${tdL}font-weight:600;white-space:nowrap;">${d.kabupaten || '-'}</td>
                <td style="${tdL}color:var(--text-secondary);white-space:nowrap;">${d.kecamatan || '-'}</td>
                <td style="${tdL}color:var(--text-secondary);white-space:nowrap;max-width:160px;overflow:hidden;text-overflow:ellipsis;" title="${d.desa_kel || ''}">${d.desa_kel || '-'}</td>
                <td style="${tdL}">
                    <div style="font-weight:600;font-size:0.82rem;color:var(--text-primary);">${d.sls || '-'}</div>
                    <div style="font-size:0.68rem;color:var(--text-secondary);font-family:monospace;">${d.id_sub_sls || ''}</div>
                </td>
                <td style="${tdR}font-weight:600;">${(d.target_muatan || 0).toLocaleString('id-ID')}</td>
                <td style="${tdR}color:#16a34a;font-weight:600;">${(d.realisasi_ditemukan || 0).toLocaleString('id-ID')}</td>
                <td style="${tdR}">${hilangNum}</td>
                <td style="${tdC}">
                    <span style="font-size:0.72rem;color:#b45309;font-weight:600;" title="Indikasi Pindah SLS: ${d.pindah_ya || 0} Ya / ${d.pindah_tidak || 0} Tidak">
                        ${d.pindah_ya || 0} Ya
                    </span>
                </td>
                <td style="${tdR}font-weight:700;color:${pctColor};">${(d.pct_tdk_ditemukan || 0).toFixed(1)}%</td>
                <td style="${tdC}">
                    <span style="font-weight:800;color:${skorColor};font-family:'Outfit',sans-serif;font-size:0.95rem;">${(d.skor_perhatian || 0).toFixed(1)}</span>
                </td>
                <td style="${tdC}">
                    <span style="display:inline-block;padding:0.25rem 0.6rem;border-radius:99px;font-size:0.7rem;font-weight:700;background:${kategoriColor.bg};color:${kategoriColor.text};border:1px solid ${kategoriColor.border};white-space:nowrap;">
                        ${kategoriColor.dot} ${d.kategori_sisir === 'PRIORITAS 1 - SISIR SEGERA' ? 'Sisir Segera' : d.kategori_sisir === 'PRIORITAS 2 - PERLU CEK' ? 'Perlu Cek' : 'Wajar'}
                    </span>
                </td>
                <td style="${tdL}font-size:0.72rem;max-width:150px;overflow:hidden;text-overflow:ellipsis;" title="PPL: ${d.ppl || '-'} | PML: ${d.pml || '-'}">
                    <div style="color:var(--text-primary);font-weight:500;">👤 ${d.ppl || '-'}</div>
                    <div style="color:var(--text-secondary);">🛡️ ${d.pml || '-'}</div>
                </td>
            </tr>`;
        });

        tbody.innerHTML = rows.join('');
        renderPnyKelPagination(total, totalPages);
    }

    // ── Pagination ───────────────────────────────────────────────────────────
    function renderPnyKelPagination(total, totalPages) {
        const infoEl  = document.getElementById('pny-kel-page-info');
        const numsEl  = document.getElementById('pny-kel-page-nums');
        const prevBtn = document.getElementById('pny-kel-btn-prev');
        const nextBtn = document.getElementById('pny-kel-btn-next');

        const start = (pnyKelPage - 1) * PNY_KEL_PER_PAGE + 1;
        const end   = Math.min(pnyKelPage * PNY_KEL_PER_PAGE, total);

        if (infoEl) infoEl.textContent = total > 0 ? `${start}–${end} dari ${total.toLocaleString('id-ID')}` : '0 data';
        if (prevBtn) prevBtn.disabled = pnyKelPage <= 1;
        if (nextBtn) nextBtn.disabled = pnyKelPage >= totalPages;

        if (!numsEl) return;
        numsEl.innerHTML = '';

        const makePage = (p) => {
            const btn = document.createElement('button');
            btn.textContent = p;
            btn.style.cssText = `padding:0.3rem 0.6rem;border-radius:0.5rem;border:1px solid var(--card-border);font-size:0.8rem;cursor:pointer;${p === pnyKelPage ? 'background:var(--primary);color:#fff;font-weight:700;' : 'background:var(--input-bg);color:var(--text-secondary);'}`;
            btn.onclick = () => { pnyKelPage = p; renderPnyKelTable(); };
            numsEl.appendChild(btn);
        };

        if (totalPages <= 7) {
            for (let p = 1; p <= totalPages; p++) makePage(p);
        } else {
            const pages = new Set([1, 2, pnyKelPage - 1, pnyKelPage, pnyKelPage + 1, totalPages - 1, totalPages].filter(p => p >= 1 && p <= totalPages));
            let prev = null;
            [...pages].sort((a, b) => a - b).forEach(p => {
                if (prev && p - prev > 1) {
                    const dots = document.createElement('span');
                    dots.textContent = '…';
                    dots.style.cssText = 'padding:0.3rem 0.3rem;color:var(--text-secondary);font-size:0.8rem;';
                    numsEl.appendChild(dots);
                }
                makePage(p);
                prev = p;
            });
        }
    }

    window.changePnyKelPage = function (dir) {
        const totalPages = Math.ceil(pnyKelFiltered.length / PNY_KEL_PER_PAGE);
        pnyKelPage = Math.max(1, Math.min(totalPages, pnyKelPage + dir));
        renderPnyKelTable();
    };

    window.togglePenyisiranKelSort = function () {
        pnyKelSortAsc = !pnyKelSortAsc;
        const btn = document.getElementById('pny-kel-sort-dir');
        if (btn) btn.textContent = pnyKelSortAsc ? '↑ ASC' : '↓ DESC';
        window.renderPenyisiranKeluarga();
    };

    // ── Download Excel (.xlsx) ──────────────────────────────────────────────
    window.downloadPenyisiranKeluargaExcel = function () {
        if (!pnyKelFiltered.length) return alert('Tidak ada data penyisiran keluarga untuk diunduh.');
        const exportData = pnyKelFiltered.map((d, i) => ({
            'No': i + 1,
            'Kabupaten': d.kabupaten || '-',
            'Kecamatan': d.kecamatan || '-',
            'Desa / Kelurahan': d.desa_kel || '-',
            'Nama SLS': d.sls || '-',
            'Kode SLS': d.id_sub_sls ? String(d.id_sub_sls) : '-',
            'Total Beban Target': d.target_muatan || 0,
            'Ditemukan': d.realisasi_ditemukan || 0,
            'Keluarga Hilang': d.tidak_ditemukan || 0,
            'Indikasi Pindah (Ya)': d.pindah_ya || 0,
            'Indikasi Pindah (Tidak)': d.pindah_tidak || 0,
            '% Tidak Ditemukan': d.pct_tdk_ditemukan || 0,
            'Skor Perhatian': d.skor_perhatian || 0,
            'Kategori Sisir': d.kategori_sisir || '-',
            'Petugas PPL': d.ppl || '-',
            'Petugas PML': d.pml || '-'
        }));

        if (window.XLSX) {
            const ws = XLSX.utils.json_to_sheet(exportData);
            const wb = XLSX.utils.book_new();
            XLSX.utils.book_append_sheet(wb, ws, "Prioritas_Sisir_Keluarga");
            XLSX.writeFile(wb, `Prioritas_Penyisiran_Keluarga_SLS_${new Date().toISOString().slice(0,10)}.xlsx`);
        } else {
            window.downloadPenyisiranKeluargaCSV();
        }
    };

    // ── Download CSV (.csv) ──────────────────────────────────────────────────
    window.downloadPenyisiranKeluargaCSV = function () {
        if (!pnyKelFiltered.length) return alert('Tidak ada data penyisiran keluarga untuk diunduh.');
        const headers = ['No','Kabupaten','Kecamatan','Desa / Kelurahan','Nama SLS','Kode SLS','Total Beban Target','Ditemukan','Keluarga Hilang','Indikasi Pindah Ya','Indikasi Pindah Tidak','% Tidak Ditemukan','Skor Perhatian','Kategori Sisir','Petugas PPL','Petugas PML'];
        const keys = ['kabupaten','kecamatan','desa_kel','sls','id_sub_sls','target_muatan','realisasi_ditemukan','tidak_ditemukan','pindah_ya','pindah_tidak','pct_tdk_ditemukan','skor_perhatian','kategori_sisir','ppl','pml'];
        
        let csvContent = '\uFEFF' + headers.map(h => `"${h.replace(/"/g, '""')}"`).join(',') + '\r\n';
        pnyKelFiltered.forEach((d, i) => {
            const rowValues = [i + 1, ...keys.map(k => {
                let v = d[k];
                if (v === null || v === undefined) v = '';
                v = String(v).replace(/(\r\n|\n|\r)/g, ' ').replace(/"/g, '""');
                return `"${v}"`;
            })];
            csvContent += rowValues.join(',') + '\r\n';
        });

        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = `Prioritas_Penyisiran_Keluarga_SLS_${new Date().toISOString().slice(0,10)}.csv`;
        a.click();
        URL.revokeObjectURL(a.href);
    };

    // Auto init if already in active view
    if (document.readyState === 'complete') {
        window.initPenyisiranKeluarga();
    } else {
        window.addEventListener('DOMContentLoaded', window.initPenyisiranKeluarga);
    }
})();
