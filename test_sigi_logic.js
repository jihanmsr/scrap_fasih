const fs = require('fs');

// Load data
eval(fs.readFileSync('petugas_region_map.js', 'utf8').replace('window.PETUGAS_REGION_MAP', 'global.PETUGAS_REGION_MAP'));
eval(fs.readFileSync('fast_petugas_progress.js', 'utf8').replace('window.PETUGAS_PROGRESS_MAP', 'global.PETUGAS_PROGRESS_MAP'));

const kabFilterDashboard = '[10] SIGI';
const kecFilterDashboard = 'all';

let resolvedKabPrefix = '';
const kabPrefixMatch = kabFilterDashboard.match(/\[(\d+)\]/);
if (kabPrefixMatch) resolvedKabPrefix = kabPrefixMatch[1];

let resolvedKecPrefix = '';

let arr = [];
['Pencacah', 'Pengawas'].forEach(roleKey => {
    const roleData = global.PETUGAS_PROGRESS_MAP[roleKey];
    for (const [email, pMapData] of Object.entries(roleData)) {
        let isPetugasInWilayah = false;
        if ((kabFilterDashboard !== 'all' || kecFilterDashboard !== 'all') && global.PETUGAS_REGION_MAP) {
            const regions = global.PETUGAS_REGION_MAP[email.toLowerCase()];
            if (regions && regions.length > 0) {
                isPetugasInWilayah = regions.some(rc => {
                    if (!rc) return false;
                    let match = true;
                    if (resolvedKabPrefix) match = match && rc.startsWith('72' + resolvedKabPrefix);
                    if (resolvedKabPrefix && resolvedKecPrefix) match = match && rc.startsWith('72' + resolvedKabPrefix + resolvedKecPrefix);
                    return match;
                });
            }
        } else {
            isPetugasInWilayah = true;
        }
        
        if (!isPetugasInWilayah) {
            continue;
        }

        const pTotal = Math.max(pMapData.target || 0, 0); // simplified
        
        arr.push({
            email: email,
            role: roleKey,
            total: pTotal
        });
    }
});

let currentPetugasTab = 'Pencacah';
arr = arr.filter(p => (!p.role || p.role === currentPetugasTab));

console.log("Filtered arr length:", arr.length);
if (arr.length > 0) console.log("Sample:", arr[0]);

