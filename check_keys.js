const fs = require('fs');
global.window = {};
eval(fs.readFileSync('fast_petugas_progress.js', 'utf8'));
let p = window.PETUGAS_PROGRESS_MAP['Pencacah'];
let firstKey = Object.keys(p)[0];
console.log("Keys in first item:", Object.keys(p[firstKey]));
console.log("First item:", p[firstKey]);
