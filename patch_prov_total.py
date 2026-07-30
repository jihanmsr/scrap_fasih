import re

with open('app.js', 'r') as f:
    content = f.read()

replacement = """        const provDeltaLusa = prelist > 0 ? (twoDaysAgo / prelist) * 100 : 0;
        const provDeltaKemarin = prelist > 0 ? (yesterday / prelist) * 100 : 0;
        const provDeltaHariIni = prelist > 0 ? (today / prelist) * 100 : 0;

        const getProvDeltaHTML = (delta) => {
            if (delta === 0) return `<span style="font-size: 0.9rem; color: var(--text-muted);">-</span>`;
            return `<span style="font-size: 0.9rem; font-weight: 700; color: ${delta > 0 ? '#22c55e' : '#ef4444'};">${delta > 0 ? '+' : ''}${delta.toFixed(2)}%</span>`;
        };

        provRow.innerHTML = `
            <td style="font-weight: 800; color: var(--text-primary); position: sticky; left: 0; background-color: var(--tfoot-sticky-bg); z-index: 25; border-bottom: 2px solid var(--card-border);">[72] SULAWESI TENGAH</td>
            <td style="text-align: right; font-family: monospace; font-weight: 700; color: var(--text-secondary); border-bottom: 2px solid var(--card-border);">${formatNum(prelist)}</td>
            <td style="text-align: right; font-family: monospace; font-weight: 700; color: #f59e0b; border-bottom: 2px solid var(--card-border);">${formatNum(draft)}</td>
            <td style="text-align: right; font-family: monospace; font-weight: 700; color: #3b82f6; border-bottom: 2px solid var(--card-border);">${formatNum(openVal)}</td>
            
            <td style="text-align: right; font-family: monospace; font-weight: 800; color: var(--color-delivered); border-bottom: 2px solid var(--card-border);">${formatNum(submitted)}</td>
            <td style="text-align: right; font-family: monospace; color: var(--color-opened); border-bottom: 2px solid var(--card-border);">${formatNum(submittedPencacah)}</td>
            <td style="text-align: right; font-family: monospace; color: #d97706; border-bottom: 2px solid var(--card-border);">${formatNum(submittedRespondent)}</td>
            <td style="text-align: right; font-family: monospace; color: #047857; border-bottom: 2px solid var(--card-border);">${formatNum(approved)}</td>
            <td style="text-align: right; font-family: monospace; color: #dc2626; border-bottom: 2px solid var(--card-border);">${formatNum(rejected)}</td>
            
            <td style="text-align: center; border-bottom: 2px solid var(--card-border);">
                <span style="display: inline-block; padding: 0.25rem 0.5rem; border-radius: 0.5rem; font-size: 0.75rem; font-weight: 800; ${provPctClass}">
                    ${persentase}%
                </span>
            </td>
            <td style="text-align: center; border-bottom: 2px solid var(--card-border);">
                ${getProvDeltaHTML(provDeltaLusa)}
            </td>
            <td style="text-align: center; border-bottom: 2px solid var(--card-border);">
                ${getProvDeltaHTML(provDeltaKemarin)}
            </td>
            <td style="text-align: center; border-bottom: 2px solid var(--card-border);">
                ${getProvDeltaHTML(provDeltaHariIni)}
            </td>
            <td style="text-align: center; border-bottom: 2px solid var(--card-border);">
                ${provPenambahanBadge}
            </td>
        `;"""

# Use regex to replace the old provRow.innerHTML assignment and the lines immediately preceding it
pattern = re.compile(r'        const provTodayHTML = .*?        `;', re.DOTALL)
new_content = pattern.sub(replacement, content)

with open('app.js', 'w') as f:
    f.write(new_content)
