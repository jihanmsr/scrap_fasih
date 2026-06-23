const fs = require('fs');
const zlib = require('zlib');

// Load granular_assignments.json
const raw = JSON.parse(fs.readFileSync('granular_assignments.json', 'utf8'));
const comp = raw.compressed_data;
const decompressed = zlib.gunzipSync(Buffer.from(comp, 'base64'));
const data = JSON.parse(decompressed.toString('utf8'));

console.log("Total targets:", data.targets.length);

const unassignedSubmitted = [];
data.targets.forEach(t => {
    // t = [tid, code_id, name, stat_idx, pet_idx, reg_idx, epoch_mod, survey_flag]
    const status = data.statuses[t[3]] || '';
    const pet_idx = t[4];
    const pet = pet_idx >= 0 ? data.petugas[pet_idx] : null;
    const pet_username = pet ? pet[0] : '-';
    
    const is_unassigned = (!pet_username || pet_username === '-');
    const is_submitted = (status !== 'OPEN' && status !== 'DRAFT');
    
    if (is_unassigned && is_submitted) {
        unassignedSubmitted.push({
            id: t[0],
            code_id: t[1],
            name: t[2],
            status: status,
            pet_idx: pet_idx
        });
    }
});

console.log("Found", unassignedSubmitted.length, "unassigned but submitted targets:");
console.log(unassignedSubmitted.slice(0, 10));
