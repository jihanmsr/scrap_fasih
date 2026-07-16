const fs = require('fs');
const content = fs.readFileSync('ipas_data.js', 'utf-8');
const start = content.indexOf('{');
const end = content.lastIndexOf('}') + 1;
const data = JSON.parse(content.substring(start, end));
const surveyData = data['se_umum'];
let prelist = 0;

function scaleBreakdown(bd, total) {
    if(!bd) return {};
    let sum = 0; Object.values(bd).forEach(v => sum += v);
    if(sum === 0) return bd;
    let res = {};
    for (let k in bd) {
        res[k] = Math.round(bd[k] * total / sum);
    }
    return res;
}

try {
    surveyData.forEach(item => {
        if (item.today_completed_breakdown) delete item.today_completed_breakdown["Belum Terkategori"];
        item.today_completed = Math.max(item.today_completed || 0, 0);
        item.today_completed_breakdown = scaleBreakdown(item.today_completed_breakdown, item.today_completed);
        
        prelist += item.total_prelist || 0;
    });
    console.log("SUCCESS, prelist=", prelist);
} catch(e) {
    console.log("ERROR", e);
}
