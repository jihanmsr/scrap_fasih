const fs = require('fs');
const content = fs.readFileSync('ipas_data.js', 'utf-8');
const start = content.indexOf('{');
const end = content.lastIndexOf('}') + 1;
const data = JSON.parse(content.substring(start, end));

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

const scaleKecamatans = (kecamatanList, targetCount, timeKey, kabItem) => {
    if (!kecamatanList || kecamatanList.length === 0) return;
    const completedKey = `${timeKey}_completed`;
    const breakdownKey = `${completedKey}_breakdown`;
    let sumKec = 0;
    kecamatanList.forEach(k => { sumKec += (k[completedKey] || 0); });
    if (sumKec === 0) {
        if (targetCount > 0) {
            let totalPrelist = 0;
            kecamatanList.forEach(k => totalPrelist += (k.total_prelist || 0));
            if (totalPrelist > 0) {
                let currentSum = 0;
                kecamatanList.forEach(k => {
                    k[completedKey] = Math.round((k.total_prelist / totalPrelist) * targetCount);
                    currentSum += k[completedKey];
                });
                const diff = targetCount - currentSum;
                if (diff !== 0 && kecamatanList.length > 0) {
                    kecamatanList[0][completedKey] = Math.max(0, kecamatanList[0][completedKey] + diff);
                }
                kecamatanList.forEach(k => {
                    k[breakdownKey] = scaleBreakdown(kabItem[breakdownKey] || {}, k[completedKey]);
                });
            } else {
                kecamatanList.forEach(k => { k[completedKey] = 0; k[breakdownKey] = {}; });
            }
        } else {
            kecamatanList.forEach(k => { k[completedKey] = 0; k[breakdownKey] = {}; });
        }
        return;
    }
    if (sumKec === targetCount) return;
    const scale = targetCount / sumKec;
    let newSum = 0;
    kecamatanList.forEach(k => {
        k[completedKey] = Math.round((k[completedKey] || 0) * scale);
        newSum += k[completedKey];
    });
    const diff = targetCount - newSum;
    if (diff !== 0) {
        let maxKec = null;
        let maxVal = -1;
        kecamatanList.forEach(k => {
            if (k[completedKey] > maxVal) { maxVal = k[completedKey]; maxKec = k; }
        });
        if (maxKec) maxKec[completedKey] = Math.max(0, maxKec[completedKey] + diff);
    }
    kecamatanList.forEach(k => { k[breakdownKey] = scaleBreakdown(k[breakdownKey] || {}, k[completedKey]); });
};

try {
    data['se_umum'].forEach(item => {
        item.today_completed = Math.max(item.today_completed || 0, 0);
        item.yesterday_completed = Math.max(item.yesterday_completed || 0, 0);
        item.two_days_ago_completed = Math.max(item.two_days_ago_completed || 0, 0);
        
        scaleKecamatans(item.kecamatan_list, item.today_completed, 'today', item);
        scaleKecamatans(item.kecamatan_list, item.yesterday_completed, 'yesterday', item);
        scaleKecamatans(item.kecamatan_list, item.two_days_ago_completed, 'two_days_ago', item);
    });
    console.log("SUCCESS");
} catch(e) {
    console.log("ERROR", e);
}
