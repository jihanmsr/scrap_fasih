const fs = require('fs');
let code = fs.readFileSync('app.js', 'utf8');

const target1 = `function renderSeTable(surveyType, parentElId) {`;
const rep1 = `function getFormattedDateLabels() {
    const t = new Date();
    const y = new Date(t); y.setDate(y.getDate() - 1);
    const h2 = new Date(t); h2.setDate(h2.getDate() - 2);
    const fmt = d => String(d.getDate()).padStart(2, '0') + '/' + String(d.getMonth()+1).padStart(2, '0');
    return {
        today: "Hari Ini (" + fmt(t) + ")",
        yesterday: "Kemarin (" + fmt(y) + ")",
        h2: "H-2 (" + fmt(h2) + ")"
    };
}

function renderSeTable(surveyType, parentElId) {`;

code = code.replace(target1, rep1);

const target2 = `Hari Ini\${getIcon('today_completed')}`;
const rep2 = `\${getFormattedDateLabels().today}\${getIcon('today_completed')}`;
code = code.replace(target2, rep2);

const target3 = `Kemarin\${getIcon('yesterday_completed')}`;
const rep3 = `\${getFormattedDateLabels().yesterday}\${getIcon('yesterday_completed')}`;
code = code.replace(target3, rep3);

const target4 = `H-2\${getIcon('two_days_ago_completed')}`;
const rep4 = `\${getFormattedDateLabels().h2}\${getIcon('two_days_ago_completed')}`;
code = code.replace(target4, rep4);

// For Alokasi Petugas Last Updated
const target5 = `                <div style="font-weight: 700; color: var(--text); padding: 0.2rem 0; font-family: 'Outfit', sans-serif;">\${item.kabupaten}</div>`;
const rep5 = `                <div style="font-weight: 700; color: var(--text); padding: 0.2rem 0 0 0; font-family: 'Outfit', sans-serif;">\${item.kabupaten}</div>
                \${item.timestamp ? \`<div style="font-size: 0.65rem; color: var(--text-muted); font-weight: normal; margin-top: 0.1rem;">Update: \${new Date(item.timestamp).toLocaleString('id-ID', {day:'2-digit', month:'short', hour:'2-digit', minute:'2-digit'})}</div>\` : ''}`;
code = code.replace(target5, rep5);

fs.writeFileSync('app.js', code);
console.log('Patched app.js');
