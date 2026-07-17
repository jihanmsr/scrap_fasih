const fs = require('fs');
const path = require('path');

const inputFile = path.join(__dirname, 'data_unik_dtsen_umk.csv');
const dtsenFile = path.join(__dirname, 'dtsen_counts.csv');
const umkFile = path.join(__dirname, 'umk_counts.csv');
const summaryFile = path.join(__dirname, 'summary_dtsen_umk_per_kabkot.csv');

// Initialize write streams
const dtsenStream = fs.createWriteStream(dtsenFile);
const umkStream = fs.createWriteStream(umkFile);
const summaryStream = fs.createWriteStream(summaryFile);

dtsenStream.write('uuid,kode_identitas,kabkot\n');
umkStream.write('uuid,kode_identitas,kabkot\n');
summaryStream.write('kabkot,dtsen_count,umk_count\n');

// Data structures for summary
const summary = {};

// Helper to increment count
function inc(kab, type) {
  if (!summary[kab]) summary[kab] = { dtsen: 0, umk: 0 };
  summary[kab][type]++;
}

// Read input CSV line by line
const rl = require('readline').createInterface({
  input: fs.createReadStream(inputFile),
  crlfDelay: Infinity
});

let isHeader = true;
rl.on('line', (line) => {
  if (isHeader) { isHeader = false; return; }
  const [uuid, kodeIdentitas, kabkot] = line.split(',');
  if (!uuid) return; // skip empty lines
  const lower = (kodeIdentitas || '').toLowerCase();
  const isDtsen = lower.includes('dtsen');
  const isUmk = lower.includes('umk');
  if (isDtsen) {
    dtsenStream.write(`${uuid},${kodeIdentitas},${kabkot}\n`);
    inc(kabkot, 'dtsen');
  }
  if (isUmk) {
    umkStream.write(`${uuid},${kodeIdentitas},${kabkot}\n`);
    inc(kabkot, 'umk');
  }
});

rl.on('close', () => {
  // write summary
  for (const kab in summary) {
    const { dtsen, umk } = summary[kab];
    summaryStream.write(`${kab},${dtsen},${umk}\n`);
  }
  dtsenStream.end();
  umkStream.end();
  summaryStream.end();
  console.log('Splitting done. Files created:');
  console.log(' - dtsen_counts.csv');
  console.log(' - umk_counts.csv');
  console.log(' - summary_dtsen_umk_per_kabkot.csv');
});
