const fs = require('fs');

const targetText = fs.readFileSync('target_companies.txt', 'utf8');
const targetLines = targetText.trim().split('\n').map(line => {
    const parts = line.split('\t');
    return {
        id: parts[0],
        name: parts[5] ? parts[5].trim() : ''
    };
}).filter(t => t.name);

// parse data.js
const vm = require('vm');
const sandbox = { window: {} };
vm.createContext(sandbox);

let dataData = [];
try {
    const dataStr = fs.readFileSync('data.js', 'utf8');
    vm.runInContext(dataStr, sandbox);
    dataData = sandbox.window.EMAIL_DATA;
} catch (e) {
    console.error("Failed to parse data.js", e);
}

function cleanForRegex(str) {
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

const results = [];
let matchedCount = 0;

targetLines.forEach(target => {
    const origName = target.name.toUpperCase();
    const cleanName = origName.replace(/PT\./g, 'PT').replace(/,?\s*(PT|CV|UD)/g, '').replace(/[^A-Z0-9]/g, ' ').replace(/\s+/g, ' ').trim();
    
    const matches = [];
    
    if (dataData && dataData.length) {
        dataData.forEach(d => {
            if (!d.company_name) return;
            const dNameOrig = d.company_name.toUpperCase();
            const dNameClean = dNameOrig.replace(/PT\./g, 'PT').replace(/,?\s*(PT|CV|UD)/g, '').replace(/[^A-Z0-9]/g, ' ').replace(/\s+/g, ' ').trim();
            
            if (dNameClean === cleanName || dNameClean.includes(cleanName) || cleanName.includes(dNameClean)) {
                if (cleanName.length > 5 && dNameClean.length > 5) { // avoid matching short generic words
                    matches.push({
                        company_name: d.company_name,
                        survey_status: d.survey_status,
                        status: d.status,
                        timestamp: d.timestamp
                    });
                }
            }
        });
    }

    if (matches.length > 0) {
        matchedCount++;
        results.push({
            id: target.id,
            target_name: target.name,
            matches: matches
        });
    } else {
        results.push({
            id: target.id,
            target_name: target.name,
            matches: []
        });
    }
});

fs.writeFileSync('match_results.json', JSON.stringify(results, null, 2));
console.log(`Found matches for ${matchedCount} out of ${targetLines.length} targets.`);
