const fs = require('fs');
const path = require('path');
const zlib = require('zlib');

const files = [
  'granular_assignments_se_umum_7201.json',
  'granular_assignments_se_umum_7202.json',
  'granular_assignments_se_umum_7204.json',
  'granular_assignments_se_umum_7205.json',
  'granular_assignments_se_umum_7206.json',
  'granular_assignments_se_umum_7207.json',
  'granular_assignments_se_umum_7208.json',
  'granular_assignments_se_umum_7209.json',
  'granular_assignments_se_umum_7210.json',
  'granular_assignments_se_umum_7211.json',
  'granular_assignments_se_umum_7212.json',
  'granular_assignments_se_umum_7271.json'
];

const outputFile = path.join(__dirname, 'data_nama_kbu.csv');
const writeStream = fs.createWriteStream(outputFile);
writeStream.write('uuid,kode_identitas,kabkot\n');

let count = 0;
const SUMBER_UMUM = ['DTSEN', 'UMK', 'UMKM', 'NONBKU', 'DUMMY', 'KORPORASI'];

files.forEach(file => {
  try {
    const kabkot = file.match(/_(\d{4})\.json/)[1];
    const data = require('./old_partitions/' + file);
    if (!data.compressed_data) return;
    const buffer = Buffer.from(data.compressed_data, 'base64');
    const unzipped = JSON.parse(zlib.gunzipSync(buffer).toString('utf-8'));
    if (!unzipped.targets) return;
    
    unzipped.targets.forEach(t => {
      if (!t[0] || !t[1] || typeof t[1] !== 'string') return;
      const str = t[1];
      const parts = str.split(' - ').map(p => p.trim());
      
      // Jika middle part bukan SUMBER_UMUM, asumsikan itu adalah [nama k/b/u]
      let isNamaKbu = false;
      if (parts.length >= 3) {
        const middle = parts[1].toUpperCase();
        if (!SUMBER_UMUM.includes(middle)) {
          isNamaKbu = true;
        }
      } else {
        // Jika formatnya berantakan, mungkin juga itu nama kbu
        isNamaKbu = true;
      }
      
      if (isNamaKbu) {
        // Escape quotes
        const safeName = str.replace(/\"/g, '\"\"');
        writeStream.write(`${t[0]},"${safeName}",${kabkot}\n`);
        count++;
      }
    });
  } catch(e) {}
});

writeStream.end();
console.log('Selesai. Total baris nama K/B/U:', count);
