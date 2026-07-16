const fs = require('fs');
const content = fs.readFileSync('ipas_data.js', 'utf-8');
const start = content.indexOf('{');
const end = content.lastIndexOf('}') + 1;
const data = JSON.parse(content.substring(start, end));

let prelist = 0;
data['se_umum'].forEach(item => {
    prelist += item.total_prelist || 0;
});
console.log("SE_UMUM PRELIST:", prelist);

let prelist_ub = 0;
data['se_ub'].forEach(item => {
    prelist_ub += item.total_prelist || 0;
});
console.log("SE_UB PRELIST:", prelist_ub);
