const fs = require('fs');

// Create dummy window object
global.window = {};

// Load data files
try {
    eval(fs.readFileSync('petugas_region_map.js', 'utf8'));
    eval(fs.readFileSync('fast_petugas_progress.js', 'utf8'));
    eval(fs.readFileSync('fast_petugas_history.js', 'utf8'));
    
    let pencacah = window.PETUGAS_PROGRESS_MAP['Pencacah'];
    let sigiCount = 0;
    let bangkepCount = 0;
    
    let sigiEmails = [];
    let bangkepEmails = [];
    
    for (const [email, data] of Object.entries(pencacah)) {
        let regions = window.PETUGAS_REGION_MAP[email.toLowerCase()] || [];
        
        // Check for Sigi (7210)
        let isSigi = regions.some(rc => rc && rc.startsWith('7210'));
        if (isSigi) {
            sigiCount++;
            sigiEmails.push(email);
        }
        
        // Check for Banggai Kepulauan (7201)
        let isBangkep = regions.some(rc => rc && rc.startsWith('7201'));
        if (isBangkep) {
            bangkepCount++;
            bangkepEmails.push(email);
        }
    }
    
    console.log(`Total Pencacah: ${Object.keys(pencacah).length}`);
    console.log(`Sigi Count: ${sigiCount}`);
    console.log(`Bangkep Count: ${bangkepCount}`);
    
    // Check for duplicates in names
    let sigiNames = sigiEmails.map(email => pencacah[email].name);
    let uniqueSigiNames = new Set(sigiNames);
    console.log(`Sigi unique names: ${uniqueSigiNames.size} out of ${sigiNames.length}`);
    
    if (uniqueSigiNames.size !== sigiNames.length) {
        console.log("Duplicate names in Sigi:");
        let counts = {};
        sigiNames.forEach(n => counts[n] = (counts[n] || 0) + 1);
        for (let n in counts) {
            if (counts[n] > 1) console.log(n + " : " + counts[n]);
        }
    }
} catch (e) {
    console.error(e);
}
