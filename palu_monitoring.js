// ═══════════════════════════════════════════════════════════════════════════
// palu_monitoring.js — Monitoring Khusus Kota Palu (sub-tab Progres Petugas)
// ═══════════════════════════════════════════════════════════════════════════

(function () {
    const DEADLINE = new Date('2026-07-15T23:59:59');
    const PALU_KAB_CODE = '7271';
    const PALU_KAB_NAME = '[71] PALU';

    function fmt(n) {
        if (n == null || isNaN(n)) return '0';
        return Number(n).toLocaleString('id-ID');
    }
    function pct(a, b) { return (!b || b === 0) ? 0 : Math.min(100, (a / b) * 100); }
    function toDateStr(d) { return d.toISOString().slice(0, 10); }

    function daysUntilDeadline() {
        const diff = DEADLINE - new Date();
        return Math.max(0, Math.ceil(diff / (1000 * 60 * 60 * 24)));
    }

    // Cari data IPAS Palu — coba beberapa format nama
    function getPaluIpas(surveyType) {
        const ipas = window.IPAS_DATA || {};
        const data = ipas[surveyType] || [];
        return data.find(d =>
            d.kabupaten === PALU_KAB_NAME ||
            d.kabupaten === 'PALU' ||
            (d.kabupaten || '').includes('PALU')
        ) || null;
    }

    function getPaluPetugasEmails() {
        const regionMap = window.PETUGAS_REGION_MAP || {};
        const paluEmails = new Set();
        for (const [email, slsList] of Object.entries(regionMap)) {
            if (Array.isArray(slsList) && slsList.some(s => String(s).startsWith(PALU_KAB_CODE))) {
                paluEmails.add(email.toLowerCase());
            }
        }
        return paluEmails;
    }

    function getPaluPetugasData() {
        const paluEmails = getPaluPetugasEmails();
        const progressMap = window.PETUGAS_PROGRESS_MAP || {};
        const users = window.PETUGAS_USERS || {};
        let all = [];
        const traverse = (obj) => {
            for (const [key, val] of Object.entries(obj)) {
                if (val && typeof val === 'object' && 'target' in val) {
                    if (paluEmails.has(key.toLowerCase())) {
                        const name = users[key] || users[key.split('@')[0]] || key.split('@')[0];
                        const total = val.target || 0;
                        const submitted = (val.submitted_pencacah || 0) + (val.approved || 0);
                        const sisa = Math.max(0, total - submitted);
                        const pctCap = pct(submitted, total);
                        const hariLeft = daysUntilDeadline();
                        const perHari = hariLeft > 0 ? Math.ceil(sisa / hariLeft) : sisa;
                        all.push({ email: key, name, total, submitted,
                            selesai: val.approved || 0, inProgress: val.submitted_pencacah || 0,
                            sisa, pctCap, perHari });
                    }
                } else if (val && typeof val === 'object') {
                    traverse(val);
                }
            }
        };
        traverse(progressMap);
        all.sort((a, b) => a.pctCap - b.pctCap);
        return all;
    }

    function getPaluDailyStats(surveyType) {
        const stats = window.DAILY_SUBMISSION_STATS || [];
        const sType = surveyType === 'se_ub' ? 'se_ub' : 'se_umum';
        const filtered = stats.filter(s => s.kab_name === 'PALU' && s.survey_type === sType);
        const grouped = {};
        filtered.forEach(s => {
            if (!grouped[s.date]) grouped[s.date] = 0;
            grouped[s.date] += s.count || 0;
        });
        return grouped;
    }

    // ── Petugas Table (PERTAMA - lebih urgent) ───────────────────────────────
    function renderPetugasTable() {
        const petugasList = getPaluPetugasData();
        if (petugasList.length === 0) {
            return '<div style="background:var(--card-bg);border:1px solid var(--card-border);border-radius:1rem;padding:2rem;text-align:center;color:var(--text-secondary);margin-bottom:1.25rem;">Data petugas Palu tidak ditemukan.</div>';
        }
        const thBase = 'padding:0.5rem 0.6rem;font-size:0.72rem;font-weight:700;color:#fff;white-space:nowrap;';
        const rows = petugasList.map((p, idx) => {
            const capVal = p.pctCap;
            let badge;
            if (capVal < 15) badge = '<span style="background:#fef2f2;color:#dc2626;border:1px solid #fca5a5;border-radius:0.4rem;padding:0.1rem 0.4rem;font-size:0.65rem;font-weight:700;">🔴 KRITIS</span>';
            else if (capVal < 30) badge = '<span style="background:#fffbeb;color:#d97706;border:1px solid #fcd34d;border-radius:0.4rem;padding:0.1rem 0.4rem;font-size:0.65rem;font-weight:700;">🟡 KEJAR</span>';
            else badge = '<span style="background:#f0fdf4;color:#16a34a;border:1px solid #86efac;border-radius:0.4rem;padding:0.1rem 0.4rem;font-size:0.65rem;font-weight:700;">🟢 OK</span>';
            const barColor = capVal < 15 ? '#dc2626' : capVal < 30 ? '#f59e0b' : '#22c55e';
            const bar = '<div style="width:100%;background:var(--card-border);border-radius:9999px;height:4px;margin-top:2px;"><div style="width:' + Math.min(100, capVal).toFixed(1) + '%;background:' + barColor + ';height:4px;border-radius:9999px;"></div></div>';
            const rowBg = idx % 2 === 0 ? '' : 'rgba(99,102,241,0.03)';
            const td = 'padding:0.45rem 0.6rem;font-size:0.78rem;border-bottom:1px solid var(--card-border);text-align:right;';
            const tdL = 'padding:0.45rem 0.6rem;font-size:0.78rem;border-bottom:1px solid var(--card-border);text-align:left;';
            return '<tr style="background:' + rowBg + '">' +
                '<td style="' + tdL + 'color:var(--text-secondary);font-weight:600;">' + (idx+1) + '</td>' +
                '<td style="' + tdL + '"><div style="font-weight:600;color:var(--text-primary);font-size:0.8rem;">' + p.name + '</div><div style="font-size:0.65rem;color:var(--text-secondary);">' + p.email + '</div></td>' +
                '<td style="' + td + '">' + fmt(p.total) + '</td>' +
                '<td style="' + td + 'color:#22c55e;font-weight:700;">' + fmt(p.submitted) + '</td>' +
                '<td style="' + td + 'color:#3b82f6;">' + fmt(p.sisa) + '</td>' +
                '<td style="' + td + '"><div style="font-weight:700;color:' + barColor + ';">' + capVal.toFixed(1) + '%</div>' + bar + '</td>' +
                '<td style="' + td + 'color:#f59e0b;font-weight:700;">' + fmt(p.perHari) + '/hr</td>' +
                '<td style="' + tdL + '">' + badge + '</td>' +
            '</tr>';
        }).join('');
        const totTarget = petugasList.reduce((a, b) => a + b.total, 0);
        const totSub = petugasList.reduce((a, b) => a + b.submitted, 0);
        const totSisa = petugasList.reduce((a, b) => a + b.sisa, 0);
        return `
        <div style="background:var(--card-bg);border:1px solid var(--card-border);border-radius:1rem;overflow:hidden;margin-bottom:1.25rem;">
            <div style="padding:0.9rem 1.25rem;border-bottom:1px solid var(--card-border);display:flex;justify-content:space-between;align-items:center;">
                <div style="font-weight:700;font-size:0.9rem;color:var(--text-primary);">
                    👥 Petugas Palu <span style="font-size:0.75rem;font-weight:400;color:var(--text-secondary);">(capaian terendah di atas)</span>
                </div>
                <div style="font-size:0.75rem;color:var(--text-secondary);">${petugasList.length} petugas</div>
            </div>
            <div style="overflow-x:auto;max-height:400px;overflow-y:auto;">
                <table style="width:100%;border-collapse:collapse;">
                    <thead style="position:sticky;top:0;z-index:1;">
                        <tr style="background:linear-gradient(135deg,#1e3a5f,#1a3050);">
                            <th style="${thBase}text-align:left;">No</th>
                            <th style="${thBase}text-align:left;">Petugas</th>
                            <th style="${thBase}text-align:right;">Target</th>
                            <th style="${thBase}text-align:right;">Selesai</th>
                            <th style="${thBase}text-align:right;">Sisa</th>
                            <th style="${thBase}text-align:right;">%</th>
                            <th style="${thBase}text-align:right;">Wajib/Hari</th>
                            <th style="${thBase}text-align:left;">Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${rows}
                        <tr style="background:rgba(99,102,241,0.08);font-weight:700;">
                            <td colspan="2" style="padding:0.6rem;font-size:0.78rem;color:var(--text-primary);">TOTAL (${petugasList.length})</td>
                            <td style="padding:0.6rem;text-align:right;font-size:0.78rem;">${fmt(totTarget)}</td>
                            <td style="padding:0.6rem;text-align:right;font-size:0.78rem;color:#22c55e;">${fmt(totSub)}</td>
                            <td style="padding:0.6rem;text-align:right;font-size:0.78rem;color:#3b82f6;">${fmt(totSisa)}</td>
                            <td style="padding:0.6rem;text-align:right;font-size:0.78rem;">${pct(totSub,totTarget).toFixed(1)}%</td>
                            <td colspan="2"></td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>`;
    }

    // ── Daily Tracker Table (KEDUA - di bawah petugas) ───────────────────────
    function renderDailyTable(surveyType) {
        const ipasData = getPaluIpas(surveyType);
        const totalTarget = ipasData ? (ipasData.total_prelist || 0) : 0;
        const totalSubmitted = ipasData ? (ipasData.total_submitted || 0) : 0;
        const sisa = Math.max(0, totalTarget - totalSubmitted);
        const dailyStats = getPaluDailyStats(surveyType);

        const today = new Date(); today.setHours(0,0,0,0);
        const deadline = new Date('2026-07-15T00:00:00');

        const allDates = Object.keys(dailyStats).sort();
        const historyDates = allDates.filter(d => d <= toDateStr(today));

        // Future dates: tomorrow → 15 Jul
        const futureDates = [];
        const cur = new Date(today); cur.setDate(cur.getDate() + 1);
        while (cur <= deadline) { futureDates.push(toDateStr(cur)); cur.setDate(cur.getDate() + 1); }

        // Show last 7 history + today + future
        const showHistory = historyDates.slice(-7);
        const showDates = [...showHistory, toDateStr(today), ...futureDates];

        const hariLeft = daysUntilDeadline();
        const targetPerHari = totalTarget > 0 && hariLeft > 0 ? Math.ceil(sisa / hariLeft) : 0;

        // Avg 3 hari terakhir real data
        const last3 = historyDates.slice(-3).map(d => dailyStats[d] || 0);
        const avg3 = last3.length > 0 ? Math.round(last3.reduce((a,b) => a+b, 0) / last3.length) : 0;

        // Compute running cumulative anchored to IPAS total
        // Strategy: cumulative[today] ≈ totalSubmitted
        // Work backwards for past days, forward for future
        const todayCount = dailyStats[toDateStr(today)] || 0;
        const cumAsOfYesterday = totalSubmitted - todayCount;

        // Build cumulative map for shown dates
        // First compute backwards from yesterday
        const cumMap = {};
        let runBack = cumAsOfYesterday;
        const shownHistory = [...showHistory].reverse();
        shownHistory.forEach(d => {
            cumMap[d] = runBack;
            runBack -= (dailyStats[d] || 0);
        });
        // Today
        cumMap[toDateStr(today)] = totalSubmitted;
        // Future: forward projection
        let runFwd = totalSubmitted;
        futureDates.forEach(d => {
            runFwd += avg3;
            cumMap[d] = runFwd;
        });

        const thStyle = 'padding:0.5rem 0.75rem;font-size:0.75rem;font-weight:700;color:#fff;white-space:nowrap;text-align:center;';
        const thLeftStyle = 'padding:0.5rem 0.75rem;font-size:0.75rem;font-weight:700;color:#fff;white-space:nowrap;text-align:left;';

        let prevCount = null;
        let rows = '';

        showDates.forEach((dateStr, i) => {
            const isToday = dateStr === toDateStr(today);
            const isFuture = dateStr > toDateStr(today);
            const isPast = !isToday && !isFuture;

            const count = isPast ? (dailyStats[dateStr] || 0)
                : isToday ? todayCount
                : avg3;

            const cum = cumMap[dateStr] || 0;
            const pctCum = totalTarget > 0 ? ((cum / totalTarget) * 100).toFixed(2) + '%' : '—';

            // delta vs previous day in table
            const delta = prevCount !== null ? count - prevCount : null;
            const deltaVsTarget = targetPerHari > 0 ? count - targetPerHari : null;

            prevCount = isFuture ? avg3 : count;

            let rowBg = '', countColor = 'var(--text-primary)', statusBadge = '';
            if (isFuture) {
                rowBg = 'rgba(99,102,241,0.04)'; countColor = '#6366f1';
                statusBadge = '<span style="font-size:0.65rem;color:#6366f1;background:rgba(99,102,241,0.1);padding:0.1rem 0.4rem;border-radius:0.3rem;">PROYEKSI</span>';
            } else if (isToday && count === 0) {
                rowBg = 'rgba(245,158,11,0.06)'; countColor = '#d97706';
                statusBadge = '<span style="font-size:0.65rem;color:#d97706;background:rgba(245,158,11,0.1);padding:0.1rem 0.4rem;border-radius:0.3rem;">BELUM DITARIK</span>';
            } else if (targetPerHari > 0 && count >= targetPerHari) {
                rowBg = 'rgba(34,197,94,0.04)'; countColor = '#16a34a';
                statusBadge = '<span style="font-size:0.65rem;color:#16a34a;background:rgba(34,197,94,0.1);padding:0.1rem 0.4rem;border-radius:0.3rem;">✓ TERCAPAI</span>';
            } else if (count > 0) {
                rowBg = 'rgba(239,68,68,0.04)'; countColor = '#dc2626';
                statusBadge = '<span style="font-size:0.65rem;color:#dc2626;background:rgba(239,68,68,0.1);padding:0.1rem 0.4rem;border-radius:0.3rem;">✗ KURANG</span>';
            } else {
                statusBadge = '<span style="font-size:0.65rem;color:var(--text-secondary);padding:0.1rem 0.4rem;">—</span>';
            }

            const dateObj = new Date(dateStr + 'T00:00:00');
            const dateLabel = dateObj.toLocaleDateString('id-ID', { weekday: 'short', day: 'numeric', month: 'short' });
            const dayLabel = isToday ? '<strong style="color:var(--text-primary);">HARI INI (' + dateLabel + ')</strong>' : dateLabel;

            // Delta vs target: green if positive, red if negative
            let deltaVsStr = '—';
            if (deltaVsTarget !== null && (count > 0 || isFuture)) {
                const dColor = deltaVsTarget >= 0 ? '#16a34a' : '#dc2626';
                const dSign = deltaVsTarget >= 0 ? '+' : '';
                deltaVsStr = '<span style="color:' + dColor + ';font-weight:600;">' + dSign + fmt(deltaVsTarget) + '</span>';
            }

            // Delta vs previous day (hari sebelumnya)
            let deltaDayStr = '—';
            if (delta !== null) {
                const dColor2 = delta >= 0 ? '#16a34a' : '#dc2626';
                const dSign2 = delta >= 0 ? '+' : '';
                deltaDayStr = '<span style="color:' + dColor2 + ';">' + dSign2 + fmt(delta) + '</span>';
            }

            const td = 'padding:0.5rem 0.6rem;font-size:0.8rem;border-bottom:1px solid var(--card-border);text-align:center;';
            const tdL = 'padding:0.5rem 0.6rem;font-size:0.8rem;border-bottom:1px solid var(--card-border);text-align:left;';
            rows += '<tr style="background:' + rowBg + '">' +
                '<td style="' + tdL + '">' + dayLabel + '</td>' +
                '<td style="' + td + 'font-weight:700;color:' + countColor + ';">' + fmt(count) + (isFuture ? '<div style="font-size:0.63rem;color:var(--text-secondary);">avg 3hr</div>' : '') + '</td>' +
                '<td style="' + td + '">' + deltaDayStr + '</td>' +
                '<td style="' + td + '">' + deltaVsStr + '</td>' +
                '<td style="' + td + 'font-weight:600;">' + (totalTarget > 0 ? fmt(cum) : '—') + '</td>' +
                '<td style="' + td + '">' + pctCum + '</td>' +
                '<td style="' + tdL + '">' + statusBadge + '</td>' +
            '</tr>';
        });

        const targetInfo = targetPerHari > 0
            ? 'Target/hari: <b>' + fmt(targetPerHari) + '</b> | Rata-rata 3 hari: <b>' + fmt(avg3) + '</b>'
            : 'Rata-rata 3 hari: <b>' + fmt(avg3) + '</b> <span style="color:#d97706;">(target/hari tidak dapat dihitung — data IPAS belum tersedia)</span>';

        return `
        <div style="background:var(--card-bg);border:1px solid var(--card-border);border-radius:1rem;overflow:hidden;">
            <div style="padding:0.9rem 1.25rem;border-bottom:1px solid var(--card-border);display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:0.5rem;">
                <div style="font-weight:700;font-size:0.9rem;color:var(--text-primary);">
                    📅 Tracker Harian — Kemarin s/d 15 Juli
                </div>
                <div style="font-size:0.75rem;color:var(--text-secondary);">${targetInfo}</div>
            </div>
            <div style="overflow-x:auto;">
                <table style="width:100%;border-collapse:collapse;">
                    <thead>
                        <tr style="background:linear-gradient(135deg,#1e3a5f,#1a3050);">
                            <th style="${thLeftStyle}">Tanggal</th>
                            <th style="${thStyle}">Submit Hari Ini</th>
                            <th style="${thStyle}">∆ vs Hari Sebelumnya</th>
                            <th style="${thStyle}">∆ vs Target/Hari</th>
                            <th style="${thStyle}">Kumulatif</th>
                            <th style="${thStyle}">% Capaian</th>
                            <th style="${thLeftStyle}">Status</th>
                        </tr>
                    </thead>
                    <tbody>${rows}</tbody>
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
        const dailyStats = getPaluDailyStats(surveyType);
        const allDates = Object.keys(dailyStats).sort();
        const last3Dates = allDates.slice(-3);
        const avgLast3 = last3Dates.length > 0 ? Math.round(last3Dates.reduce((a, d) => a + (dailyStats[d]||0), 0) / last3Dates.length) : 0;
        const projDays = avgLast3 > 0 ? Math.ceil(sisa / avgLast3) : 999;
        const projDate = new Date(); projDate.setDate(projDate.getDate() + projDays);
        const projDateStr = projDate.toLocaleDateString('id-ID', { day: 'numeric', month: 'long' });
        const onTrack = targetPerHari > 0 && avgLast3 >= targetPerHari;
        const statusColor = noData ? '#6366f1' : (capaian >= 50 ? '#16a34a' : capaian >= 25 ? '#d97706' : '#dc2626');
        const statusText = noData ? '— (data IPAS belum tersedia)' : (capaian >= 50 ? '🟢 AMAN' : capaian >= 25 ? '🟡 WASPADA' : '🔴 KRITIS');
        const projColor = onTrack ? '#16a34a' : '#dc2626';

        return `
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:0.75rem;margin-bottom:1.25rem;">
            <div style="background:var(--card-bg);border:1px solid var(--card-border);border-radius:0.75rem;padding:1rem;border-left:3px solid ${statusColor};">
                <div style="font-size:0.7rem;color:var(--text-secondary);font-weight:600;text-transform:uppercase;">Capaian Palu</div>
                <div style="font-size:1.8rem;font-weight:800;color:${statusColor};">${noData ? '—' : capaian.toFixed(1) + '%'}</div>
                <div style="font-size:0.75rem;color:var(--text-secondary);">${statusText}</div>
                ${!noData ? '<div style="font-size:0.72rem;color:var(--text-secondary);margin-top:2px;">' + fmt(submitted) + ' / ' + fmt(total) + '</div>' : ''}
            </div>
            <div style="background:var(--card-bg);border:1px solid var(--card-border);border-radius:0.75rem;padding:1rem;border-left:3px solid #3b82f6;">
                <div style="font-size:0.7rem;color:var(--text-secondary);font-weight:600;text-transform:uppercase;">Sisa Usaha</div>
                <div style="font-size:1.8rem;font-weight:800;color:#3b82f6;">${noData ? '—' : fmt(sisa)}</div>
                <div style="font-size:0.75rem;color:var(--text-secondary);">Sisa ${hariLeft} hari lagi</div>
            </div>
            <div style="background:var(--card-bg);border:1px solid var(--card-border);border-radius:0.75rem;padding:1rem;border-left:3px solid #f59e0b;">
                <div style="font-size:0.7rem;color:var(--text-secondary);font-weight:600;text-transform:uppercase;">Target/Hari</div>
                <div style="font-size:1.8rem;font-weight:800;color:#f59e0b;">${targetPerHari > 0 ? fmt(targetPerHari) : '—'}</div>
                <div style="font-size:0.75rem;color:var(--text-secondary);">Avg 3 hari: ${fmt(avgLast3)}/hari</div>
            </div>
            <div style="background:var(--card-bg);border:1px solid var(--card-border);border-radius:0.75rem;padding:1rem;border-left:3px solid ${projColor};">
                <div style="font-size:0.7rem;color:var(--text-secondary);font-weight:600;text-transform:uppercase;">Proyeksi Selesai</div>
                <div style="font-size:1.3rem;font-weight:800;color:${projColor};line-height:1.2;">${projDays < 200 ? projDateStr : '—'}</div>
                <div style="font-size:0.75rem;color:${projColor};font-weight:600;">${noData ? '' : (onTrack ? '✅ On track' : '⚠️ Tidak akan selesai tgl 15')}</div>
            </div>
        </div>`;
    }

    // ── Survey type toggle ───────────────────────────────────────────────────
    function renderSurveyToggle(active) {
        const base = 'padding:0.4rem 0.9rem;border-radius:0.6rem;border:1px solid var(--card-border);font-family:Outfit,sans-serif;font-size:0.78rem;font-weight:600;cursor:pointer;transition:all 0.2s;';
        const activeStyle = 'background:linear-gradient(135deg,#6366f1,#4f46e5);color:#fff;';
        const inactiveStyle = 'background:transparent;color:var(--text-secondary);';
        return `
        <div style="display:flex;gap:0.5rem;margin-bottom:1rem;">
            <button onclick="window.renderPaluMonitoring('se_umum')" style="${base}${active==='se_umum'?activeStyle:inactiveStyle}">SE Umum</button>
            <button onclick="window.renderPaluMonitoring('se_ub')" style="${base}${active==='se_ub'?activeStyle:inactiveStyle}">SE UB</button>
        </div>`;
    }

    // ── Main render ──────────────────────────────────────────────────────────
    window.renderPaluMonitoring = function (surveyType) {
        surveyType = surveyType || 'se_umum';
        const container = document.getElementById('palu-monitoring-container');
        if (!container) return;
        const ipasData = getPaluIpas(surveyType);

        // ORDER: toggle → summary cards → petugas table → daily tracker
        container.innerHTML =
            renderSurveyToggle(surveyType) +
            renderSummaryCards(ipasData, surveyType) +
            renderPetugasTable() +
            renderDailyTable(surveyType);
    };

    window.initPaluMonitoring = function () {
        window.renderPaluMonitoring('se_umum');
    };
})();
