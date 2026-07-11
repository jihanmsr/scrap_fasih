// ═══════════════════════════════════════════════════════════════════════════
// palu_monitoring.js — Tab Monitoring Khusus Kota Palu
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
        return Object.entries(grouped).sort((a, b) => a[0].localeCompare(b[0]));
    }

    function renderSummaryCards(ipasData, surveyType) {
        if (!ipasData) return '<div style="color:var(--text-secondary);padding:2rem;text-align:center;">Data Palu belum tersedia.</div>';

        const total = ipasData.total_prelist || 0;
        const submitted = ipasData.total_submitted || 0;
        const draft = ipasData.total_draft || 0;
        const open = ipasData.total_open || 0;
        const sisa = Math.max(0, total - submitted);
        const capaian = pct(submitted, total);
        const hariLeft = daysUntilDeadline();
        const targetPerHari = hariLeft > 0 ? Math.ceil(sisa / hariLeft) : sisa;

        const daily = getPaluDailyStats(surveyType);
        const last3 = daily.slice(-3).map(d => d[1]);
        const avgLast3 = last3.length > 0 ? Math.round(last3.reduce((a, b) => a + b, 0) / last3.length) : 0;

        const projDays = avgLast3 > 0 ? Math.ceil(sisa / avgLast3) : 999;
        const projDate = new Date();
        projDate.setDate(projDate.getDate() + projDays);
        const projDateStr = projDate.toLocaleDateString('id-ID', { day: 'numeric', month: 'long', year: 'numeric' });
        const onTrack = avgLast3 >= targetPerHari;

        const statusColor = capaian >= 50 ? '#16a34a' : capaian >= 25 ? '#d97706' : '#dc2626';
        const statusText = capaian >= 50 ? '🟢 AMAN' : capaian >= 25 ? '🟡 WASPADA' : '🔴 KRITIS';
        const projColor = onTrack ? '#16a34a' : '#dc2626';

        return `
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:1rem;margin-bottom:1.5rem;">
            <div style="background:var(--card-bg);border:1px solid var(--card-border);border-radius:1rem;padding:1.25rem;border-left:4px solid ${statusColor};">
                <div style="font-size:0.75rem;color:var(--text-secondary);font-weight:600;text-transform:uppercase;letter-spacing:0.05em;">Status Palu</div>
                <div style="font-size:2rem;font-weight:800;color:${statusColor};margin:0.25rem 0;">${capaian.toFixed(1)}%</div>
                <div style="font-size:0.8rem;color:var(--text-secondary);">${statusText}</div>
                <div style="font-size:0.75rem;color:var(--text-secondary);margin-top:0.4rem;">${fmt(submitted)} dari ${fmt(total)}</div>
            </div>
            <div style="background:var(--card-bg);border:1px solid var(--card-border);border-radius:1rem;padding:1.25rem;border-left:4px solid #3b82f6;">
                <div style="font-size:0.75rem;color:var(--text-secondary);font-weight:600;text-transform:uppercase;letter-spacing:0.05em;">Sisa Usaha</div>
                <div style="font-size:2rem;font-weight:800;color:#3b82f6;margin:0.25rem 0;">${fmt(sisa)}</div>
                <div style="font-size:0.8rem;color:var(--text-secondary);">Open: ${fmt(open)} | Draft: ${fmt(draft)}</div>
                <div style="font-size:0.75rem;color:var(--text-secondary);margin-top:0.4rem;">Sisa hari: ${hariLeft} hari</div>
            </div>
            <div style="background:var(--card-bg);border:1px solid var(--card-border);border-radius:1rem;padding:1.25rem;border-left:4px solid #f59e0b;">
                <div style="font-size:0.75rem;color:var(--text-secondary);font-weight:600;text-transform:uppercase;letter-spacing:0.05em;">Target Harian</div>
                <div style="font-size:2rem;font-weight:800;color:#f59e0b;margin:0.25rem 0;">${fmt(targetPerHari)}</div>
                <div style="font-size:0.8rem;color:var(--text-secondary);">submit/hari agar selesai tgl 15</div>
                <div style="font-size:0.75rem;color:var(--text-secondary);margin-top:0.4rem;">Rata-rata 3 hari terakhir: ${fmt(avgLast3)}/hari</div>
            </div>
            <div style="background:var(--card-bg);border:1px solid var(--card-border);border-radius:1rem;padding:1.25rem;border-left:4px solid ${projColor};">
                <div style="font-size:0.75rem;color:var(--text-secondary);font-weight:600;text-transform:uppercase;letter-spacing:0.05em;">Proyeksi Selesai</div>
                <div style="font-size:1.3rem;font-weight:800;color:${projColor};margin:0.25rem 0;line-height:1.2;">${projDays < 200 ? projDateStr : '—'}</div>
                <div style="font-size:0.8rem;color:${projColor};font-weight:600;">${onTrack ? '✅ Bisa selesai tepat waktu' : '⚠️ Kemungkinan TIDAK selesai tgl 15'}</div>
            </div>
        </div>`;
    }

    function renderChart(surveyType) {
        const daily = getPaluDailyStats(surveyType);
        if (daily.length === 0) return '<div style="color:var(--text-secondary);padding:1rem;text-align:center;font-size:0.85rem;">Belum ada data harian Palu.</div>';

        const ipasData = getPaluIpas(surveyType);
        const total = ipasData ? ipasData.total_prelist || 0 : 0;
        const submitted = ipasData ? ipasData.total_submitted || 0 : 0;
        const sisa = Math.max(0, total - submitted);
        const hariLeft = daysUntilDeadline();
        const targetPerHari = hariLeft > 0 ? Math.ceil(sisa / hariLeft) : 0;

        const shown = daily.slice(-30);
        const labels = JSON.stringify(shown.map(d => {
            const parts = d[0].split('-');
            return parseInt(parts[2]) + '/' + parseInt(parts[1]);
        }));
        const counts = JSON.stringify(shown.map(d => d[1]));
        const barColors = JSON.stringify(shown.map(d => d[1] >= targetPerHari ? 'rgba(34,197,94,0.75)' : 'rgba(239,68,68,0.75)'));
        const borderColors = JSON.stringify(shown.map(d => d[1] >= targetPerHari ? '#16a34a' : '#dc2626'));
        const maxVal = Math.ceil(Math.max(...shown.map(d => d[1]), targetPerHari) * 1.2);
        const targetLine = JSON.stringify(Array(shown.length).fill(targetPerHari));

        return `
        <div style="background:var(--card-bg);border:1px solid var(--card-border);border-radius:1rem;padding:1.25rem;margin-bottom:1.5rem;">
            <div style="font-weight:700;font-size:0.95rem;color:var(--text-primary);margin-bottom:1rem;">
                📊 Progres Harian Palu (30 Hari Terakhir)
                <span style="font-size:0.75rem;font-weight:400;color:var(--text-secondary);margin-left:0.5rem;">🟢 Di atas target | 🔴 Di bawah target | — Target: ${fmt(targetPerHari)}/hari</span>
            </div>
            <canvas id="palu-daily-chart" height="100"></canvas>
        </div>
        <script id="palu-chart-script">
        (function(){
            const ctx = document.getElementById('palu-daily-chart');
            if (!ctx || !window.Chart) return;
            if (ctx._chartInstance) { ctx._chartInstance.destroy(); }
            ctx._chartInstance = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: ${labels},
                    datasets: [
                        { label: 'Submit per Hari', data: ${counts}, backgroundColor: ${barColors}, borderColor: ${borderColors}, borderWidth: 1.5, borderRadius: 4, order: 2 },
                        { label: 'Target Harian (${fmt(targetPerHari)}/hari)', data: ${targetLine}, type: 'line', borderColor: '#f59e0b', borderWidth: 2, borderDash: [6,3], pointRadius: 0, fill: false, order: 1 }
                    ]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { display: true, position: 'top', labels: { font: { family: 'Outfit' }, boxWidth: 14 } },
                        tooltip: { callbacks: { label: function(ctx){ return ctx.dataset.label + ': ' + ctx.parsed.y.toLocaleString('id-ID'); } } }
                    },
                    scales: {
                        x: { grid: { display: false }, ticks: { font: { family: 'Outfit', size: 10 } } },
                        y: { beginAtZero: true, max: ${maxVal}, ticks: { font: { family: 'Outfit', size: 10 }, callback: function(v){ return v.toLocaleString('id-ID'); } } }
                    }
                }
            });
        })();
        <\/script>`;
    }

    function renderPetugasTable(surveyType) {
        const petugasList = getPaluPetugasData();

        if (petugasList.length === 0) {
            return '<div style="color:var(--text-secondary);padding:2rem;text-align:center;">Data petugas Palu tidak ditemukan. Pastikan <code>petugas_region_map.js</code> sudah dimuat.</div>';
        }

        const thBase = 'padding:0.6rem 0.75rem;font-size:0.75rem;font-weight:700;color:#fff;white-space:nowrap;';
        const rows = petugasList.map((p, idx) => {
            const capVal = p.pctCap;
            let badge, rowBg;
            if (capVal < 15) {
                badge = '<span style="background:#fef2f2;color:#dc2626;border:1px solid #fca5a5;border-radius:0.5rem;padding:0.15rem 0.5rem;font-size:0.7rem;font-weight:700;">🔴 SANGAT RENDAH</span>';
                rowBg = idx % 2 === 0 ? '' : 'rgba(239,68,68,0.03)';
            } else if (capVal < 30) {
                badge = '<span style="background:#fffbeb;color:#d97706;border:1px solid #fcd34d;border-radius:0.5rem;padding:0.15rem 0.5rem;font-size:0.7rem;font-weight:700;">🟡 PERLU DIKEJAR</span>';
                rowBg = idx % 2 === 0 ? '' : 'rgba(245,158,11,0.03)';
            } else {
                badge = '<span style="background:#f0fdf4;color:#16a34a;border:1px solid #86efac;border-radius:0.5rem;padding:0.15rem 0.5rem;font-size:0.7rem;font-weight:700;">🟢 OK</span>';
                rowBg = idx % 2 === 0 ? '' : 'rgba(34,197,94,0.03)';
            }
            const barColor = capVal < 15 ? '#dc2626' : capVal < 30 ? '#f59e0b' : '#22c55e';
            const bar = '<div style="width:100%;background:var(--card-border);border-radius:9999px;height:5px;margin-top:3px;"><div style="width:' + Math.min(100, capVal).toFixed(1) + '%;background:' + barColor + ';height:5px;border-radius:9999px;"></div></div>';
            const td = 'padding:0.55rem 0.75rem;font-size:0.8rem;border-bottom:1px solid var(--card-border);text-align:right;';
            const tdL = 'padding:0.55rem 0.75rem;font-size:0.8rem;border-bottom:1px solid var(--card-border);text-align:left;';
            return '<tr style="background:' + rowBg + '">' +
                '<td style="' + tdL + 'color:var(--text-secondary);font-weight:600;">' + (idx+1) + '</td>' +
                '<td style="' + tdL + '"><div style="font-weight:600;color:var(--text-primary);">' + p.name + '</div><div style="font-size:0.7rem;color:var(--text-secondary);">' + p.email + '</div></td>' +
                '<td style="' + td + 'font-weight:600;">' + fmt(p.total) + '</td>' +
                '<td style="' + td + 'color:#22c55e;font-weight:700;">' + fmt(p.submitted) + '</td>' +
                '<td style="' + td + 'color:#3b82f6;">' + fmt(p.sisa) + '</td>' +
                '<td style="' + td + '"><div style="font-weight:700;color:' + barColor + ';">' + capVal.toFixed(1) + '%</div>' + bar + '</td>' +
                '<td style="' + td + 'color:#f59e0b;font-weight:700;">' + fmt(p.perHari) + '/hari</td>' +
                '<td style="' + tdL + '">' + badge + '</td>' +
            '</tr>';
        }).join('');

        const totTarget = petugasList.reduce((a, b) => a + b.total, 0);
        const totSubmitted = petugasList.reduce((a, b) => a + b.submitted, 0);
        const totSisa = petugasList.reduce((a, b) => a + b.sisa, 0);
        const totPct = pct(totSubmitted, totTarget);

        return `
        <div style="background:var(--card-bg);border:1px solid var(--card-border);border-radius:1rem;overflow:hidden;">
            <div style="padding:1rem 1.25rem;border-bottom:1px solid var(--card-border);display:flex;justify-content:space-between;align-items:center;">
                <div style="font-weight:700;font-size:0.95rem;color:var(--text-primary);">
                    👥 Progres Petugas Palu
                    <span style="font-size:0.8rem;font-weight:400;color:var(--text-secondary);margin-left:0.5rem;">(diurutkan dari capaian terendah)</span>
                </div>
                <div style="font-size:0.8rem;color:var(--text-secondary);">${petugasList.length} petugas</div>
            </div>
            <div style="overflow-x:auto;">
                <table style="width:100%;border-collapse:collapse;">
                    <thead>
                        <tr style="background:linear-gradient(135deg,#1e3a5f,#1a3050);">
                            <th style="${thBase}text-align:left;">No</th>
                            <th style="${thBase}text-align:left;">Petugas</th>
                            <th style="${thBase}text-align:right;">Target</th>
                            <th style="${thBase}text-align:right;">Selesai</th>
                            <th style="${thBase}text-align:right;">Sisa</th>
                            <th style="${thBase}text-align:right;">% Capaian</th>
                            <th style="${thBase}text-align:right;">Wajib/Hari</th>
                            <th style="${thBase}text-align:left;">Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${rows}
                        <tr style="background:rgba(99,102,241,0.08);font-weight:700;">
                            <td colspan="2" style="padding:0.7rem 0.75rem;font-size:0.8rem;color:var(--text-primary);">TOTAL (${petugasList.length} petugas)</td>
                            <td style="padding:0.7rem 0.75rem;text-align:right;font-size:0.8rem;">${fmt(totTarget)}</td>
                            <td style="padding:0.7rem 0.75rem;text-align:right;font-size:0.8rem;color:#22c55e;">${fmt(totSubmitted)}</td>
                            <td style="padding:0.7rem 0.75rem;text-align:right;font-size:0.8rem;color:#3b82f6;">${fmt(totSisa)}</td>
                            <td style="padding:0.7rem 0.75rem;text-align:right;font-size:0.8rem;">${totPct.toFixed(1)}%</td>
                            <td colspan="2"></td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>`;
    }

    window.renderPaluMonitoring = function (surveyType) {
        surveyType = surveyType || 'se_umum';
        const container = document.getElementById('palu-monitoring-container');
        if (!container) return;

        const tabUmum = document.getElementById('palu-tab-se-umum');
        const tabUb = document.getElementById('palu-tab-se-ub');
        [tabUmum, tabUb].forEach(btn => {
            if (!btn) return;
            const active = btn.id === 'palu-tab-' + surveyType;
            btn.style.background = active ? 'linear-gradient(135deg,#6366f1,#4f46e5)' : 'transparent';
            btn.style.color = active ? '#fff' : 'var(--text-secondary)';
        });

        const ipasData = getPaluIpas(surveyType);
        container.innerHTML = renderSummaryCards(ipasData, surveyType) + renderChart(surveyType) + renderPetugasTable(surveyType);

        // Execute chart script
        const script = container.querySelector('script');
        if (script) {
            const s = document.createElement('script');
            s.textContent = script.textContent;
            document.body.appendChild(s);
            s.remove();
        }
    };

    window.initPaluMonitoring = function () {
        window.renderPaluMonitoring('se_umum');
    };
})();
