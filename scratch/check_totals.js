const fs = require('fs');
const zlib = require('zlib');

const script_dir = '.';
const files = fs.readdirSync(script_dir).filter(f => f.startsWith('granular_assignments_se_umum_') && f.endsWith('.json'));

const allTids = new Map(); // tid -> count
let duplicatesCount = 0;
let totalLoaded = 0;

files.forEach(f => {
    const raw = JSON.parse(fs.readFileSync(f, 'utf8'));
    const comp = raw.compressed_data;
    if (comp) {
        const buffer = Buffer.from(comp, 'base64');
        const decompressed = zlib.gunzipSync(buffer);
        const parsed = JSON.parse(decompressed.toString('utf8'));
        
        parsed.targets.forEach(t => {
            const tid = t[0];
            totalLoaded++;
            if (allTids.has(tid)) {
                allTids.set(tid, allTids.get(tid) + 1);
                duplicatesCount++;
            } else {
                allTids.set(tid, 1);
            }
        });
    }
});

console.log(`Total loaded targets from all files: ${totalLoaded}`);
console.log(`Total unique target IDs: ${allTids.size}`);
console.log(`Total duplicated target occurrences: ${duplicatesCount}`);
