// ═══════════════════════════════════════════════════════════════════════════
// palu_monitoring.js — Monitoring Harian Per-Petugas Kota Palu
// ═══════════════════════════════════════════════════════════════════════════
(function () {
    const DEADLINE = new Date('2026-07-15T23:59:59');
    const PALU_KAB_CODE = '7271';
    const PALU_KAB_NAME = '[71] PALU';
    let _showAllDates = false; // toggle history columns

    function fmt(n) { if (n == null || isNaN(n)) return '0'; return Number(n).toLocaleString('id-ID'); }
    function pct(a, b) { return (!b || b === 0) ? 0 : Math.min(100, (a / b) * 100); }
    function toDateStr(d) { return d.toISOString().slice(0, 10); }
    function daysUntilDeadline() { return Math.max(0, Math.ceil((DEADLINE - new Date()) / 86400000)); }

    function getPaluIpas(surveyType) {
        const data = (window.IPAS_DATA || {})[surveyType] || [];
        return data.find(d => (d.kabupaten||'').includes('PALU')) || null;
    }
    function getPaluPetugasEmails() {
        const regionMap = window.PETUGAS_REGION_MAP || {};
        const s = new Set();
        for (const [email, sls] of Object.entries(regionMap))
            if (Array.isArray(sls) && sls.some(x => String(x).startsWith(PALU_KAB_CODE)))
                s.add(email.toLowerCase());
        return s;
    }

    // ── Build pivot data from PETUGAS_DAILY_PALU ────────────────────────────
    function getPivotData() {
        const daily = window.PETUGAS_DAILY_PALU || {};
        const paluEmails = getPaluPetugasEmails();
        const progressMap = window.PETUGAS_PROGRESS_MAP || {};
        const users = window.PETUGAS_USERS || {};

        // Get current totals from fast_petugas_progress
        const curTotals = {};
        const traverse = (obj) => {
            for (const [k, v] of Object.entries(obj)) {
                if (v && typeof v === 'object' && 'target' in v) {
                    curTotals[k.toLowerCase()] = {
                        target: v.target || 0,
                        selesai: (v.submitted_pencacah || 0) + (v.approved || 0),
                        name: users[k] || users[k.split('@')[0]] || k.split('@')[0]
                    };
                } else if (v && typeof v === 'object') { traverse(v); }
            }
        };
        traverse(progressMap);

        // Collect all snapshot dates
        const allDatesSet = new Set();
        for (const d of Object.values(daily)) Object.keys(d.snapshots || {}).forEach(dt => allDatesSet.add(dt));
        const allDates = [...allDatesSet].sort();

        // Build rows
        const rows = [];
        const emails = new Set([...paluEmails, ...Object.keys(daily)]);
        for (const email of emails) {
            const snap = daily[email] || {};
            const cur = curTotals[email] || {};
            const name = snap.name || cur.name || email.split('@')[0];
            const target = cur.target || snap.target || 0;
            const selesaiNow = cur.selesai || 0;
            const sisa = Math.max(0, target - selesaiNow);
            const pctNow = pct(selesaiNow, target);
            const hariLeft = daysUntilDeadline();
            const perHari = hariLeft > 0 ? Math.ceil(sisa / hariLeft) : sisa;
            const snapshots = snap.snapshots || {};
            // Compute daily deltas: for each date, delta = snapshots[date] - snapshots[prevDate]
            const deltas = {};
            for (let i = 0; i < allDates.length; i++) {
                const d = allDates[i];
                const prev = i > 0 ? (snapshots[allDates[i-1]] || 0) : 0;
                const cur_val = snapshots[d];
                if (cur_val !== undefined) deltas[d] = cur_val - prev;
            }
            rows.push({ email, name, target, selesaiNow, sisa, pctNow, perHari, snapshots, deltas });
        }
        rows.sort((a, b) => a.pctNow - b.pctNow);
        return { rows, allDates };
    }

    // ── Petugas Pivot Table ─────────────────────────────────────────────────
    function renderPetugasTable(surveyType) {
        const { rows, allDates } = getPivotData();
        if (rows.length === 0) return '<div style="padding:2rem;text-align:center;color:var(--text-secondary);">Data tidak ditemukan.</div>';

        const today = toDateStr(new Date());
        // Dates to show: always show today. History = toggle
        const visibleDates = _showAllDates ? allDates : allDates.filter(d => d === today);
        const hiddenCount = allDates.filter(d => d !== today).length;

        const thBase = 'padding:0.5rem 0.6rem;font-size:0.72rem;font-weight:700;color:#fff;white-space:nowrap;';
        const thDate = 'padding:0.5rem 0.6rem;font-size:0.72rem;font-weight:700;color:#fff;white-space:nowrap;text-align:center;min-width:80px;';

        // Date column headers
        const dateHeaders = visibleDates.map(d => {
            const dObj = new Date(d + 'T00:00:00');
            const label = dObj.toLocaleDateString('id-ID', { day: 'numeric', month: 'short' });
            const isToday = d === today;
            return '<th style="' + thDate + (isToday ? 'background:rgba(99,102,241,0.3);' : '') + '">' +
                label + (isToday ? '<br><span style="font-size:0.6rem;font-weight:400;">hari ini</span>' : '<br><span style="font-size:0.6rem;font-weight:400;">delta</span>') +
                '</th>';
        }).join('');

        const tableRows = rows.map((p, idx) => {
            const capVal = p.pctNow;
            const barColor = capVal < 15 ? '#dc2626' : capVal < 30 ? '#f59e0b' : '#22c55e';
            let badge = capVal < 15
                ? '<span style="font-size:0.6rem;color:#dc2626;border:1px solid #fca5a5;border-radius:0.3rem;padding:0.05rem 0.35rem;background:#fef2f2;">🔴 KRITIS</span>'
                : capVal < 30
                ? '<span style="font-size:0.6rem;color:#d97706;border:1px solid #fcd34d;border-radius:0.3rem;padding:0.05rem 0.35rem;background:#fffbeb;">🟡 KEJAR</span>'
                : '<span style="font-size:0.6rem;color:#16a34a;border:1px solid #86efac;border-radius:0.3rem;padding:0.05rem 0.35rem;background:#f0fdf4;">🟢 OK</span>';
            const bar = '<div style="width:100%;background:var(--card-border);border-radius:9999px;height:4px;margin-top:2px;"><div style="width:' + Math.min(100, capVal).toFixed(1) + '%;background:' + barColor + ';height:4px;border-radius:9999px;"></div></div>';
            const rowBg = idx % 2 === 0 ? '' : 'rgba(99,102,241,0.03)';
            const td = 'padding:0.45rem 0.6rem;font-size:0.78rem;border-bottom:1px solid var(--card-border);text-align:right;vertical-align:middle;';
            const tdL = 'padding:0.45rem 0.6rem;font-size:0.78rem;border-bottom:1px solid var(--card-border);text-align:left;vertical-align:middle;';
            const tdC = 'padding:0.45rem 0.6rem;font-size:0.78rem;border-bottom:1px solid var(--card-border);text-align:center;vertical-align:middle;';

            // Date columns: show delta (how many submitted that day) or cumulative for today
            const dateCells = visibleDates.map(d => {
                const isToday = d === today;
                const snapVal = p.snapshots[d]; // cumulative as of that date
                const delta = p.deltas[d];

                if (isToday) {
                    // Show cumulative total (selesai saat ini)
                    const val = p.selesaiNow;
                    const color = capVal < 15 ? '#dc2626' : capVal < 30 ? '#f59e0b' : '#22c55e';
                    return '<td style="' + tdC + 'background:rgba(99,102,241,0.06);font-weight:700;color:' + color + ';">' + fmt(val) + '</td>';
                } else {
                    // Show delta for that historical day
                    if (delta === undefined || snapVal === undefined) {
                        return '<td style="' + tdC + 'color:var(--text-secondary);">—</td>';
                    }
                    const dColor = delta > 0 ? '#16a34a' : delta < 0 ? '#dc2626' : 'var(--text-secondary)';
                    const dSign = delta > 0 ? '+' : '';
                    return '<td style="' + tdC + '">' +
                        '<div style="font-weight:700;color:' + dColor + ';">' + dSign + fmt(delta) + '</div>' +
                        '<div style="font-size:0.63rem;color:var(--text-secondary);">' + fmt(snapVal) + '</div>' +
                        '</td>';
                }
            }).join('');

            return '<tr style="background:' + rowBg + '">' +
                '<td style="' + tdL + 'color:var(--text-secondary);font-weight:600;">' + (idx+1) + '</td>' +
                '<td style="' + tdL + '"><div style="font-weight:600;color:var(--text-primary);font-size:0.8rem;">' + p.name + '</div><div style="font-size:0.63rem;color:var(--text-secondary);">' + p.email + '</div></td>' +
                '<td style="' + td + '">' + fmt(p.target) + '</td>' +
                dateCells +
                '<td style="' + td + '"><div style="font-weight:700;color:' + barColor + ';">' + capVal.toFixed(1) + '%</div>' + bar + '</td>' +
                '<td style="' + td + 'color:#f59e0b;font-weight:700;">' + fmt(p.perHari) + '/hr</td>' +
                '<td style="' + tdL + '">' + badge + '</td>' +
            '</tr>';
        }).join('');

        const totTarget = rows.reduce((a, b) => a + b.target, 0);
        const totSub = rows.reduce((a, b) => a + b.selesaiNow, 0);
        const totDateCells = visibleDates.map(d => {
            if (d === today) {
                return '<td style="padding:0.6rem;text-align:center;font-weight:700;color:#22c55e;">' + fmt(totSub) + '</td>';
            }
            const totDelta = rows.reduce((a, b) => a + (b.deltas[d] || 0), 0);
            return '<td style="padding:0.6rem;text-align:center;font-weight:700;color:' + (totDelta > 0 ? '#22c55e' : '#dc2626') + ';">' + (totDelta >= 0 ? '+' : '') + fmt(totDelta) + '</td>';
        }).join('');

        const toggleLabel = _showAllDates
            ? '🙈 Sembunyikan history (' + hiddenCount + ' tgl)'
            : '📅 Tampilkan history (' + hiddenCount + ' tgl)';

        return `
        <div style="background:var(--card-bg);border:1px solid var(--card-border);border-radius:1rem;overflow:hidden;margin-bottom:1.25rem;">
            <div style="padding:0.9rem 1.25rem;border-bottom:1px solid var(--card-border);display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:0.5rem;">
                <div style="font-weight:700;font-size:0.9rem;color:var(--text-primary);">
                    👥 Progress Petugas Palu
                    <span style="font-size:0.75rem;font-weight:400;color:var(--text-secondary);margin-left:0.5rem;">(capaian terendah di atas · ${rows.length} petugas)</span>
                </div>
                <button onclick="window.togglePaluHistory()" style="padding:0.35rem 0.8rem;border-radius:0.6rem;border:1px solid var(--card-border);font-family:Outfit,sans-serif;font-size:0.75rem;font-weight:600;cursor:pointer;background:transparent;color:var(--text-secondary);">
                    ${toggleLabel}
                </button>
            </div>
            <div style="overflow-x:auto;max-height:480px;overflow-y:auto;">
                <table style="width:100%;border-collapse:collapse;">
                    <thead style="position:sticky;top:0;z-index:2;">
                        <tr style="background:linear-gradient(135deg,#1e3a5f,#1a3050);">
                            <th style="${thBase}text-align:left;">No</th>
                            <th style="${thBase}text-align:left;">Petugas</th>
                            <th style="${thBase}text-align:right;">Target</th>
                            ${dateHeaders}
                            <th style="${thBase}text-align:right;">% Capaian</th>
                            <th style="${thBase}text-align:right;">Wajib/Hari</th>
                            <th style="${thBase}text-align:left;">Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${tableRows}
                        <tr style="background:rgba(99,102,241,0.08);font-weight:700;position:sticky;bottom:0;">
                            <td colspan="3" style="padding:0.6rem;font-size:0.78rem;color:var(--text-primary);">TOTAL (${rows.length})</td>
                            ${totDateCells}
                            <td style="padding:0.6rem;text-align:right;font-size:0.78rem;">${pct(totSub,totTarget).toFixed(1)}%</td>
                            <td colspan="2"></td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>`;
    }

    // ── Summary Cards ────────────────────────────────────────────────────────
    function renderSummaryCards(ipasData, surveyType) {
        const noData = !ipasData;
        const total = noData ? 0 : (ipasData.total_prelist || 0);
        const submitted = noData ? 0 : (ipasData.total_submitted || 0);
        const sisa = Math.max(0, total - submitted);
        const capaian = pct(submitted, total);
        const hariLeft = daysUntilDeadline();
        const targetPerHari = total > 0 && hariLeft > 0 ? Math.ceil(sisa / hariLeft) : 0;
        const dailyStats = (window.DAILY_SUBMISSION_STATS || [])
            .filter(s => s.kab_name === 'PALU' && s.survey_type === (surveyType === 'se_ub' ? 'se_ub' : 'se_umum'));
        const grouped = {};
        dailyStats.forEach(s => { grouped[s.date] = (grouped[s.date]||0) + s.count; });
        const sortedDates = Object.keys(grouped).sort();
        const last3 = sortedDates.slice(-3).map(d => grouped[d]||0);
        const avg3 = last3.length > 0 ? Math.round(last3.reduce((a,b)=>a+b,0)/last3.length) : 0;
        const projDays = avg3 > 0 ? Math.ceil(sisa / avg3) : 999;
        const projDate = new Date(); projDate.setDate(projDate.getDate() + projDays);
        const projDateStr = projDate.toLocaleDateString('id-ID', { day: 'numeric', month: 'long' });
        const onTrack = targetPerHari > 0 && avg3 >= targetPerHari;
        const sColor = noData ? '#6366f1' : capaian >= 50 ? '#16a34a' : capaian >= 25 ? '#d97706' : '#dc2626';
        const projColor = onTrack ? '#16a34a' : '#dc2626';
        return `
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:0.75rem;margin-bottom:1.25rem;">
            <div style="background:var(--card-bg);border:1px solid var(--card-border);border-radius:0.75rem;padding:1rem;border-left:3px solid ${sColor};">
                <div style="font-size:0.68rem;color:var(--text-secondary);font-weight:600;text-transform:uppercase;">Capaian Palu</div>
                <div style="font-size:1.8rem;font-weight:800;color:${sColor};">${noData?'—':capaian.toFixed(1)+'%'}</div>
                <div style="font-size:0.72rem;color:var(--text-secondary);">${noData?'data IPAS belum tersedia':fmt(submitted)+'/'+fmt(total)}</div>
            </div>
            <div style="background:var(--card-bg);border:1px solid var(--card-border);border-radius:0.75rem;padding:1rem;border-left:3px solid #3b82f6;">
                <div style="font-size:0.68rem;color:var(--text-secondary);font-weight:600;text-transform:uppercase;">Sisa Usaha</div>
                <div style="font-size:1.8rem;font-weight:800;color:#3b82f6;">${noData?'—':fmt(sisa)}</div>
                <div style="font-size:0.72rem;color:var(--text-secondary);">Sisa ${hariLeft} hari</div>
            </div>
            <div style="background:var(--card-bg);border:1px solid var(--card-border);border-radius:0.75rem;padding:1rem;border-left:3px solid #f59e0b;">
                <div style="font-size:0.68rem;color:var(--text-secondary);font-weight:600;text-transform:uppercase;">Target/Hari</div>
                <div style="font-size:1.8rem;font-weight:800;color:#f59e0b;">${targetPerHari>0?fmt(targetPerHari):'—'}</div>
                <div style="font-size:0.72rem;color:var(--text-secondary);">Avg 3 hari: ${fmt(avg3)}/hari</div>
            </div>
            <div style="background:var(--card-bg);border:1px solid var(--card-border);border-radius:0.75rem;padding:1rem;border-left:3px solid ${projColor};">
                <div style="font-size:0.68rem;color:var(--text-secondary);font-weight:600;text-transform:uppercase;">Proyeksi Selesai</div>
                <div style="font-size:1.2rem;font-weight:800;color:${projColor};line-height:1.2;">${projDays<200?projDateStr:'—'}</div>
                <div style="font-size:0.72rem;color:${projColor};font-weight:600;">${noData?'':onTrack?'✅ On track':'⚠️ Tidak selesai tgl 15'}</div>
            </div>
        </div>`;
    }

    function renderSurveyToggle(active) {
        const base = 'padding:0.4rem 0.9rem;border-radius:0.6rem;border:1px solid var(--card-border);font-family:Outfit,sans-serif;font-size:0.78rem;font-weight:600;cursor:pointer;';
        return `<div style="display:flex;gap:0.5rem;margin-bottom:1rem;">
            <button onclick="window.renderPaluMonitoring('se_umum')" style="${base}${active==='se_umum'?'background:linear-gradient(135deg,#6366f1,#4f46e5);color:#fff;':'background:transparent;color:var(--text-secondary);'}">SE Umum</button>
            <button onclick="window.renderPaluMonitoring('se_ub')" style="${base}${active==='se_ub'?'background:linear-gradient(135deg,#6366f1,#4f46e5);color:#fff;':'background:transparent;color:var(--text-secondary);'}">SE UB</button>
        </div>`;
    }

    window.togglePaluHistory = function() {
        _showAllDates = !_showAllDates;
        const container = document.getElementById('palu-monitoring-container');
        if (!container) return;
        const tableDiv = container.querySelector('[data-palu-table]');
        if (tableDiv) tableDiv.outerHTML = renderPetugasTable(window._paluSurveyType || 'se_umum');
        else window.renderPaluMonitoring(window._paluSurveyType || 'se_umum');
    };

    window.renderPaluMonitoring = function(surveyType) {
        surveyType = surveyType || 'se_umum';
        window._paluSurveyType = surveyType;
        const container = document.getElementById('palu-monitoring-container');
        if (!container) return;
        const ipasData = getPaluIpas(surveyType);
        container.innerHTML =
            renderSurveyToggle(surveyType) +
            renderSummaryCards(ipasData, surveyType) +
            '<div data-palu-table>' + renderPetugasTable(surveyType) + '</div>';
    };

    window.initPaluMonitoring = function() {
        window.renderPaluMonitoring('se_umum');
    };
})();
