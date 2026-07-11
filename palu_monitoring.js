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
    function pct(a, b) {
        if (!b || b === 0) return 0;
        return Math.min(100, (a / b) * 100);
    }
    function daysUntilDeadline() {
        const now = new Date();
        const diff = DEADLINE - now;
        return Math.max(0, Math.ceil(diff / (1000 * 60 * 60 * 24)));
    }
    function toDateStr(d) {
        return d.toISOString().slice(0, 10);
    }
    function getPaluIpas(surveyType) {
        const ipas = window.IPAS_DATA || {};
        const data = ipas[surveyType] || [];
        return data.find(d => d.kabupaten === PALU_KAB_NAME) || null;
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
                        all.push({ email: key, name, total, submitted, selesai: val.approved || 0, inProgress: val.submitted_pencacah || 0, sisa, pctCap, perHari });
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
        return grouped; // { 'YYYY-MM-DD': count }
    }

    // ── Build daily tracker table: kemarin → tgl 15 ─────────────────────────
    function renderDailyTable(surveyType) {
        const ipasData = getPaluIpas(surveyType);
        const totalTarget = ipasData ? ipasData.total_prelist || 0 : 0;
        const totalSubmitted = ipasData ? ipasData.total_submitted || 0 : 0;
        const sisa = Math.max(0, totalTarget - totalSubmitted);
        const dailyStats = getPaluDailyStats(surveyType);

        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const yesterday = new Date(today); yesterday.setDate(yesterday.getDate() - 1);
        const deadline = new Date('2026-07-15T00:00:00');

        // Collect all real dates (history)
        const allDates = Object.keys(dailyStats).sort();
        const historyDates = allDates.filter(d => d <= toDateStr(today));
        const futureDates = [];
        const cur = new Date(today); cur.setDate(cur.getDate() + 1);
        while (cur <= deadline) {
            futureDates.push(toDateStr(cur));
            cur.setDate(cur.getDate() + 1);
        }

        // We want to show: yesterday + a few days before, then today, then future until 15
        // Show last 7 history days + today + future
        const showHistory = historyDates.slice(-7);
        const showDates = [...showHistory, toDateStr(today), ...futureDates];

        // Calculate running cumulative from IPAS totalSubmitted (end of yesterday/most recent)
        // We work backwards: totalSubmitted = cumulative at latest data point
        // For today (not pulled yet): same as yesterday cumulative
        // Find cumulative at start of shown window
        let cumAtEndOfYesterday = totalSubmitted; // approximation: current total = end of yesterday

        // Compute target per hari
        const hariLeft = daysUntilDeadline();
        const targetPerHari = hariLeft > 0 ? Math.ceil(sisa / hariLeft) : 0;

        // Avg of last 3 real days for projection
        const last3 = historyDates.slice(-3).map(d => dailyStats[d] || 0);
        const avg3 = last3.length > 0 ? Math.round(last3.reduce((a, b) => a + b, 0) / last3.length) : 0;

        // Build rows
        // We need cumulative. Estimate by subtracting history from current total
        // cumulative[d] = sum of all submits up to d
        // Since we only have Palu daily, total on day d = sum(dailyStats up to d)
        const historySum = historyDates.reduce((acc, d) => acc + (dailyStats[d] || 0), 0);
        // Adjust: cumAtEndOfYesterday is the IPAS total. That should equal historySum if data is fresh.
        // But if not perfectly aligned, use IPAS total as anchor.

        const thStyle = 'padding:0.5rem 0.75rem;font-size:0.75rem;font-weight:700;color:#fff;white-space:nowrap;text-align:center;';
        const thLeftStyle = 'padding:0.5rem 0.75rem;font-size:0.75rem;font-weight:700;color:#fff;white-space:nowrap;text-align:left;';

        let prevCum = cumAtEndOfYesterday;
        // recompute prev cum: subtract today's (if any)
        const todayCount = dailyStats[toDateStr(today)] || 0;
        const yesterdayEndCum = cumAtEndOfYesterday - todayCount;

        let rows = '';
        let runCum = yesterdayEndCum;

        showDates.forEach(dateStr => {
            const dateObj = new Date(dateStr + 'T00:00:00');
            const isToday = dateStr === toDateStr(today);
            const isFuture = dateStr > toDateStr(today);
            const isPast = !isToday && !isFuture;

            const count = isPast ? (dailyStats[dateStr] || 0)
                : isToday ? (dailyStats[dateStr] || 0) // today might be 0 if not pulled
                : avg3; // future = projection

            const delta = count - (isPast ? (dailyStats[showDates[showDates.indexOf(dateStr) - 1]] || 0) : count);
            runCum += count;
            const pctCum = totalTarget > 0 ? ((runCum / totalTarget) * 100).toFixed(2) : '0.00';
            const deltaVsTarget = count - targetPerHari;

            let rowBg = '';
            let countColor = 'var(--text-primary)';
            let statusBadge = '';

            if (isFuture) {
                rowBg = 'rgba(99,102,241,0.04)';
                countColor = '#6366f1';
                statusBadge = '<span style="font-size:0.65rem;color:#6366f1;background:rgba(99,102,241,0.1);padding:0.1rem 0.4rem;border-radius:0.3rem;">PROYEKSI</span>';
            } else if (isToday && count === 0) {
                rowBg = 'rgba(245,158,11,0.06)';
                countColor = '#d97706';
                statusBadge = '<span style="font-size:0.65rem;color:#d97706;background:rgba(245,158,11,0.1);padding:0.1rem 0.4rem;border-radius:0.3rem;">BELUM DITARIK</span>';
            } else if (count >= targetPerHari) {
                rowBg = 'rgba(34,197,94,0.04)';
                countColor = '#16a34a';
                statusBadge = '<span style="font-size:0.65rem;color:#16a34a;background:rgba(34,197,94,0.1);padding:0.1rem 0.4rem;border-radius:0.3rem;">✓ TERCAPAI</span>';
            } else {
                rowBg = 'rgba(239,68,68,0.04)';
                countColor = '#dc2626';
                statusBadge = '<span style="font-size:0.65rem;color:#dc2626;background:rgba(239,68,68,0.1);padding:0.1rem 0.4rem;border-radius:0.3rem;">✗ KURANG</span>';
            }

            const dateLabel = dateObj.toLocaleDateString('id-ID', { weekday: 'short', day: 'numeric', month: 'short' });
            const dayLabel = isToday ? '<strong>HARI INI</strong>' : isFuture ? dateLabel : dateLabel;
            const deltaStr = deltaVsTarget > 0 ? '<span style="color:#16a34a;">+' + fmt(deltaVsTarget) + '</span>' : '<span style="color:#dc2626;">' + fmt(deltaVsTarget) + '</span>';
            const td = 'padding:0.5rem 0.75rem;font-size:0.8rem;border-bottom:1px solid var(--card-border);text-align:center;';
            const tdL = 'padding:0.5rem 0.75rem;font-size:0.8rem;border-bottom:1px solid var(--card-border);text-align:left;';

            rows += '<tr style="background:' + rowBg + '">' +
                '<td style="' + tdL + '">' + dayLabel + '</td>' +
                '<td style="' + td + 'font-weight:700;color:' + countColor + ';">' + fmt(count) + (isFuture ? '<div style="font-size:0.65rem;color:var(--text-secondary);">avg 3 hari</div>' : '') + '</td>' +
                '<td style="' + td + '">' + (count > 0 || isPast ? deltaStr : '—') + '</td>' +
                '<td style="' + td + 'font-weight:600;">' + fmt(runCum) + '</td>' +
                '<td style="' + td + '">' + pctCum + '%</td>' +
                '<td style="' + td + '">' + statusBadge + '</td>' +
            '</tr>';
        });

        return `
        <div style="background:var(--card-bg);border:1px solid var(--card-border);border-radius:1rem;overflow:hidden;margin-bottom:1.5rem;">
            <div style="padding:0.9rem 1.25rem;border-bottom:1px solid var(--card-border);display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:0.5rem;">
                <div style="font-weight:700;font-size:0.9rem;color:var(--text-primary);">
                    📅 Tracker Harian Palu — Kemarin s/d 15 Juli
                    <span style="font-size:0.75rem;font-weight:400;color:var(--text-secondary);margin-left:0.5rem;">Target: ${fmt(targetPerHari)}/hari | Rata-rata 3 hari: ${fmt(avg3)}/hari</span>
                </div>
                <div style="font-size:0.75rem;color:var(--text-secondary);">
                    🟣 = Proyeksi &nbsp; 🟡 = Belum ditarik &nbsp; 🟢 = Tercapai &nbsp; 🔴 = Kurang
                </div>
            </div>
            <div style="overflow-x:auto;">
                <table style="width:100%;border-collapse:collapse;">
                    <thead>
                        <tr style="background:linear-gradient(135deg,#1e3a5f,#1a3050);">
                            <th style="${thLeftStyle}">Tanggal</th>
                            <th style="${thStyle}">Submit Hari Ini</th>
                            <th style="${thStyle}">vs Target/Hari</th>
                            <th style="${thStyle}">Kumulatif</th>
                            <th style="${thStyle}">% Capaian</th>
                            <th style="${thStyle}">Status</th>
                        </tr>
                    </thead>
                    <tbody>${rows}</tbody>
                </table>
            </div>
        </div>`;
    }

    // ── Summary Cards ────────────────────────────────────────────────────────
    function renderSummaryCards(ipasData, surveyType) {
        if (!ipasData) return '<div style="color:var(--text-secondary);padding:1.5rem;text-align:center;">Data Palu belum tersedia.</div>';
        const total = ipasData.total_prelist || 0;
        const submitted = ipasData.total_submitted || 0;
        const sisa = Math.max(0, total - submitted);
        const capaian = pct(submitted, total);
        const hariLeft = daysUntilDeadline();
        const targetPerHari = hariLeft > 0 ? Math.ceil(sisa / hariLeft) : sisa;
        const dailyStats = getPaluDailyStats(surveyType);
        const today = new Date(); today.setHours(0,0,0,0);
        const allDates = Object.keys(dailyStats).sort();
        const last3Dates = allDates.slice(-3);
        const avgLast3 = last3Dates.length > 0 ? Math.round(last3Dates.reduce((a, d) => a + (dailyStats[d] || 0), 0) / last3Dates.length) : 0;
        const projDays = avgLast3 > 0 ? Math.ceil(sisa / avgLast3) : 999;
        const projDate = new Date(); projDate.setDate(projDate.getDate() + projDays);
        const projDateStr = projDate.toLocaleDateString('id-ID', { day: 'numeric', month: 'long' });
        const onTrack = avgLast3 >= targetPerHari;
        const statusColor = capaian >= 50 ? '#16a34a' : capaian >= 25 ? '#d97706' : '#dc2626';
        const statusText = capaian >= 50 ? '🟢 AMAN' : capaian >= 25 ? '🟡 WASPADA' : '🔴 KRITIS';
        const projColor = onTrack ? '#16a34a' : '#dc2626';

        return `
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:0.75rem;margin-bottom:1.25rem;">
            <div style="background:var(--card-bg);border:1px solid var(--card-border);border-radius:0.75rem;padding:1rem;border-left:3px solid ${statusColor};">
                <div style="font-size:0.7rem;color:var(--text-secondary);font-weight:600;text-transform:uppercase;">Capaian Palu</div>
                <div style="font-size:1.8rem;font-weight:800;color:${statusColor};">${capaian.toFixed(1)}%</div>
                <div style="font-size:0.75rem;color:var(--text-secondary);">${statusText} · ${fmt(submitted)}/${fmt(total)}</div>
            </div>
            <div style="background:var(--card-bg);border:1px solid var(--card-border);border-radius:0.75rem;padding:1rem;border-left:3px solid #3b82f6;">
                <div style="font-size:0.7rem;color:var(--text-secondary);font-weight:600;text-transform:uppercase;">Sisa Usaha</div>
                <div style="font-size:1.8rem;font-weight:800;color:#3b82f6;">${fmt(sisa)}</div>
                <div style="font-size:0.75rem;color:var(--text-secondary);">Sisa ${hariLeft} hari lagi</div>
            </div>
            <div style="background:var(--card-bg);border:1px solid var(--card-border);border-radius:0.75rem;padding:1rem;border-left:3px solid #f59e0b;">
                <div style="font-size:0.7rem;color:var(--text-secondary);font-weight:600;text-transform:uppercase;">Wajib/Hari</div>
                <div style="font-size:1.8rem;font-weight:800;color:#f59e0b;">${fmt(targetPerHari)}</div>
                <div style="font-size:0.75rem;color:var(--text-secondary);">Avg 3 hari: ${fmt(avgLast3)}/hari</div>
            </div>
            <div style="background:var(--card-bg);border:1px solid var(--card-border);border-radius:0.75rem;padding:1rem;border-left:3px solid ${projColor};">
                <div style="font-size:0.7rem;color:var(--text-secondary);font-weight:600;text-transform:uppercase;">Proyeksi Selesai</div>
                <div style="font-size:1.3rem;font-weight:800;color:${projColor};line-height:1.2;">${projDays < 200 ? projDateStr : '—'}</div>
                <div style="font-size:0.75rem;color:${projColor};font-weight:600;">${onTrack ? '✅ On track' : '⚠️ Tidak akan selesai tgl 15'}</div>
            </div>
        </div>`;
    }

    // ── Petugas Table ────────────────────────────────────────────────────────
    function renderPetugasTable() {
        const petugasList = getPaluPetugasData();
        if (petugasList.length === 0) {
            return '<div style="color:var(--text-secondary);padding:1.5rem;text-align:center;">Data petugas Palu tidak ditemukan.</div>';
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
        <div style="background:var(--card-bg);border:1px solid var(--card-border);border-radius:1rem;overflow:hidden;">
            <div style="padding:0.9rem 1.25rem;border-bottom:1px solid var(--card-border);display:flex;justify-content:space-between;align-items:center;">
                <div style="font-weight:700;font-size:0.9rem;color:var(--text-primary);">
                    👥 Petugas Palu <span style="font-size:0.75rem;font-weight:400;color:var(--text-secondary);">(capaian terendah di atas)</span>
                </div>
                <div style="font-size:0.75rem;color:var(--text-secondary);">${petugasList.length} petugas</div>
            </div>
            <div style="overflow-x:auto;max-height:380px;overflow-y:auto;">
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
                            <td colspan="2" style="padding:0.6rem 0.6rem;font-size:0.78rem;color:var(--text-primary);">TOTAL (${petugasList.length})</td>
                            <td style="padding:0.6rem 0.6rem;text-align:right;font-size:0.78rem;">${fmt(totTarget)}</td>
                            <td style="padding:0.6rem 0.6rem;text-align:right;font-size:0.78rem;color:#22c55e;">${fmt(totSub)}</td>
                            <td style="padding:0.6rem 0.6rem;text-align:right;font-size:0.78rem;color:#3b82f6;">${fmt(totSisa)}</td>
                            <td style="padding:0.6rem 0.6rem;text-align:right;font-size:0.78rem;">${pct(totSub,totTarget).toFixed(1)}%</td>
                            <td colspan="2"></td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>`;
    }

    // ── Survey type toggle ───────────────────────────────────────────────────
    function renderSurveyToggle(active) {
        return `
        <div style="display:flex;gap:0.5rem;margin-bottom:1rem;">
            <button onclick="window.renderPaluMonitoring('se_umum')"
                style="padding:0.4rem 0.9rem;border-radius:0.6rem;border:1px solid var(--card-border);font-family:Outfit,sans-serif;font-size:0.78rem;font-weight:600;cursor:pointer;transition:all 0.2s;
                ${active === 'se_umum' ? 'background:linear-gradient(135deg,#6366f1,#4f46e5);color:#fff;' : 'background:transparent;color:var(--text-secondary);'}">
                SE Umum
            </button>
            <button onclick="window.renderPaluMonitoring('se_ub')"
                style="padding:0.4rem 0.9rem;border-radius:0.6rem;border:1px solid var(--card-border);font-family:Outfit,sans-serif;font-size:0.78rem;font-weight:600;cursor:pointer;transition:all 0.2s;
                ${active === 'se_ub' ? 'background:linear-gradient(135deg,#6366f1,#4f46e5);color:#fff;' : 'background:transparent;color:var(--text-secondary);'}">
                SE UB
            </button>
        </div>`;
    }

    // ── Main render ──────────────────────────────────────────────────────────
    window.renderPaluMonitoring = function (surveyType) {
        surveyType = surveyType || 'se_umum';
        const container = document.getElementById('palu-monitoring-container');
        if (!container) return;

        const ipasData = getPaluIpas(surveyType);
        container.innerHTML =
            renderSurveyToggle(surveyType) +
            renderSummaryCards(ipasData, surveyType) +
            renderDailyTable(surveyType) +
            renderPetugasTable();
    };

    window.initPaluMonitoring = function () {
        window.renderPaluMonitoring('se_umum');
    };
})();
