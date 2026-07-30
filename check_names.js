const fs = require('fs');

global.window = {};

eval(fs.readFileSync('petugas_region_map.js', 'utf8'));
eval(fs.readFileSync('fast_petugas_progress.js', 'utf8'));
eval(fs.readFileSync('users.js', 'utf8'));
eval(fs.readFileSync('mitra_data.js', 'utf8'));

let userMap = {};
if (window.USERS_DATA) {
    window.USERS_DATA.forEach(u => {
        if (u.email) userMap[u.email.toLowerCase()] = u.name;
        if (u.username) userMap[u.username.toLowerCase()] = u.name;
    });
}
let mitraMap = {};
if (window.MITRA_DATA) {
    window.MITRA_DATA.forEach(m => {
        if (m.email) {
            mitraMap[m.email.toLowerCase()] = m.nama;
        }
    });
}

let pencacah = window.PETUGAS_PROGRESS_MAP['Pencacah'];
let sigiCount = 0;
let sigiNames = [];

for (const [email, data] of Object.entries(pencacah)) {
    let regions = window.PETUGAS_REGION_MAP[email.toLowerCase()] || [];
    let isSigi = regions.some(rc => rc && rc.startsWith('7210'));
    if (isSigi) {
        sigiCount++;
        let displayName = email;
        if (mitraMap[email]) displayName = mitraMap[email];
        else if (userMap[email]) displayName = userMap[email];
        else if (userMap[email.split('@')[0]]) displayName = userMap[email.split('@')[0]];
        sigiNames.push(displayName);
    }
}

let uniqueSigiNames = new Set(sigiNames);
console.log(`Sigi Count: ${sigiCount}`);
console.log(`Unique Names: ${uniqueSigiNames.size}`);

if (uniqueSigiNames.size !== sigiNames.length) {
    let counts = {};
    sigiNames.forEach(n => counts[n] = (counts[n] || 0) + 1);
    for (let n in counts) {
        if (counts[n] > 1) console.log(n + " : " + counts[n]);
    }
}
