// ═══════════════════════════════════════════════════════════════════════════
// palu_monitoring.js — Delta Harian Per-Petugas Kota Palu
// ═══════════════════════════════════════════════════════════════════════════
(function () {
    const DEADLINE = new Date('2026-07-15T23:59:59');
    const PALU_KAB_CODE = '7271';
    let _showHistory = false;

    function fmt(n) { if (n == null || isNaN(n)) return '0'; return Number(n).toLocaleString('id-ID'); }
    function pct(a, b) { return (!b) ? 0 : Math.min(100, (a / b) * 100); }
    function toDateStr(d) { return d.toISOString().slice(0, 10); }
    function daysLeft() { return Math.max(0, Math.ceil((DEADLINE - new Date()) / 86400000)); }
    function getPaluIpas(t) {
        return ((window.IPAS_DATA||{})[t]||[]).find(d=>(d.kabupaten||'').includes('PALU'))||null;
    }

    // ── Build per-petugas data with deltas ───────────────────────────────────
    function buildPetugasData() {
        const snapData = window.PETUGAS_DAILY_PALU || {}; // { email: { name, target, snapshots:{date:cum} } }
        const progressMap = window.PETUGAS_PROGRESS_MAP || {};
        const users = window.PETUGAS_USERS || {};

        // Current totals from fast_petugas_progress
        const curMap = {};
        const traverse = (obj) => {
            for (const [k, v] of Object.entries(obj)) {
                if (v && typeof v === 'object' && 'target' in v) {
                    curMap[k.toLowerCase()] = {
                        target: v.target || 0,
                        selesai: (v.submitted_pencacah||0) + (v.approved||0),
                        name: users[k] || users[k.split('@')[0]] || k.split('@')[0]
                    };
                } else if (v && typeof v === 'object') traverse(v);
            }
        };
        traverse(progressMap);

        // Collect all snapshot dates (sorted)
        const allDatesSet = new Set();
        for (const d of Object.values(snapData))
            Object.keys(d.snapshots||{}).forEach(dt => allDatesSet.add(dt));
        const allDates = [...allDatesSet].sort(); // e.g. ['2026-07-09', '2026-07-11']

        // Build rows: each petugas = { name, target, selesaiNow, pctNow, perHari, deltas:{date:n} }
        const rows = [];
        for (const [email, snap] of Object.entries(snapData)) {
            const cur = curMap[email] || {};
            const name = snap.name || cur.name || email.split('@')[0];
            const target = cur.target || snap.target || 0;
            const selesaiNow = cur.selesai || 0;
            const sisa = Math.max(0, target - selesaiNow);
            const pctNow = pct(selesaiNow, target);
            const hl = daysLeft();
            const perHari = hl > 0 ? Math.ceil(sisa / hl) : sisa;

            // Compute delta per snapshot date: delta[date] = cum[date] - cum[prevDate]
            const snaps = snap.snapshots || {};
            const deltas = {};
            for (let i = 0; i < allDates.length; i++) {
                const d = allDates[i];
                const prevCum = i > 0 ? (snaps[allDates[i-1]] || 0) : 0;
                const curCum  = snaps[d];
                if (curCum !== undefined) deltas[d] = curCum - prevCum;
            }
            // Also compute delta for "today" vs last snapshot
            const today = toDateStr(new Date());
            const lastSnapDate = allDates[allDates.length - 1];
            if (lastSnapDate !== today && selesaiNow > 0) {
                const lastCum = snaps[lastSnapDate] || 0;
                deltas[today] = selesaiNow - lastCum;
            }

            rows.push({ email, name, target, selesaiNow, sisa, pctNow, perHari, deltas });
        }

        rows.sort((a, b) => a.pctNow - b.pctNow);
        return { rows, allDates };
    }

    // ── Petugas pivot table ─────────────────────────────────────────────────
    function renderPetugasTable() {
        const { rows, allDates } = buildPetugasData();
        if (!rows.length) return '<div style="padding:2rem;text-align:center;color:var(--text-secondary);">Data tidak ditemukan.</div>';

        const today = toDateStr(new Date());
        // Dates to display: today always shown. History = toggle.
        const histDates = allDates.filter(d => d !== today);
        const visibleDates = _showHistory ? [...allDates, today].filter((d,i,a)=>a.indexOf(d)===i).sort() : [today];
        const hiddenCount = histDates.length;

        const thBase = 'padding:0.5rem 0.6rem;font-size:0.72rem;font-weight:700;color:#fff;white-space:nowrap;';

        // Build date header cells
        const dateHeaders = visibleDates.map(d => {
            const dObj = new Date(d + 'T00:00:00');
            const label = dObj.toLocaleDateString('id-ID', { day: 'numeric', month: 'short' });
            const isToday = d === today;
            return `<th style="${thBase}text-align:center;min-width:75px;${isToday ? 'background:rgba(99,102,241,0.25);' : ''}">
                ${label}${isToday ? '<br><span style="font-size:0.58rem;font-weight:400;opacity:0.8;">hari ini</span>' : '<br><span style="font-size:0.58rem;font-weight:400;opacity:0.7;">delta</span>'}
            </th>`;
        }).join('');

        // Build rows
        const tableRows = rows.map((p, idx) => {
            const cv = p.pctNow;
            const barColor = cv < 15 ? '#dc2626' : cv < 30 ? '#f59e0b' : '#22c55e';
            const badge = cv < 15
                ? '<span style="font-size:0.6rem;color:#dc2626;border:1px solid #fca5a5;border-radius:0.3rem;padding:0.05rem 0.35rem;background:#fef2f2;white-space:nowrap;">🔴 KRITIS</span>'
                : cv < 30
                ? '<span style="font-size:0.6rem;color:#d97706;border:1px solid #fcd34d;border-radius:0.3rem;padding:0.05rem 0.35rem;background:#fffbeb;white-space:nowrap;">🟡 KEJAR</span>'
                : '<span style="font-size:0.6rem;color:#16a34a;border:1px solid #86efac;border-radius:0.3rem;padding:0.05rem 0.35rem;background:#f0fdf4;white-space:nowrap;">🟢 OK</span>';
            const bar = `<div style="width:100%;background:var(--card-border);border-radius:9999px;height:4px;margin-top:2px;">
                <div style="width:${Math.min(100,cv).toFixed(1)}%;background:${barColor};height:4px;border-radius:9999px;"></div></div>`;
            const rowBg = idx % 2 === 0 ? '' : 'rgba(99,102,241,0.025)';
            const td  = 'padding:0.4rem 0.55rem;font-size:0.77rem;border-bottom:1px solid var(--card-border);text-align:right;vertical-align:middle;';
            const tdL = 'padding:0.4rem 0.55rem;font-size:0.77rem;border-bottom:1px solid var(--card-border);text-align:left;vertical-align:middle;';
            const tdC = 'padding:0.4rem 0.55rem;font-size:0.77rem;border-bottom:1px solid var(--card-border);text-align:center;vertical-align:middle;';

            const dateCells = visibleDates.map(d => {
                const isToday = d === today;
                const delta = p.deltas[d];
                if (delta === undefined || delta === null) {
                    return `<td style="${tdC}color:var(--text-secondary);">—</td>`;
                }
                // Color: green = positive, red = 0 or negative, gray = no data
                const dColor = delta > 0 ? '#16a34a' : delta === 0 ? '#d97706' : '#dc2626';
                const bg = isToday ? 'background:rgba(99,102,241,0.06);' : '';
                return `<td style="${tdC}${bg}font-weight:700;color:${dColor};">+${fmt(delta)}</td>`;
            }).join('');

            return `<tr style="background:${rowBg}">
                <td style="${tdL}color:var(--text-secondary);font-weight:600;">${idx+1}</td>
                <td style="${tdL}">
                    <div style="font-weight:600;color:var(--text-primary);font-size:0.79rem;">${p.name}</div>
                    <div style="font-size:0.62rem;color:var(--text-secondary);">${p.email}</div>
                </td>
                <td style="${td}">${fmt(p.target)}</td>
                <td style="${td}color:#22c55e;font-weight:700;">${fmt(p.selesaiNow)}</td>
                ${dateCells}
                <td style="${td}"><div style="font-weight:700;color:${barColor};">${cv.toFixed(1)}%</div>${bar}</td>
                <td style="${td}color:#f59e0b;font-weight:700;">${fmt(p.perHari)}/hr</td>
                <td style="${tdL}">${badge}</td>
            </tr>`;
        }).join('');

        // Total row
        const totTarget = rows.reduce((a,b)=>a+b.target,0);
        const totSub    = rows.reduce((a,b)=>a+b.selesaiNow,0);
        const totDateCells = visibleDates.map(d => {
            const sum = rows.reduce((a,b)=> a + (b.deltas[d] ?? 0), 0);
            const isToday = d === today;
            const dColor = sum > 0 ? '#22c55e' : '#d97706';
            return `<td style="padding:0.6rem 0.55rem;text-align:center;font-weight:800;color:${dColor};${isToday?'background:rgba(99,102,241,0.08);':''}">+${fmt(sum)}</td>`;
        }).join('');

        const toggleBtn = `<button onclick="window.togglePaluHistory()" style="padding:0.35rem 0.8rem;border-radius:0.6rem;border:1px solid var(--card-border);font-family:Outfit,sans-serif;font-size:0.73rem;font-weight:600;cursor:pointer;background:transparent;color:var(--text-secondary);">
            ${_showHistory ? '🙈 Sembunyikan history (' + hiddenCount + ' tgl)' : '📅 Lihat history (' + hiddenCount + ' tgl)'}
        </button>`;

        return `
        <div style="background:var(--card-bg);border:1px solid var(--card-border);border-radius:1rem;overflow:hidden;">
            <div style="padding:0.9rem 1.25rem;border-bottom:1px solid var(--card-border);display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:0.5rem;">
                <div style="font-weight:700;font-size:0.9rem;color:var(--text-primary);">
                    👥 Delta Submit Harian — Petugas Palu
                    <span style="font-size:0.73rem;font-weight:400;color:var(--text-secondary);margin-left:0.5rem;">capaian terendah di atas · ${rows.length} petugas</span>
                </div>
                ${hiddenCount > 0 ? toggleBtn : ''}
            </div>
            <div style="overflow-x:auto;max-height:500px;overflow-y:auto;">
                <table style="width:100%;border-collapse:collapse;">
                    <thead style="position:sticky;top:0;z-index:2;">
                        <tr style="background:linear-gradient(135deg,#1e3a5f,#1a3050);">
                            <th style="${thBase}text-align:left;">No</th>
                            <th style="${thBase}text-align:left;">Petugas</th>
                            <th style="${thBase}text-align:right;">Target</th>
                            <th style="${thBase}text-align:right;">Total Selesai</th>
                            ${dateHeaders}
                            <th style="${thBase}text-align:right;">% Capaian</th>
                            <th style="${thBase}text-align:right;">Wajib/Hari</th>
                            <th style="${thBase}text-align:left;">Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${tableRows}
                        <tr style="background:rgba(99,102,241,0.08);font-weight:700;border-top:2px solid rgba(99,102,241,0.3);">
                            <td colspan="2" style="padding:0.6rem 0.55rem;font-size:0.78rem;color:var(--text-primary);">TOTAL (${rows.length})</td>
                            <td style="padding:0.6rem 0.55rem;text-align:right;font-size:0.78rem;">${fmt(totTarget)}</td>
                            <td style="padding:0.6rem 0.55rem;text-align:right;font-size:0.78rem;color:#22c55e;">${fmt(totSub)}</td>
                            ${totDateCells}
                            <td style="padding:0.6rem 0.55rem;text-align:right;font-size:0.78rem;">${pct(totSub,totTarget).toFixed(1)}%</td>
                            <td colspan="2"></td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>`;
    }

    // ── Summary cards ────────────────────────────────────────────────────────
    function renderSummaryCards(ipasData, surveyType) {
        const nd = !ipasData;
        const total = nd ? 0 : (ipasData.total_prelist||0);
        const sub   = nd ? 0 : (ipasData.total_submitted||0);
        const sisa  = Math.max(0, total - sub);
        const cap   = pct(sub, total);
        const hl    = daysLeft();
        const tph   = total > 0 && hl > 0 ? Math.ceil(sisa / hl) : 0;
        const ds    = (window.DAILY_SUBMISSION_STATS||[]).filter(s=>s.kab_name==='PALU' && s.survey_type===(surveyType==='se_ub'?'se_ub':'se_umum'));
        const grp   = {}; ds.forEach(s=>{ grp[s.date]=(grp[s.date]||0)+s.count; });
        const sdates = Object.keys(grp).sort();
        const l3    = sdates.slice(-3).map(d=>grp[d]||0);
        const avg3  = l3.length ? Math.round(l3.reduce((a,b)=>a+b,0)/l3.length) : 0;
        const pj    = avg3 > 0 ? Math.ceil(sisa/avg3) : 999;
        const pjDate= new Date(); pjDate.setDate(pjDate.getDate()+pj);
        const pjStr = pjDate.toLocaleDateString('id-ID',{day:'numeric',month:'long'});
        const onTk  = tph > 0 && avg3 >= tph;
        const sc    = nd ? '#6366f1' : cap>=50?'#16a34a':cap>=25?'#d97706':'#dc2626';
        const pc    = onTk ? '#16a34a' : '#dc2626';
        return `
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:0.65rem;margin-bottom:1.1rem;">
            <div style="background:var(--card-bg);border:1px solid var(--card-border);border-radius:0.75rem;padding:0.9rem;border-left:3px solid ${sc};">
                <div style="font-size:0.66rem;color:var(--text-secondary);font-weight:700;text-transform:uppercase;letter-spacing:0.04em;">Capaian Palu</div>
                <div style="font-size:1.75rem;font-weight:800;color:${sc};">${nd?'—':cap.toFixed(1)+'%'}</div>
                <div style="font-size:0.7rem;color:var(--text-secondary);">${nd?'data IPAS belum tersedia':fmt(sub)+'/'+fmt(total)}</div>
            </div>
            <div style="background:var(--card-bg);border:1px solid var(--card-border);border-radius:0.75rem;padding:0.9rem;border-left:3px solid #3b82f6;">
                <div style="font-size:0.66rem;color:var(--text-secondary);font-weight:700;text-transform:uppercase;letter-spacing:0.04em;">Sisa Usaha</div>
                <div style="font-size:1.75rem;font-weight:800;color:#3b82f6;">${nd?'—':fmt(sisa)}</div>
                <div style="font-size:0.7rem;color:var(--text-secondary);">Sisa ${hl} hari</div>
            </div>
            <div style="background:var(--card-bg);border:1px solid var(--card-border);border-radius:0.75rem;padding:0.9rem;border-left:3px solid #f59e0b;">
                <div style="font-size:0.66rem;color:var(--text-secondary);font-weight:700;text-transform:uppercase;letter-spacing:0.04em;">Target/Hari</div>
                <div style="font-size:1.75rem;font-weight:800;color:#f59e0b;">${tph>0?fmt(tph):'—'}</div>
                <div style="font-size:0.7rem;color:var(--text-secondary);">Avg 3 hari: ${fmt(avg3)}/hari</div>
            </div>
            <div style="background:var(--card-bg);border:1px solid var(--card-border);border-radius:0.75rem;padding:0.9rem;border-left:3px solid ${pc};">
                <div style="font-size:0.66rem;color:var(--text-secondary);font-weight:700;text-transform:uppercase;letter-spacing:0.04em;">Proyeksi Selesai</div>
                <div style="font-size:1.2rem;font-weight:800;color:${pc};line-height:1.2;">${pj<200?pjStr:'—'}</div>
                <div style="font-size:0.7rem;color:${pc};font-weight:600;">${nd?'':onTk?'✅ On track':'⚠️ Tidak selesai tgl 15'}</div>
            </div>
        </div>`;
    }

    function renderToggle(active) {
        const b = 'padding:0.38rem 0.85rem;border-radius:0.6rem;border:1px solid var(--card-border);font-family:Outfit,sans-serif;font-size:0.77rem;font-weight:600;cursor:pointer;';
        return `<div style="display:flex;gap:0.5rem;margin-bottom:1rem;">
            <button onclick="window.renderPaluMonitoring('se_umum')" style="${b}${active==='se_umum'?'background:linear-gradient(135deg,#6366f1,#4f46e5);color:#fff;':'background:transparent;color:var(--text-secondary);'}">SE Umum</button>
            <button onclick="window.renderPaluMonitoring('se_ub')"   style="${b}${active==='se_ub'  ?'background:linear-gradient(135deg,#6366f1,#4f46e5);color:#fff;':'background:transparent;color:var(--text-secondary);'}">SE UB</button>
        </div>`;
    }

    window.togglePaluHistory = function() {
        _showHistory = !_showHistory;
        // Re-render only the table portion
        const c = document.getElementById('palu-monitoring-container');
        const tbl = c && c.querySelector('[data-palu-tbl]');
        if (tbl) tbl.outerHTML = '<div data-palu-tbl>' + renderPetugasTable() + '</div>';
        else window.renderPaluMonitoring(window._paluSt || 'se_umum');
    };

    window.renderPaluMonitoring = function(surveyType) {
        surveyType = surveyType || 'se_umum';
        window._paluSt = surveyType;
        const c = document.getElementById('palu-monitoring-container');
        if (!c) return;
        const ipas = getPaluIpas(surveyType);
        c.innerHTML = renderToggle(surveyType) + renderSummaryCards(ipas, surveyType) +
            '<div data-palu-tbl>' + renderPetugasTable() + '</div>';
    };

    window.initPaluMonitoring = function() { window.renderPaluMonitoring('se_umum'); };
})();
