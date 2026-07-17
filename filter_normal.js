const fs = require('fs');
const path = require('path');

const inputCsv = path.join(__dirname, 'data_unik_dtsen_umk.csv');
const outputCsv = path.join(__dirname, 'filtered_normal_dtsen_umk.csv');

const writeStream = fs.createWriteStream(outputCsv);
writeStream.write('uuid,kode_identitas,kabkot\n');

const rl = require('readline').createInterface({
  input: fs.createReadStream(inputCsv),
  crlfDelay: Infinity
});

let isHeader = true;
let kept = 0, total = 0;
rl.on('line', line => {
  if (isHeader) { isHeader = false; return; }
  total++;
  const [uuid, kodeIdentitas, kabkot] = line.split(',');
  if (!kodeIdentitas) return;
  // Split by ' - ' (space dash space)
  const parts = kodeIdentitas.split(' - ').map(p => p.trim());
  if (parts.length !== 3) {
    // malformed, skip
    return;
  }
  const middle = parts[1].toLowerCase();
  // keep only if middle part is exactly 'dtsen' or 'umk'
  if (middle === 'dtsen' || middle === 'umk') {
    writeStream.write(`${uuid},${kodeIdentitas},${kabkot}\n`);
    kept++;
  }
});

rl.on('close', () => {
  writeStream.end();
  console.log(`Filtering selesai. Total baris: ${total}, dipertahankan: ${kept}`);
});
