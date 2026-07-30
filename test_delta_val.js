const fs = require('fs');
let content = fs.readFileSync('ipas_data.js', 'utf8');
content = content.replace('window.IPAS_DATA = ', '').trim();
if (content.endsWith(';')) content = content.slice(0, -1);
const data = JSON.parse(content);
const kecs = data.se_umum[0].kecamatan_list;
console.log('Kecamatans in Bangkep:');
kecs.forEach(k => {
    console.log(`${k.kec_name}: delta=${k.delta_persen}, delta_h1=${k.delta_kemarin_persen}`);
});
