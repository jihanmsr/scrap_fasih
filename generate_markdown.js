const fs = require('fs');

const data = JSON.parse(fs.readFileSync('match_results.json', 'utf8'));
let md = `# Hasil Pencocokan Data Granular (PT IMIP Morowali)\n\n`;
md += `Dari 45 nama perusahaan yang diberikan, **${data.filter(d => d.matches.length > 0).length}** berhasil dicocokkan dengan data granular di sistem.\n\n`;

md += `| ID | Nama Target (Dari Chat) | Nama di Sistem | Status Survei (Granular) |\n`;
md += `|---|---|---|---|\n`;

data.forEach(item => {
    if (item.matches.length > 0) {
        // take first match
        const m = item.matches[0];
        md += `| ${item.id} | ${item.target_name} | ${m.company_name} | **${m.survey_status}** |\n`;
    } else {
        md += `| ${item.id} | ${item.target_name} | *- Tidak ditemukan -* | - |\n`;
    }
});

fs.writeFileSync('/Users/jihanmaisaroh/.gemini/antigravity-ide/brain/d2cfbc9a-3344-46fc-be7d-3f3b2b886d11/hasil_pencocokan.md', md);
