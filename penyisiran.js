// ========================================================
// penyisiran.js - Menu Penyisiran Bangunan Usaha per SubSLS
// ========================================================

(function () {
    let pnyFiltered = [];
    let pnyPage = 1;
    const PNY_PER_PAGE = 50;
    let pnySortAsc = false; // DESC by default

    // ── Init saat tab dibuka ─────────────────────────────────────────────────
    window.initPenyisiran = function () {
        const data = window.PENYISIRAN_DATA;
        if (!data || data.length === 0) return;

        // Isi dropdown Kab
        const kabSel = document.getElementById('pny-filter-kab');
        if (kabSel && kabSel.options.length === 1) {
            const kabList = [...new Set(data.map(d => d.kabupaten))].sort();
            kabList.forEach(k => {
                const opt = document.createElement('option');
                opt.value = k;
                opt.textContent = k;
                kabSel.appendChild(opt);
            });
        }

        window.renderPenyisiran();
    };

    // ── Render ───────────────────────────────────────────────────────────────
    window.renderPenyisiran = function () {
        const data = window.PENYISIRAN_DATA;
        if (!data) return;

        const search   = (document.getElementById('pny-search')?.value || '').toLowerCase();
        const kab      = document.getElementById('pny-filter-kab')?.value || '';
        const kategori = document.getElementById('pny-filter-kategori')?.value || '';
        const sortKey  = document.getElementById('pny-sort-by')?.value || 'skor_perhatian';

        // Filter
        pnyFiltered = data.filter(d => {
            if (kab && d.kabupaten !== kab) return false;
            if (kategori && d.kategori_sisir !== kategori) return false;
            if (search) {
                const haystack = [d.kabupaten, d.kecamatan, d.desa_kel, d.sls, d.sub_sls, d.id_sub_sls].join(' ').toLowerCase();
                if (!haystack.includes(search)) return false;
            }
            return true;
        });

        // Sort
        pnyFiltered.sort((a, b) => {
            const va = a[sortKey] ?? 0;
            const vb = b[sortKey] ?? 0;
            return pnySortAsc ? va - vb : vb - va;
        });

        pnyPage = 1;
        updatePnySummaryCards();
        renderPnyTable();
    };

    // ── Summary cards (based on full filtered set) ───────────────────────────
    function updatePnySummaryCards() {
        const totalSubsls = pnyFiltered.length;
        const totalUsaha  = pnyFiltered.reduce((s, d) => s + (d.total_usaha || 0), 0);
        const totalTdk    = pnyFiltered.reduce((s, d) => s + (d.tidak_ditemukan || 0), 0);
        const p1 = pnyFiltered.filter(d => d.kategori_sisir === 'PRIORITAS 1 - SISIR SEGERA').length;
        const p2 = pnyFiltered.filter(d => d.kategori_sisir === 'PRIORITAS 2 - PERLU CEK').length;
        const p3 = pnyFiltered.filter(d => d.kategori_sisir === 'PRIORITAS 3 - WAJAR').length;
        const pctTdk = totalUsaha > 0 ? ((totalTdk / totalUsaha) * 100).toFixed(1) : 0;

        setText('pny-total-subsls', totalSubsls.toLocaleString('id-ID'));
        setText('pny-total-usaha', totalUsaha.toLocaleString('id-ID'));
        setText('pny-total-tdk', totalTdk.toLocaleString('id-ID'));
        setText('pny-pct-tdk', pctTdk + '% dari total usaha');
        setText('pny-p1', p1.toLocaleString('id-ID'));
        setText('pny-p2', p2.toLocaleString('id-ID'));
        setText('pny-p3', p3.toLocaleString('id-ID'));
        setText('pny-count', totalSubsls.toLocaleString('id-ID') + ' SubSLS');
    }

    function setText(id, val) {
        const el = document.getElementById(id);
        if (el) el.textContent = val;
    }

    // ── Render Table ─────────────────────────────────────────────────────────
    function renderPnyTable() {
        const tbody = document.getElementById('penyisiran-tbody');
        if (!tbody) return;

        const total = pnyFiltered.length;
        const totalPages = Math.ceil(total / PNY_PER_PAGE);
        const start = (pnyPage - 1) * PNY_PER_PAGE;
        const pageData = pnyFiltered.slice(start, start + PNY_PER_PAGE);

        if (pageData.length === 0) {
            tbody.innerHTML = '<tr><td colspan="13" style="text-align:center;padding:2rem;color:var(--text-secondary);">Tidak ada data yang sesuai filter.</td></tr>';
            renderPnyPagination(total, totalPages);
            return;
        }

        const tdR = 'padding:0.5rem 0.75rem;font-size:0.82rem;text-align:right;border-bottom:1px solid var(--card-border);';
        const tdL = 'padding:0.5rem 0.75rem;font-size:0.82rem;text-align:left;border-bottom:1px solid var(--card-border);';
        const tdC = 'padding:0.5rem 0.75rem;font-size:0.82rem;text-align:center;border-bottom:1px solid var(--card-border);';

        const rows = pageData.map((d, i) => {
            const rank = start + i + 1;
            const kategoriColor = d.kategori_sisir === 'PRIORITAS 1 - SISIR SEGERA'
                ? { bg: 'rgba(239,68,68,0.08)', text: '#dc2626', dot: '🔴' }
                : d.kategori_sisir === 'PRIORITAS 2 - PERLU CEK'
                ? { bg: 'rgba(245,158,11,0.08)', text: '#d97706', dot: '🟡' }
                : { bg: 'rgba(34,197,94,0.06)', text: '#16a34a', dot: '🟢' };

            const rowBg = d.kategori_sisir === 'PRIORITAS 1 - SISIR SEGERA' ? 'background:rgba(239,68,68,0.035);' : '';

            const skorColor = d.skor_perhatian >= 60 ? '#dc2626'
                : d.skor_perhatian >= 40 ? '#d97706'
                : '#16a34a';

            const pctSelesaiColor = d.pct_selesai >= 80 ? '#16a34a'
                : d.pct_selesai >= 40 ? '#d97706'
                : '#dc2626';

            const tdkNum = d.tidak_ditemukan > 0
                ? `<span style="color:#ef4444;font-weight:700;">${d.tidak_ditemukan.toLocaleString('id-ID')}</span>`
                : `<span style="color:var(--text-secondary);">0</span>`;

            return `<tr style="${rowBg}" onmouseenter="this.style.background='var(--hover-bg)'" onmouseleave="this.style.background='${d.kategori_sisir === 'PRIORITAS 1 - SISIR SEGERA' ? 'rgba(239,68,68,0.035)' : ''}'">
                <td style="${tdC}color:var(--text-secondary);font-size:0.75rem;">${rank}</td>
                <td style="${tdL}font-weight:600;white-space:nowrap;">${d.kabupaten || '-'}</td>
                <td style="${tdL}color:var(--text-secondary);white-space:nowrap;">${d.kecamatan || '-'}</td>
                <td style="${tdL}color:var(--text-secondary);white-space:nowrap;max-width:180px;overflow:hidden;text-overflow:ellipsis;" title="${d.desa_kel || ''}">${d.desa_kel || '-'}</td>
                <td style="${tdL}">
                    <div style="font-weight:600;font-size:0.8rem;">${d.sls || '-'}</div>
                    <div style="font-size:0.72rem;color:var(--text-secondary);">${d.sub_sls !== d.sls ? d.sub_sls : ''}</div>
                    <div style="font-size:0.68rem;color:var(--text-secondary);font-family:monospace;">${d.id_sub_sls || ''}</div>
                </td>
                <td style="${tdR}font-weight:700;">${(d.total_usaha || 0).toLocaleString('id-ID')}</td>
                <td style="${tdR}color:#16a34a;">${(d.ditemukan || 0).toLocaleString('id-ID')}</td>
                <td style="${tdR}">${tdkNum}</td>
                <td style="${tdR}color:var(--text-secondary);">${(d.tutup || 0).toLocaleString('id-ID')}</td>
                <td style="${tdR}color:var(--text-secondary);">${(d.belum_terdata || 0).toLocaleString('id-ID')}</td>
                <td style="${tdR}font-weight:700;color:${pctSelesaiColor};">${(d.pct_selesai || 0).toFixed(1)}%</td>
                <td style="${tdC}">
                    <span style="font-weight:800;color:${skorColor};font-family:'Outfit',sans-serif;">${(d.skor_perhatian || 0).toFixed(1)}</span>
                </td>
                <td style="${tdC}">
                    <span style="display:inline-block;padding:0.2rem 0.6rem;border-radius:99px;font-size:0.7rem;font-weight:700;background:${kategoriColor.bg};color:${kategoriColor.text};white-space:nowrap;">
                        ${kategoriColor.dot} ${d.kategori_sisir === 'PRIORITAS 1 - SISIR SEGERA' ? 'Sisir Segera' : d.kategori_sisir === 'PRIORITAS 2 - PERLU CEK' ? 'Perlu Cek' : 'Wajar'}
                    </span>
                </td>
            </tr>`;
        });

        tbody.innerHTML = rows.join('');
        renderPnyPagination(total, totalPages);
    }

    // ── Pagination ───────────────────────────────────────────────────────────
    function renderPnyPagination(total, totalPages) {
        const infoEl  = document.getElementById('pny-page-info');
        const numsEl  = document.getElementById('pny-page-nums');
        const prevBtn = document.getElementById('pny-btn-prev');
        const nextBtn = document.getElementById('pny-btn-next');

        const start = (pnyPage - 1) * PNY_PER_PAGE + 1;
        const end   = Math.min(pnyPage * PNY_PER_PAGE, total);

        if (infoEl) infoEl.textContent = total > 0 ? `${start}–${end} dari ${total.toLocaleString('id-ID')}` : '0 data';
        if (prevBtn) prevBtn.disabled = pnyPage <= 1;
        if (nextBtn) nextBtn.disabled = pnyPage >= totalPages;

        if (!numsEl) return;
        numsEl.innerHTML = '';

        const makePage = (p) => {
            const btn = document.createElement('button');
            btn.textContent = p;
            btn.style.cssText = `padding:0.3rem 0.6rem;border-radius:0.5rem;border:1px solid var(--card-border);font-size:0.8rem;cursor:pointer;${p === pnyPage ? 'background:var(--primary);color:#fff;font-weight:700;' : 'background:var(--input-bg);color:var(--text-secondary);'}`;
            btn.onclick = () => { pnyPage = p; renderPnyTable(); };
            numsEl.appendChild(btn);
        };

        if (totalPages <= 7) {
            for (let p = 1; p <= totalPages; p++) makePage(p);
        } else {
            const pages = new Set([1, 2, pnyPage - 1, pnyPage, pnyPage + 1, totalPages - 1, totalPages].filter(p => p >= 1 && p <= totalPages));
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

    window.changePnyPage = function (dir) {
        const totalPages = Math.ceil(pnyFiltered.length / PNY_PER_PAGE);
        pnyPage = Math.max(1, Math.min(totalPages, pnyPage + dir));
        renderPnyTable();
    };

    window.togglePenyisiranSort = function () {
        pnySortAsc = !pnySortAsc;
        const btn = document.getElementById('pny-sort-dir');
        if (btn) btn.textContent = pnySortAsc ? '↑ ASC' : '↓ DESC';
        window.renderPenyisiran();
    };

    // ── Download CSV ─────────────────────────────────────────────────────────
    window.downloadPenyisiranCSV = function () {
        if (!pnyFiltered.length) return;
        const headers = ['kabupaten','kecamatan','desa_kel','sls','sub_sls','id_sub_sls','total_usaha','prelist','tambahan','ditemukan','baru','tidak_ditemukan','tutup','belum_terdata','pct_tdk_ditemukan','pct_selesai','pct_belum_terdata','skor_perhatian','kategori_sisir'];
        const rows = [headers.join(',')];
        pnyFiltered.forEach(d => {
            rows.push(headers.map(h => {
                const v = d[h] ?? '';
                return String(v).includes(',') ? `"${v}"` : v;
            }).join(','));
        });
        const blob = new Blob([rows.join('\n')], { type: 'text/csv;charset=utf-8;' });
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = `penyisiran_bangunan_${new Date().toISOString().slice(0,10)}.csv`;
        a.click();
    };


    // ── Sub-tab Switcher inside SLS Open ──────────────────────────────────
    window.switchOpenSubslsSubTab = function (subTab) {
        const fullopenDiv  = document.getElementById('open_subsls-sub-fullopen');
        const penyisiranDiv= document.getElementById('open_subsls-sub-penyisiran');
        const btnFullopen  = document.getElementById('open_subsls-sub-btn-fullopen');
        const btnPenyisiran= document.getElementById('open_subsls-sub-btn-penyisiran');

        if (subTab === 'fullopen') {
            if (fullopenDiv) fullopenDiv.style.display = 'block';
            if (penyisiranDiv) penyisiranDiv.style.display = 'none';
            if (btnFullopen) btnFullopen.classList.add('active');
            if (btnPenyisiran) btnPenyisiran.classList.remove('active');
        } else {
            if (fullopenDiv) fullopenDiv.style.display = 'none';
            if (penyisiranDiv) penyisiranDiv.style.display = 'block';
            if (btnFullopen) btnFullopen.classList.remove('active');
            if (btnPenyisiran) btnPenyisiran.classList.add('active');
            if (window.initPenyisiran) window.initPenyisiran();
        }
    };

})();