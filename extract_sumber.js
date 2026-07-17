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

const SUMBER = ['DTSEN', 'UMK', 'UMKM', 'NONBKU', 'DUMMY'];

const streams = {};
SUMBER.forEach(s => {
  streams[s] = fs.createWriteStream(path.join(__dirname, `data_${s.toLowerCase()}.csv`));
  streams[s].write('uuid,kode_identitas,kabkot\n');
});

const summary = {};

// init summary structure
files.forEach(f => {
  const kab = f.match(/_(\d{4})\.json/)[1];
  summary[kab] = { DTSEN: 0, UMK: 0, UMKM: 0, NONBKU: 0, DUMMY: 0 };
});

let totalCount = 0;
let seen = new Set(); // to avoid duplicates

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
      if (seen.has(t[0])) return;
      seen.add(t[0]);
      
      const str = t[1];
      const parts = str.split(' - ').map(p => p.trim());
      
      if (parts.length >= 3) {
        const middle = parts[1].toUpperCase();
        if (SUMBER.includes(middle)) {
          streams[middle].write(`${t[0]},"${str}",${kabkot}\n`);
          summary[kabkot][middle]++;
          totalCount++;
        }
      }
    });
  } catch(e) {}
});

// Close all streams
SUMBER.forEach(s => streams[s].end());

// Write summary
const summaryStream = fs.createWriteStream(path.join(__dirname, 'summary_sumber_per_kabkot.csv'));
summaryStream.write('kabkot,DTSEN,UMK,UMKM,NONBKU,DUMMY,Total\n');
for (const kab in summary) {
  const row = summary[kab];
  const sum = row.DTSEN + row.UMK + row.UMKM + row.NONBKU + row.DUMMY;
  summaryStream.write(`${kab},${row.DTSEN},${row.UMK},${row.UMKM},${row.NONBKU},${row.DUMMY},${sum}\n`);
}
summaryStream.end();

console.log('Ekstraksi selesai!');
console.log('Total data sumber:', totalCount);
console.log('File CSV terpisah untuk masing-masing sumber (DTSEN, UMK, dll) telah dibuat.');
